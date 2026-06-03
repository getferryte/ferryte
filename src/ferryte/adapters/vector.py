"""Generic in-memory vector-store adapter.

This adapter ships its own minimal vector store (``InMemoryVectorStore``) so
Ferryte has a fully self-contained backend for tests, the demo, and the docs.
Real vector DBs (pgvector, Chroma, Qdrant, ...) can be wrapped by subclassing
``VectorAdapter`` and overriding the four hooks.

The store deliberately mimics a real one in one critical way: it caches written
embeddings AND it keeps a "post-deletion staleness" buffer that simulates how
real systems (e.g. Mem0 over a vector index, or AgentCore's derived long-term
memory) can keep surfacing data after the primary record is deleted. This is
not a bug — it is exactly the failure Ferryte exists to detect.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from ..context import current_context
from ..lineage import get_lineage
from .base import AdapterCapability, BackendKind, RetrievalRecord, WriteRecord

_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _WORD_RE.findall(text or "")]


def _embed(text: str, dim: int = 64) -> list[float]:
    """Deterministic toy embedding: hash-bucketed bag-of-tokens.

    Real vector DBs use neural embeddings; we use a deterministic stand-in so
    tests are reproducible and the OSS install has no model dependencies.
    """
    vec = [0.0] * dim
    for tok in _tokenize(text):
        h = int(hashlib.sha1(tok.encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


@dataclass
class _StoredItem:
    artifact_id: str
    content: str
    embedding: list[float]
    tenant_id: str | None
    metadata: dict[str, Any] = field(default_factory=dict)
    deleted: bool = False


class InMemoryVectorStore:
    """A deliberately leaky vector store.

    ``delete_by_source`` removes the primary records but a derived "summary"
    artifact (which absorbed multiple sources) may live on — this reproduces
    the exact failure both AWS AgentCore and Zep document.
    """

    def __init__(self, *, leak_summaries: bool = True, dim: int = 64) -> None:
        self._items: dict[str, _StoredItem] = {}
        self._source_index: dict[str, set[str]] = {}
        self._tenant_summary: dict[tuple[str, str], _StoredItem] = {}
        self._leak_summaries = leak_summaries
        self._dim = dim

    # --- writes ---------------------------------------------------------------

    def add(
        self,
        *,
        content: str,
        source_id: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        artifact_id = str(uuid.uuid4())
        item = _StoredItem(
            artifact_id=artifact_id,
            content=content,
            embedding=_embed(content, self._dim),
            tenant_id=tenant_id,
            metadata=dict(metadata or {}),
        )
        self._items[artifact_id] = item
        if source_id:
            self._source_index.setdefault(source_id, set()).add(artifact_id)
        if tenant_id:
            self._update_tenant_summary(tenant_id, content, source_id)
        return artifact_id

    def _update_tenant_summary(
        self, tenant_id: str, content: str, source_id: str | None
    ) -> None:
        key = (tenant_id, "summary")
        existing = self._tenant_summary.get(key)
        if existing is None:
            artifact_id = str(uuid.uuid4())
            summary = _StoredItem(
                artifact_id=artifact_id,
                content=f"[summary:{tenant_id}] {content}",
                embedding=_embed(content, self._dim),
                tenant_id=tenant_id,
                metadata={"kind": "summary", "absorbed_sources": [source_id] if source_id else []},
            )
            self._tenant_summary[key] = summary
            self._items[artifact_id] = summary
        else:
            absorbed = list(existing.metadata.get("absorbed_sources", []))
            if source_id and source_id not in absorbed:
                absorbed.append(source_id)
            existing.metadata["absorbed_sources"] = absorbed
            existing.content = f"{existing.content} | {content}"
            existing.embedding = _embed(existing.content, self._dim)

    # --- deletes --------------------------------------------------------------

    def delete_by_source(self, source_id: str) -> int:
        ids = list(self._source_index.get(source_id, set()))
        n = 0
        for artifact_id in ids:
            item = self._items.get(artifact_id)
            if item is not None and not item.deleted:
                item.deleted = True
                n += 1
        if not self._leak_summaries:
            for _key, summary in list(self._tenant_summary.items()):
                absorbed = summary.metadata.get("absorbed_sources", [])
                if source_id in absorbed:
                    summary.deleted = True
        self._source_index.pop(source_id, None)
        return n

    # --- retrieval ------------------------------------------------------------

    def search(
        self,
        *,
        query: str,
        tenant_id: str | None = None,
        limit: int = 5,
        include_deleted: bool = False,
    ) -> list[tuple[_StoredItem, float]]:
        q = _embed(query, self._dim)
        scored: list[tuple[_StoredItem, float]] = []
        for item in self._items.values():
            if item.deleted and not include_deleted:
                continue
            if tenant_id is not None and item.tenant_id not in (None, tenant_id):
                continue
            scored.append((item, _cosine(q, item.embedding)))
        scored.sort(key=lambda kv: kv[1], reverse=True)
        return scored[:limit]

    # --- introspection (used by oracle to look past the agent's mouth) -------

    def raw_items(self) -> Iterable[_StoredItem]:
        return self._items.values()

    def raw_items_containing(self, needle: str) -> list[_StoredItem]:
        return [it for it in self._items.values() if needle.lower() in it.content.lower()]


class VectorAdapter:
    """Adapter that wraps ``InMemoryVectorStore`` (or any subclass mirror)."""

    name: str = "vector"
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

    def patch(self, client: InMemoryVectorStore) -> InMemoryVectorStore:
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
            pre_summary = None
            tid_key = (tid, "summary") if tid else None
            if tid_key is not None:
                pre_summary = client._tenant_summary.get(tid_key)
            artifact_id = original_add(
                content=content, source_id=sid, tenant_id=tid, metadata=metadata
            )
            lineage.record_write(
                WriteRecord(
                    backend=self.backend,
                    artifact_id=artifact_id,
                    content=content,
                    source_id=sid,
                    tenant_id=tid,
                    kind="raw",
                    metadata=dict(metadata or {}),
                )
            )
            if tid_key is not None:
                summary = client._tenant_summary.get(tid_key)
                if summary is not None:
                    lineage.record_write(
                        WriteRecord(
                            backend=self.backend,
                            artifact_id=summary.artifact_id,
                            content=summary.content,
                            source_id=sid,
                            tenant_id=tid,
                            kind="summary",
                            metadata=dict(summary.metadata),
                        )
                    )
                    if pre_summary is not None and pre_summary is summary:
                        for prior_source in summary.metadata.get("absorbed_sources", []):
                            if prior_source and prior_source != sid:
                                lineage.record_derivation(
                                    artifact_id=summary.artifact_id,
                                    source_id=prior_source,
                                )
            return artifact_id

        def search(
            *,
            query: str,
            tenant_id: str | None = None,
            limit: int = 5,
            include_deleted: bool = False,
        ) -> list[tuple[_StoredItem, float]]:
            ctx = current_context()
            tid = tenant_id or ctx.tenant_id
            results = original_search(
                query=query, tenant_id=tid, limit=limit, include_deleted=include_deleted
            )
            for item, score in results:
                lineage.record_retrieval(
                    RetrievalRecord(
                        backend=self.backend,
                        query=query,
                        artifact_id=item.artifact_id,
                        content=item.content,
                        score=float(score),
                        tenant_id=tid,
                        metadata={"kind": item.metadata.get("kind", "raw")},
                    )
                )
            return results

        def delete_by_source(source_id: str) -> int:
            n = original_delete(source_id)
            lineage.mark_source_revoked(source_id)
            if client._leak_summaries:
                for (_tid, _kind), summary in client._tenant_summary.items():
                    if source_id in summary.metadata.get("absorbed_sources", []):
                        lineage.record_blindspot(
                            backend=self.backend.value,
                            kind="leaked_summary",
                            detail=(
                                f"derived summary {summary.artifact_id} for tenant={summary.tenant_id} "
                                f"absorbed source {source_id} and survives the delete"
                            ),
                        )
            return n

        client.add = add  # type: ignore[assignment]
        client.search = search  # type: ignore[assignment]
        client.delete_by_source = delete_by_source  # type: ignore[assignment]
        client._ferryte_patched = True
        client._ferryte_original_add = original_add
        client._ferryte_original_search = original_search
        client._ferryte_original_delete = original_delete
        return client

    def unpatch(self, client: InMemoryVectorStore) -> None:
        if not getattr(client, "_ferryte_patched", False):
            return
        client.add = client._ferryte_original_add  # type: ignore[assignment]
        client.search = client._ferryte_original_search  # type: ignore[assignment]
        client.delete_by_source = client._ferryte_original_delete  # type: ignore[assignment]
        client._ferryte_patched = False

    def delete_source(
        self, client: InMemoryVectorStore, *, source_id: str, tenant_id: str | None = None
    ) -> int:
        return client.delete_by_source(source_id)

    def list_artifacts_for_source(
        self,
        client: InMemoryVectorStore,
        *,
        source_id: str,
        tenant_id: str | None = None,
    ) -> Iterable[WriteRecord]:
        out: list[WriteRecord] = []
        for item in client.raw_items():
            absorbed = item.metadata.get("absorbed_sources", [])
            if source_id in absorbed:
                out.append(
                    WriteRecord(
                        backend=self.backend,
                        artifact_id=item.artifact_id,
                        content=item.content,
                        source_id=source_id,
                        tenant_id=item.tenant_id,
                        kind=item.metadata.get("kind", "raw"),
                        metadata=dict(item.metadata),
                    )
                )
        return out

    def probe(
        self,
        client: InMemoryVectorStore,
        *,
        query: str,
        tenant_id: str | None = None,
        limit: int = 5,
    ) -> list[RetrievalRecord]:
        results = client.search(query=query, tenant_id=tenant_id, limit=limit)
        return [
            RetrievalRecord(
                backend=self.backend,
                query=query,
                artifact_id=item.artifact_id,
                content=item.content,
                score=float(score),
                tenant_id=item.tenant_id,
            )
            for item, score in results
        ]
