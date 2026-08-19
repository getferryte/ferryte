"""Adapter for Chroma (``chromadb``).

Chroma is friendlier than raw pgvector in one important way: it owns its own
embedding function, so ``probe()`` can run true semantic retrieval without
Ferryte needing to know your model. That means the semantic-neighbour leak path
— the one the research says actually bites, where tenant B's query surfaces
tenant A's document because they are *similar*, not because a filter was
missing — is genuinely testable here.

Tenant scoping uses Chroma's metadata ``where`` filter. That is exactly the
mechanism most multi-tenant deployments rely on, which makes it exactly the
mechanism worth auditing: a ``where`` clause the application forgets to pass is
invisible from inside the application.

The adapter wraps a **Collection**, not the client, because the collection is
where ``add`` / ``query`` / ``delete`` live.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from ..context import current_context
from ..lineage import get_lineage
from .base import AdapterCapability, BackendKind, RetrievalRecord, WriteRecord


@dataclass
class ChromaStore:
    """Thin handle over a ``chromadb`` Collection.

    ``collection`` is the object returned by
    ``client.get_or_create_collection(name)``.
    """

    collection: Any
    tenant_key: str = "tenant_id"
    source_key: str = "source_id"

    _ferryte_patched: bool = False

    # ------------------------------------------------------------------ setup

    @classmethod
    def connect(
        cls,
        *,
        collection: str,
        path: str | None = None,
        host: str | None = None,
        port: int = 8000,
        tenant_key: str = "tenant_id",
        source_key: str = "source_id",
        embedding_function: Any | None = None,
    ) -> ChromaStore:
        """Open a Chroma collection, local-persistent or HTTP.

        ``embedding_function`` matters more than it looks. Chroma's default
        embedder downloads an ONNX model on first use, which fails closed in
        air-gapped environments, locked-down CI, and any network that proxies
        egress — exactly the environments a security-conscious buyer runs in.
        Production deployments also usually pin their own embedder so that
        Ferryte's queries embed the same way the application's do. Pass yours;
        Ferryte will not silently substitute a different one.
        """
        try:
            import chromadb  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise ImportError(
                "Chroma support needs the chromadb package. Install it:\n"
                "    pip install 'ferryte[chroma]'\n"
                "or\n"
                "    pip install chromadb"
            ) from exc

        if host:
            client = chromadb.HttpClient(host=host, port=port)
        elif path:
            client = chromadb.PersistentClient(path=path)
        else:
            client = chromadb.EphemeralClient()
        kwargs: dict[str, Any] = {"name": collection}
        if embedding_function is not None:
            kwargs["embedding_function"] = embedding_function
        coll = client.get_or_create_collection(**kwargs)
        return cls(collection=coll, tenant_key=tenant_key, source_key=source_key)

    # ------------------------------------------------------------------ writes

    def add(
        self,
        *,
        content: str,
        source_id: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        artifact_id = str(uuid.uuid4())
        meta: dict[str, Any] = dict(metadata or {})
        if tenant_id is not None:
            meta[self.tenant_key] = tenant_id
        if source_id is not None:
            meta[self.source_key] = source_id
        # Chroma rejects empty metadata dicts on some versions; send None instead.
        self.collection.add(
            ids=[artifact_id],
            documents=[content],
            metadatas=[meta] if meta else None,
        )
        return artifact_id

    # --------------------------------------------------------------- retrieval

    def search(
        self,
        *,
        query: str,
        tenant_id: str | None = None,
        limit: int = 5,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        _ = include_deleted  # Chroma deletes are hard deletes
        kwargs: dict[str, Any] = {"query_texts": [query], "n_results": limit}
        if tenant_id is not None:
            kwargs["where"] = {self.tenant_key: tenant_id}
        raw = self.collection.query(**kwargs)
        return _flatten_query(raw, tenant_key=self.tenant_key, source_key=self.source_key)

    def search_unfiltered(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Query with **no** tenant filter.

        This is the adversarial view: what the store would return if the
        application ever forgot its ``where`` clause. Comparing this against the
        filtered result is how a filter-bypass leak becomes visible.
        """
        raw = self.collection.query(query_texts=[query], n_results=limit)
        return _flatten_query(raw, tenant_key=self.tenant_key, source_key=self.source_key)

    def raw_rows_containing(self, needle: str, *, limit: int = 200) -> list[dict[str, Any]]:
        """Scan stored documents directly, bypassing ranking entirely."""
        try:
            raw = self.collection.get(limit=limit, include=["documents", "metadatas"])
        except TypeError:  # older chromadb signature
            raw = self.collection.get(include=["documents", "metadatas"])
        ids = raw.get("ids") or []
        docs = raw.get("documents") or []
        metas = raw.get("metadatas") or []
        out: list[dict[str, Any]] = []
        for i, doc in enumerate(docs):
            if doc and needle.lower() in str(doc).lower():
                meta = metas[i] if i < len(metas) and metas[i] else {}
                out.append(
                    {
                        "id": ids[i] if i < len(ids) else "",
                        "content": doc,
                        "tenant_id": meta.get(self.tenant_key),
                        "source_id": meta.get(self.source_key),
                    }
                )
        return out

    # ----------------------------------------------------------------- deletes

    def delete_by_source(self, source_id: str) -> int:
        before = self.count_for_source(source_id)
        self.collection.delete(where={self.source_key: source_id})
        after = self.count_for_source(source_id)
        return max(before - after, 0)

    def count_for_source(self, source_id: str) -> int:
        try:
            raw = self.collection.get(where={self.source_key: source_id}, include=[])
        except Exception:  # noqa: BLE001 - older versions reject include=[]
            raw = self.collection.get(where={self.source_key: source_id})
        return len(raw.get("ids") or [])

    def documents_for_tenant(self, tenant_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        """Enumerate one tenant's documents — powers the semantic-neighbour probe."""
        try:
            raw = self.collection.get(
                where={self.tenant_key: tenant_id},
                limit=limit,
                include=["documents", "metadatas"],
            )
        except TypeError:
            raw = self.collection.get(
                where={self.tenant_key: tenant_id}, include=["documents", "metadatas"]
            )
        ids = raw.get("ids") or []
        docs = raw.get("documents") or []
        metas = raw.get("metadatas") or []
        out: list[dict[str, Any]] = []
        for i, aid in enumerate(ids[:limit]):
            meta = metas[i] if i < len(metas) and metas[i] else {}
            out.append(
                {
                    "id": aid,
                    "content": docs[i] if i < len(docs) else "",
                    "tenant_id": meta.get(self.tenant_key, tenant_id),
                    "source_id": meta.get(self.source_key),
                }
            )
        return out

    def tenants(self, *, limit: int = 1000) -> list[str]:
        try:
            raw = self.collection.get(limit=limit, include=["metadatas"])
        except TypeError:
            raw = self.collection.get(include=["metadatas"])
        seen: list[str] = []
        for meta in raw.get("metadatas") or []:
            if not meta:
                continue
            val = meta.get(self.tenant_key)
            if val is not None and str(val) not in seen:
                seen.append(str(val))
        return seen


class ChromaAdapter:
    """Five-hook adapter over :class:`ChromaStore`."""

    name: str = "chroma"
    backend: BackendKind = BackendKind.VECTOR
    capabilities: frozenset[AdapterCapability] = frozenset(
        {
            AdapterCapability.WRITE_CAPTURE,
            AdapterCapability.READ_CAPTURE,
            AdapterCapability.SOURCE_DELETE,
            AdapterCapability.TENANT_SCOPING,
            AdapterCapability.DERIVED_ENUMERATION,
        }
    )

    def patch(self, client: ChromaStore) -> ChromaStore:
        if getattr(client, "_ferryte_patched", False):
            return client
        lineage = get_lineage()
        original_add = client.add
        original_search = client.search
        original_delete = client.delete_by_source

        def add(
            *,
            content: str,
            source_id: str | None = None,
            tenant_id: str | None = None,
            metadata: dict[str, Any] | None = None,
        ) -> str:
            ctx = current_context()
            sid = source_id or ctx.source_id
            tid = tenant_id or ctx.tenant_id
            artifact_id = original_add(
                content=content, source_id=sid, tenant_id=tid, metadata=metadata
            )
            lineage.record_write(
                WriteRecord(
                    backend=BackendKind.VECTOR,
                    artifact_id=artifact_id,
                    content=content,
                    source_id=sid,
                    tenant_id=tid,
                    kind="raw",
                    metadata=dict(metadata or {}),
                )
            )
            return artifact_id

        def search(
            *,
            query: str,
            tenant_id: str | None = None,
            limit: int = 5,
            include_deleted: bool = False,
        ) -> list[dict[str, Any]]:
            ctx = current_context()
            tid = tenant_id or ctx.tenant_id
            rows = original_search(
                query=query, tenant_id=tid, limit=limit, include_deleted=include_deleted
            )
            for row in rows:
                lineage.record_retrieval(
                    RetrievalRecord(
                        backend=BackendKind.VECTOR,
                        query=query,
                        artifact_id=str(row.get("id", "")),
                        content=str(row.get("content", "")),
                        score=row.get("score"),
                        tenant_id=row.get("tenant_id") or tid,
                        metadata={"backend": "chroma"},
                    )
                )
            return rows

        def delete_by_source(source_id: str) -> int:
            n = original_delete(source_id)
            lineage.mark_source_revoked(source_id)
            remaining = client.count_for_source(source_id)
            if remaining > 0:
                lineage.record_blindspot(
                    backend=BackendKind.VECTOR.value,
                    kind="incomplete_delete",
                    detail=(
                        f"Chroma delete for source {source_id} removed {n} documents but "
                        f"{remaining} still match the source filter."
                    ),
                )
            return n

        client.add = add  # type: ignore[assignment]
        client.search = search  # type: ignore[assignment]
        client.delete_by_source = delete_by_source  # type: ignore[assignment]
        client._ferryte_patched = True
        client._ferryte_originals = {  # type: ignore[attr-defined]
            "add": original_add,
            "search": original_search,
            "delete_by_source": original_delete,
        }
        return client

    def unpatch(self, client: ChromaStore) -> None:
        if not getattr(client, "_ferryte_patched", False):
            return
        originals = client._ferryte_originals  # type: ignore[attr-defined]
        client.add = originals["add"]  # type: ignore[assignment]
        client.search = originals["search"]  # type: ignore[assignment]
        client.delete_by_source = originals["delete_by_source"]  # type: ignore[assignment]
        client._ferryte_patched = False

    def delete_source(
        self, client: ChromaStore, *, source_id: str, tenant_id: str | None = None
    ) -> int:
        _ = tenant_id
        return client.delete_by_source(source_id)

    def list_artifacts_for_source(
        self,
        client: ChromaStore,
        *,
        source_id: str,
        tenant_id: str | None = None,
    ) -> Iterable[WriteRecord]:
        raw = client.collection.get(
            where={client.source_key: source_id}, include=["documents", "metadatas"]
        )
        ids = raw.get("ids") or []
        docs = raw.get("documents") or []
        metas = raw.get("metadatas") or []
        out: list[WriteRecord] = []
        for i, aid in enumerate(ids):
            meta = metas[i] if i < len(metas) and metas[i] else {}
            out.append(
                WriteRecord(
                    backend=BackendKind.VECTOR,
                    artifact_id=str(aid),
                    content=str(docs[i]) if i < len(docs) else "",
                    source_id=source_id,
                    tenant_id=meta.get(client.tenant_key, tenant_id),
                    kind="raw",
                    metadata=dict(meta),
                )
            )
        return out

    def probe(
        self,
        client: ChromaStore,
        *,
        query: str,
        tenant_id: str | None = None,
        limit: int = 5,
    ) -> list[RetrievalRecord]:
        rows = client.search(query=query, tenant_id=tenant_id, limit=limit)
        return [
            RetrievalRecord(
                backend=BackendKind.VECTOR,
                query=query,
                artifact_id=str(r.get("id", "")),
                content=str(r.get("content", "")),
                score=r.get("score"),
                tenant_id=r.get("tenant_id") or tenant_id,
                metadata={"backend": "chroma"},
            )
            for r in rows
        ]


def _flatten_query(raw: Any, *, tenant_key: str, source_key: str) -> list[dict[str, Any]]:
    """Chroma returns parallel lists-of-lists (one inner list per query)."""
    if not isinstance(raw, dict):
        return []
    ids = (raw.get("ids") or [[]])[0]
    docs = (raw.get("documents") or [[]])[0]
    metas = (raw.get("metadatas") or [[]])[0]
    dists = (raw.get("distances") or [[]])[0]
    out: list[dict[str, Any]] = []
    for i, aid in enumerate(ids):
        meta = metas[i] if i < len(metas) and metas[i] else {}
        rec: dict[str, Any] = {
            "id": aid,
            "content": docs[i] if i < len(docs) else "",
            "tenant_id": meta.get(tenant_key),
            "source_id": meta.get(source_key),
            "metadata": dict(meta),
        }
        if i < len(dists) and dists[i] is not None:
            rec["score"] = 1.0 - float(dists[i])
        out.append(rec)
    return out
