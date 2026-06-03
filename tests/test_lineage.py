from pathlib import Path

from ferryte.adapters.base import BackendKind, WriteRecord
from ferryte.lineage import LineageGraph, LineageStore, compute_blast_radius


def test_store_roundtrip(fresh_ferryte: Path) -> None:
    store = LineageStore(fresh_ferryte / "lineage.db")
    g = LineageGraph(store)
    g.record_write(
        WriteRecord(
            backend=BackendKind.VECTOR,
            artifact_id="a-1",
            content="hello world",
            source_id="src-1",
            tenant_id="tenant-A",
        )
    )
    g.record_write(
        WriteRecord(
            backend=BackendKind.VECTOR,
            artifact_id="a-2",
            content="another fact",
            source_id="src-1",
            tenant_id="tenant-A",
        )
    )
    arts = g.artifacts_for_source("src-1")
    assert {a["artifact_id"] for a in arts} == {"a-1", "a-2"}
    counts = g.counts()
    assert counts["sources"] == 1
    assert counts["artifacts"] == 2
    assert counts["derivations"] == 2


def test_blast_radius_includes_retrievals(fresh_ferryte: Path) -> None:
    store = LineageStore(fresh_ferryte / "lineage.db")
    g = LineageGraph(store)
    g.record_write(
        WriteRecord(
            backend=BackendKind.VECTOR,
            artifact_id="a-1",
            content="secret CODE-123",
            source_id="src-1",
            tenant_id="t",
        )
    )
    from ferryte.adapters.base import RetrievalRecord

    g.record_retrieval(
        RetrievalRecord(
            backend=BackendKind.VECTOR,
            query="what was the code",
            artifact_id="a-1",
            content="secret CODE-123",
            score=0.9,
            tenant_id="t",
        )
    )
    blast = compute_blast_radius(g, source_id="src-1")
    assert blast.artifact_count == 1
    assert blast.retrieval_count == 1
