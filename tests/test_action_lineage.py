"""J2 — action/consequence lineage: recallable vs propagated leaks."""

from __future__ import annotations

from ferryte.lineage.blast import compute_blast_radius
from ferryte.lineage.graph import LineageGraph
from ferryte.lineage.store import LineageStore


def _graph(tmp_path) -> LineageGraph:
    return LineageGraph(LineageStore(tmp_path / "lineage.db"))


def test_action_consuming_derived_artifact_is_propagated(tmp_path) -> None:
    g = _graph(tmp_path)
    g.store.upsert_source(source_id="src-1", tenant_id="acme")
    g.store.record_artifact(artifact_id="art-1", backend="vector", kind="summary", content="x")
    g.store.record_derivation(artifact_id="art-1", source_id="src-1")

    # the agent emailed a customer using the derived artifact
    g.record_action(
        action_id="act-1",
        kind="email_sent",
        artifact_ids=["art-1"],
        tenant_id="acme",
        detail={"to": "customer@example.com"},
    )

    blast = compute_blast_radius(g, source_id="src-1")
    assert blast.propagated is True
    assert blast.propagated_count == 1
    assert blast.propagated_actions[0]["kind"] == "email_sent"


def test_no_action_means_recallable_only(tmp_path) -> None:
    g = _graph(tmp_path)
    g.store.upsert_source(source_id="src-2", tenant_id="acme")
    g.store.record_artifact(artifact_id="art-2", backend="vector", kind="summary", content="x")
    g.store.record_derivation(artifact_id="art-2", source_id="src-2")

    blast = compute_blast_radius(g, source_id="src-2")
    assert blast.propagated is False and blast.propagated_count == 0


def test_action_on_unrelated_artifact_is_not_attributed(tmp_path) -> None:
    g = _graph(tmp_path)
    g.store.upsert_source(source_id="src-3", tenant_id="acme")
    g.store.record_artifact(artifact_id="art-3", backend="vector", kind="summary", content="x")
    g.store.record_derivation(artifact_id="art-3", source_id="src-3")
    # an action that consumed a *different* artifact must not attach to src-3
    g.store.record_artifact(artifact_id="other", backend="vector", kind="raw", content="y")
    g.record_action(action_id="act-x", kind="decision", artifact_ids=["other"], tenant_id="acme")

    assert compute_blast_radius(g, source_id="src-3").propagated is False
