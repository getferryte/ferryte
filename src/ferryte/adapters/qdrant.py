"""Adapter for Qdrant (``qdrant-client``).

Qdrant sits between pgvector and Chroma in how much it does for you: it owns
storage and filtering, but — unlike Chroma — it does **not** embed text for you
by default. So this adapter takes the same honest position as pgvector: supply
an ``embedder`` for true vector retrieval, or accept a scroll-based lexical
fallback and a recorded blind spot.

Qdrant's payload filters are the tenant-isolation mechanism here, and Qdrant's
own docs recommend exactly that pattern for multi-tenancy — which is precisely
why it is worth auditing. A payload filter is only as good as the application
remembering to send it.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from ..context import current_context
from ..lineage import get_lineage
from .base import AdapterCapability, BackendKind, RetrievalRecord, WriteRecord

Embedder = Callable[[str], Sequence[float]]


@dataclass
class QdrantStore:
    """Thin handle over a Qdrant collection."""

    client: Any
    collection: str
    embedder: Embedder | None = None
    tenant_key: str = "tenant_id"
    source_key: str = "source_id"
    content_key: str = "content"

    _ferryte_patched: bool = False

    @classmethod
    def connect(
        cls,
        *,
        collection: str,
        url: str | None = None,
        host: str | None = None,
        port: int = 6333,
        api_key: str | None = None,
        embedder: Embedder | None = None,
        **kwargs: Any,
    ) -> QdrantStore:
        try:
            from qdrant_client import QdrantClient  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise ImportError(
                "Qdrant support needs the qdrant-client package. Install it:\n"
                "    pip install 'ferryte[qdrant]'\n"
                "or\n"
                "    pip install qdrant-client"
            ) from exc
        if url:
            client = QdrantClient(url=url, api_key=api_key, **kwargs)
        else:
            client = QdrantClient(host=host or "localhost", port=port, api_key=api_key, **kwargs)
        return cls(client=client, collection=collection, embedder=embedder)

    # ------------------------------------------------------------------ writes

    def add(
        self,
        *,
        content: str,
        source_id: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if self.embedder is None:
            raise ValueError(
                "QdrantStore.add needs an embedder — Qdrant does not embed text for you. "
                "Pass embedder=... when constructing the store."
            )
        from qdrant_client.models import PointStruct  # type: ignore

        artifact_id = str(uuid.uuid4())
        payload: dict[str, Any] = dict(metadata or {})
        payload[self.content_key] = content
        if tenant_id is not None:
            payload[self.tenant_key] = tenant_id
        if source_id is not None:
            payload[self.source_key] = source_id
        self.client.upsert(
            collection_name=self.collection,
            points=[
                PointStruct(
                    id=artifact_id,
                    vector=list(self.embedder(content)),
                    payload=payload,
                )
            ],
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
        _ = include_deleted
        if self.embedder is None:
            get_lineage().record_blindspot(
                backend=BackendKind.VECTOR.value,
                kind="lexical_fallback",
                detail=(
                    "Qdrant probe ran without an embedder, so retrieval used a payload "
                    "scroll + substring scan instead of vector search. Exact-token "
                    "(canary) leaks are still detected; paraphrased or semantic-neighbour "
                    "leaks may be missed."
                ),
            )
            return self._scroll_contains(query, tenant_id=tenant_id, limit=limit)

        hits = self._vector_query(
            vector=list(self.embedder(query)),
            query_filter=self._tenant_filter(tenant_id),
            limit=limit,
        )
        return [self._hit_to_dict(h) for h in hits]

    def search_unfiltered(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Vector search with no tenant filter — the adversarial view."""
        if self.embedder is None:
            return self._scroll_contains(query, tenant_id=None, limit=limit)
        hits = self._vector_query(
            vector=list(self.embedder(query)), query_filter=None, limit=limit
        )
        return [self._hit_to_dict(h) for h in hits]

    def _vector_query(
        self, *, vector: list[float], query_filter: Any, limit: int
    ) -> list[Any]:
        """Run a similarity query across qdrant-client API generations.

        qdrant-client 1.12+ replaced ``search()`` with ``query_points()`` and
        wraps results in a ``QueryResponse``. Older versions only have
        ``search()``. Supporting both matters here: a buyer will not upgrade
        their client library to run an audit, and an adapter that only works on
        the newest SDK is an adapter that fails on first contact.
        """
        query_points = getattr(self.client, "query_points", None)
        if callable(query_points):
            resp = query_points(
                collection_name=self.collection,
                query=vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )
            return list(getattr(resp, "points", resp) or [])
        legacy = getattr(self.client, "search", None)
        if callable(legacy):
            return list(
                legacy(
                    collection_name=self.collection,
                    query_vector=vector,
                    query_filter=query_filter,
                    limit=limit,
                    with_payload=True,
                )
                or []
            )
        raise AttributeError(
            "This qdrant-client exposes neither query_points() nor search(). "
            "Ferryte cannot run vector retrieval against it."
        )

    def raw_rows_containing(self, needle: str, *, limit: int = 200) -> list[dict[str, Any]]:
        return self._scroll_contains(needle, tenant_id=None, limit=limit)

    # ----------------------------------------------------------------- deletes

    def delete_by_source(self, source_id: str) -> int:
        from qdrant_client.models import (  # type: ignore
            FieldCondition,
            Filter,
            FilterSelector,
            MatchValue,
        )

        before = self.count_for_source(source_id)
        self.client.delete(
            collection_name=self.collection,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key=self.source_key, match=MatchValue(value=source_id)
                        )
                    ]
                )
            ),
        )
        after = self.count_for_source(source_id)
        return max(before - after, 0)

    def count_for_source(self, source_id: str) -> int:
        from qdrant_client.models import FieldCondition, Filter, MatchValue  # type: ignore

        flt = Filter(
            must=[FieldCondition(key=self.source_key, match=MatchValue(value=source_id))]
        )
        res = self.client.count(
            collection_name=self.collection, count_filter=flt, exact=True
        )
        return int(getattr(res, "count", 0))

    def documents_for_tenant(self, tenant_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        """Enumerate one tenant's points — powers the semantic-neighbour probe."""
        points, _ = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=self._tenant_filter(tenant_id),
            limit=limit,
            with_payload=True,
        )
        out: list[dict[str, Any]] = []
        for p in points:
            payload = getattr(p, "payload", None) or {}
            out.append(
                {
                    "id": str(getattr(p, "id", "")),
                    "content": str(payload.get(self.content_key, "")),
                    "tenant_id": payload.get(self.tenant_key, tenant_id),
                    "source_id": payload.get(self.source_key),
                }
            )
        return out

    def tenants(self, *, limit: int = 1000) -> list[str]:
        points, _ = self.client.scroll(
            collection_name=self.collection, limit=limit, with_payload=True
        )
        seen: list[str] = []
        for p in points:
            payload = getattr(p, "payload", None) or {}
            val = payload.get(self.tenant_key)
            if val is not None and str(val) not in seen:
                seen.append(str(val))
        return seen

    # ---------------------------------------------------------------- internal

    def _tenant_filter(self, tenant_id: str | None) -> Any:
        if tenant_id is None:
            return None
        from qdrant_client.models import FieldCondition, Filter, MatchValue  # type: ignore

        return Filter(
            must=[FieldCondition(key=self.tenant_key, match=MatchValue(value=tenant_id))]
        )

    def _scroll_contains(
        self, needle: str, *, tenant_id: str | None, limit: int
    ) -> list[dict[str, Any]]:
        points, _ = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=self._tenant_filter(tenant_id),
            limit=max(limit * 20, 200),
            with_payload=True,
        )
        out: list[dict[str, Any]] = []
        for p in points:
            payload = getattr(p, "payload", None) or {}
            content = str(payload.get(self.content_key, ""))
            if needle.lower() in content.lower():
                out.append(
                    {
                        "id": str(getattr(p, "id", "")),
                        "content": content,
                        "tenant_id": payload.get(self.tenant_key),
                        "source_id": payload.get(self.source_key),
                        "metadata": dict(payload),
                    }
                )
            if len(out) >= limit:
                break
        return out

    def _hit_to_dict(self, hit: Any) -> dict[str, Any]:
        payload = getattr(hit, "payload", None) or {}
        return {
            "id": str(getattr(hit, "id", "")),
            "content": str(payload.get(self.content_key, "")),
            "tenant_id": payload.get(self.tenant_key),
            "source_id": payload.get(self.source_key),
            "score": getattr(hit, "score", None),
            "metadata": dict(payload),
        }


