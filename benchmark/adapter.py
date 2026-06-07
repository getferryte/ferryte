"""Ferryte adapter for `SummaryMemory`.

Implements the 5-method `Adapter` protocol so the existing Ferryte scenarios
(source-revocation, cross-tenant, stale-fact, memory-poisoning) run unmodified
against the benchmark's system-under-test. We resolve source/tenant from the
`tag()` context the runner sets, exactly like the built-in vector adapter.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ferryte.adapters.base import (
    AdapterCapability,
    BackendKind,
    RetrievalRecord,
    WriteRecord,
)
from ferryte.context import current_context
from ferryte.lineage import get_lineage

from .memory import SummaryMemory


class SummaryMemoryAdapter:
    name = "summary-memory"
    backend = BackendKind.VECTOR
    capabilities = frozenset(
        {
            AdapterCapability.WRITE_CAPTURE,
            AdapterCapability.READ_CAPTURE,
            AdapterCapability.SOURCE_DELETE,
            AdapterCapability.TENANT_SCOPING,
            AdapterCapability.DERIVED_ENUMERATION,
        }
    )

    def patch(self, client: SummaryMemory) -> SummaryMemory:
        if getattr(client, "_ferryte_patched", False):
            return client
        lineage = get_lineage()
        orig_add = client.add
        orig_search = client.search
        orig_delete = client.delete_by_source

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
            aid = orig_add(content=content, source_id=sid, tenant_id=tid, metadata=metadata)
            lineage.record_write(
                WriteRecord(
                    backend=self.backend,
                    artifact_id=aid,
                    content=content,
                    source_id=sid,
                    tenant_id=tid,
                    kind="raw",
                    metadata=dict(metadata or {}),
                )
            )
            sinfo = client._summaries.get(tid) if tid else None
            if sinfo:
                lineage.record_write(
                    WriteRecord(
                        backend=self.backend,
                        artifact_id=sinfo["artifact_id"],
                        content=sinfo["text"],
                        source_id=sid,
                        tenant_id=tid,
                        kind="summary",
                        metadata={"kind": "summary", "absorbed_sources": list(sinfo["absorbed"])},
                    )
                )
                for prior in sinfo["absorbed"]:
                    if prior and prior != sid:
                        lineage.record_derivation(artifact_id=sinfo["artifact_id"], source_id=prior)
            return aid

        def search(
            *, query: str, tenant_id: str | None = None, limit: int = 5
        ) -> list[tuple[Any, float]]:
            tid = tenant_id or current_context().tenant_id
            results = orig_search(query=query, tenant_id=tid, limit=limit)
            for it, score in results:
                lineage.record_retrieval(
                    RetrievalRecord(
                        backend=self.backend,
                        query=query,
                        artifact_id=it.artifact_id,
                        content=it.content,
                        score=float(score),
                        tenant_id=tid,
                        metadata={"kind": it.kind},
                    )
                )
            return results

        def delete_by_source(source_id: str, *, tenant_id: str | None = None) -> int:
            n = orig_delete(source_id, tenant_id=tenant_id)
            lineage.mark_source_revoked(source_id)
            if client.leak_summaries:
                for tid, sinfo in client._summaries.items():
                    if source_id in sinfo["absorbed"]:
                        lineage.record_blindspot(
                            backend=self.backend.value,
                            kind="leaked_summary",
                            detail=(
                                f"derived summary {sinfo['artifact_id']} for tenant={tid} "
                                f"absorbed source {source_id} and survives the delete"
                            ),
                        )
            return n

        client.add = add  # type: ignore[method-assign]
        client.search = search  # type: ignore[method-assign]
        client.delete_by_source = delete_by_source  # type: ignore[method-assign]
        client._ferryte_patched = True
        client._ferryte_orig = (orig_add, orig_search, orig_delete)
        return client

    def unpatch(self, client: SummaryMemory) -> None:
        if not getattr(client, "_ferryte_patched", False):
            return
        orig_add, orig_search, orig_delete = client._ferryte_orig
        client.add = orig_add  # type: ignore[method-assign]
        client.search = orig_search  # type: ignore[method-assign]
        client.delete_by_source = orig_delete  # type: ignore[method-assign]
        client._ferryte_patched = False

    def delete_source(
        self, client: SummaryMemory, *, source_id: str, tenant_id: str | None = None
    ) -> int:
        return client.delete_by_source(source_id, tenant_id=tenant_id)

    def list_artifacts_for_source(
        self, client: SummaryMemory, *, source_id: str, tenant_id: str | None = None
    ) -> Iterable[WriteRecord]:
        out: list[WriteRecord] = []
        for it in client.store.items():
            absorbed = it.metadata.get("absorbed_sources", [])
            if it.source_id == source_id or source_id in absorbed:
                out.append(
                    WriteRecord(
                        backend=self.backend,
                        artifact_id=it.artifact_id,
                        content=it.content,
                        source_id=source_id,
                        tenant_id=it.tenant_id,
                        kind=it.kind,
                        metadata=dict(it.metadata),
                    )
                )
        return out

    def probe(
        self, client: SummaryMemory, *, query: str, tenant_id: str | None = None, limit: int = 5
    ) -> list[RetrievalRecord]:
        results = client.search(query=query, tenant_id=tenant_id, limit=limit)
        return [
            RetrievalRecord(
                backend=self.backend,
                query=query,
                artifact_id=it.artifact_id,
                content=it.content,
                score=float(score),
                tenant_id=it.tenant_id,
                metadata={"kind": it.kind},
            )
            for it, score in results
        ]
