"""High-level lineage graph: the source → derived-artifact view adapters write into.

This is a thin facade over ``LineageStore`` so adapters never touch SQL directly
and we can swap the storage layer later (DuckDB / Postgres) without touching them.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..adapters.base import RetrievalRecord, WriteRecord
from ..config import get_config
from .store import LineageStore


class LineageGraph:
    def __init__(self, store: LineageStore) -> None:
        self.store = store

    # ----- ingestion called by adapters --------------------------------------

    def record_write(self, write: WriteRecord) -> None:
        if write.source_id:
            self.store.upsert_source(source_id=write.source_id, tenant_id=write.tenant_id)
        self.store.record_artifact(
            artifact_id=write.artifact_id,
            backend=write.backend.value,
            kind=write.kind,
            content=write.content,
            tenant_id=write.tenant_id,
            metadata=write.metadata,
        )
        if write.source_id:
            self.store.record_derivation(
                artifact_id=write.artifact_id,
                source_id=write.source_id,
            )

    def record_derivation(
        self, *, artifact_id: str, source_id: str, confidence: float = 1.0
    ) -> None:
        self.store.record_derivation(
            artifact_id=artifact_id, source_id=source_id, confidence=confidence
        )

    def record_retrieval(self, retrieval: RetrievalRecord) -> None:
        self.store.record_retrieval(
            backend=retrieval.backend.value,
            query=retrieval.query,
            artifact_id=retrieval.artifact_id,
            content=retrieval.content,
            score=retrieval.score,
            tenant_id=retrieval.tenant_id,
            metadata=retrieval.metadata,
        )

    def record_action(
        self,
        *,
        action_id: str,
        kind: str,
        artifact_ids: Iterable[str],
        tenant_id: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.store.record_action(
            action_id=action_id,
            kind=kind,
            artifact_ids=artifact_ids,
            tenant_id=tenant_id,
            detail=detail,
        )

    def actions_consuming_source(self, source_id: str) -> list[dict[str, Any]]:
        return self.store.actions_consuming_source(source_id)

    def record_answer(
        self,
        *,
        answer_id: str,
        content: str | None,
        query: str | None = None,
        tenant_id: str | None = None,
        artifact_ids: Iterable[str] = (),
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.store.record_answer(
            answer_id=answer_id,
            content=content,
            query=query,
            tenant_id=tenant_id,
            artifact_ids=artifact_ids,
            metadata=metadata,
        )

    def record_supersession(
        self, *, old_artifact_id: str, new_artifact_id: str, reason: str | None = None
    ) -> None:
        self.store.record_supersession(
            old_artifact_id=old_artifact_id,
            new_artifact_id=new_artifact_id,
            reason=reason,
        )

    def record_blindspot(self, *, backend: str, kind: str, detail: str) -> None:
        self.store.record_blindspot(backend=backend, kind=kind, detail=detail)

    def mark_source_revoked(self, source_id: str) -> None:
        self.store.mark_source_revoked(source_id)

    def mark_artifact_deleted(self, artifact_id: str) -> None:
        self.store.mark_artifact_deleted(artifact_id)

    # ----- queries used by oracle + reports ----------------------------------

    def artifacts_for_source(self, source_id: str) -> list[dict[str, Any]]:
        return self.store.artifacts_for_source(source_id)

    def sources(self, tenant_id: str | None = None) -> list[dict[str, Any]]:
        return self.store.sources(tenant_id=tenant_id)

    def sources_for_artifact(self, artifact_id: str) -> list[dict[str, Any]]:
        return self.store.sources_for_artifact(artifact_id)

    def retrievals_for_artifact(
        self, artifact_id: str, since: float | None = None
    ) -> list[dict[str, Any]]:
        return self.store.retrievals_for_artifact(artifact_id, since=since)

    def retrievals_matching(
        self,
        *,
        query_substring: str | None = None,
        tenant_id: str | None = None,
        since: float | None = None,
    ) -> list[dict[str, Any]]:
        return self.store.retrievals_matching(
            query_substring=query_substring, tenant_id=tenant_id, since=since
        )

    def all_artifacts(self) -> Iterable[dict[str, Any]]:
        return self.store.all_artifacts()

    def artifacts_by_ids(self, artifact_ids: Iterable[str]) -> list[dict[str, Any]]:
        return self.store.artifacts_by_ids(artifact_ids)

    def candidate_artifact_ids(
        self, tokens: Iterable[str], *, limit: int = 2000
    ) -> list[str] | None:
        return self.store.candidate_artifact_ids(tokens, limit=limit)

    def answers_matching(
        self,
        *,
        tenant_id: str | None = None,
        since: float | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return self.store.answers_matching(tenant_id=tenant_id, since=since, limit=limit)

    def artifact_ids_for_answer(self, answer_id: str) -> list[str]:
        return self.store.artifact_ids_for_answer(answer_id)

    def supersessions_for(self, artifact_id: str) -> list[dict[str, Any]]:
        return self.store.supersessions_for(artifact_id)

    def retrieval_query_counts(self) -> dict[str, int]:
        return self.store.retrieval_query_counts()

    def blindspots(self) -> list[dict[str, Any]]:
        return self.store.blindspots()

    def counts(self) -> dict[str, int]:
        return self.store.counts()


_LINEAGE: LineageGraph | None = None


def get_lineage(path: Path | None = None) -> LineageGraph:
    """Return the process-wide lineage graph, creating it if needed."""
    global _LINEAGE
    if _LINEAGE is None:
        cfg = get_config()
        cfg.ensure_dirs()
        store = LineageStore(
            path or cfg.resolved_db_path(),
            fingerprint_mode=getattr(cfg, "fingerprint_mode", False),
            fingerprint_salt=getattr(cfg, "fingerprint_salt", None),
        )
        _LINEAGE = LineageGraph(store)
    return _LINEAGE


def reset_lineage_for_tests() -> None:
    global _LINEAGE
    if _LINEAGE is not None:
        _LINEAGE.store.close()
    _LINEAGE = None