class QdrantAdapter:
    """Five-hook adapter over :class:`QdrantStore`."""

    name: str = "qdrant"
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

    def patch(self, client: QdrantStore) -> QdrantStore:
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
                        metadata={"backend": "qdrant"},
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
                        f"Qdrant delete for source {source_id} removed {n} points but "
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

    def unpatch(self, client: QdrantStore) -> None:
        if not getattr(client, "_ferryte_patched", False):
            return
        originals = client._ferryte_originals  # type: ignore[attr-defined]
        client.add = originals["add"]  # type: ignore[assignment]
        client.search = originals["search"]  # type: ignore[assignment]
        client.delete_by_source = originals["delete_by_source"]  # type: ignore[assignment]
        client._ferryte_patched = False

    def delete_source(
        self, client: QdrantStore, *, source_id: str, tenant_id: str | None = None
    ) -> int:
        _ = tenant_id
        return client.delete_by_source(source_id)

    def list_artifacts_for_source(
        self,
        client: QdrantStore,
        *,
        source_id: str,
        tenant_id: str | None = None,
    ) -> Iterable[WriteRecord]:
        from qdrant_client.models import FieldCondition, Filter, MatchValue  # type: ignore

        flt = Filter(
            must=[FieldCondition(key=client.source_key, match=MatchValue(value=source_id))]
        )
        points, _ = client.client.scroll(
            collection_name=client.collection,
            scroll_filter=flt,
            limit=1000,
            with_payload=True,
        )
        out: list[WriteRecord] = []
        for p in points:
            payload = getattr(p, "payload", None) or {}
            out.append(
                WriteRecord(
                    backend=BackendKind.VECTOR,
                    artifact_id=str(getattr(p, "id", "")),
                    content=str(payload.get(client.content_key, "")),
                    source_id=source_id,
                    tenant_id=payload.get(client.tenant_key, tenant_id),
                    kind="raw",
                    metadata=dict(payload),
                )
            )
        return out

    def probe(
        self,
        client: QdrantStore,
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
                metadata={"backend": "qdrant"},
            )
            for r in rows
        ]
