"""Answer lineage, supersession edges, FTS prefiltering, retrieval fan-out."""

from __future__ import annotations

import time

import pytest

from ferryte.adapters.base import BackendKind, RetrievalRecord, WriteRecord
from ferryte.lineage.graph import LineageGraph
from ferryte.lineage.store import LineageStore
from ferryte.oracle.attribute import attribute_answer


def _graph(tmp_path, **kw) -> LineageGraph:
    return LineageGraph(LineageStore(tmp_path / "lineage.db", **kw))


def _write(g: LineageGraph, *, aid: str, content: str, source: str, tenant: str = "acme") -> None:
    g.record_write(
        WriteRecord(
            backend=BackendKind.VECTOR,
            artifact_id=aid,
            content=content,
            source_id=source,
            tenant_id=tenant,
        )
    )


def test_record_answer_roundtrip(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m-1", content="fact one", source="s-1")
    _write(g, aid="m-2", content="fact two", source="s-2")

    g.record_answer(
        answer_id="turn-1",
        content="the agent said something",
        query="what happened",
        tenant_id="acme",
        artifact_ids=["m-1", "m-2", "m-1"],  # dupes are de-duped
        metadata={"model": "test"},
    )

    assert sorted(g.artifact_ids_for_answer("turn-1")) == ["m-1", "m-2"]
    answers = g.answers_matching(tenant_id="acme")
    assert len(answers) == 1
    assert answers[0]["answer_id"] == "turn-1"
    assert answers[0]["content"] == "the agent said something"
    assert answers[0]["metadata"] == {"model": "test"}

    counts = g.counts()
    assert counts["answers"] == 1
    assert counts["answer_inputs"] == 2


def test_answers_matching_filters(tmp_path) -> None:
    g = _graph(tmp_path)
    g.record_answer(answer_id="a-acme", content="x", tenant_id="acme", artifact_ids=[])
    g.record_answer(answer_id="a-beta", content="y", tenant_id="beta", artifact_ids=[])

    assert [a["answer_id"] for a in g.answers_matching(tenant_id="acme")] == ["a-acme"]
    assert g.answers_matching(since=time.time() + 60) == []
    assert len(g.answers_matching()) == 2


def test_supersession_edge_roundtrip(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m-old", content="old belief", source="s-1")
    _write(g, aid="m-new", content="new belief", source="s-2")

    g.record_supersession(old_artifact_id="m-old", new_artifact_id="m-new", reason="update")

    edges = g.supersessions_for("m-old")
    assert len(edges) == 1
    assert edges[0]["new_artifact_id"] == "m-new"
    assert edges[0]["reason"] == "update"
    assert g.supersessions_for("m-new") == []
    assert g.counts()["supersessions"] == 1


def test_retrieval_query_counts_are_distinct(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m-1", content="something", source="s-1")
    for q in ("q one", "q two", "q one"):  # repeated query counts once
        g.record_retrieval(
            RetrievalRecord(
                backend=BackendKind.VECTOR, query=q, artifact_id="m-1",
                content="", tenant_id="acme",
            )
        )

    assert g.retrieval_query_counts() == {"m-1": 2}


def test_fts_candidate_prefilter(tmp_path) -> None:
    g = _graph(tmp_path)
    if not g.store._fts_enabled:  # noqa: SLF001
        pytest.skip("SQLite build without FTS5")
    _write(g, aid="m-plan", content="Customer acme is on the Legacy Free plan.", source="s-1")
    _write(g, aid="m-other", content="Weekly standup notes for the platform team.", source="s-2")

    ids = g.candidate_artifact_ids(["legacy", "plan"])
    assert ids is not None
    assert "m-plan" in ids
    assert "m-other" not in ids

    # content updates keep the index in sync (artifact upsert rewrites content)
    g.record_write(
        WriteRecord(
            backend=BackendKind.VECTOR, artifact_id="m-other",
            content="The legacy migration is scheduled.", source_id="s-2", tenant_id="acme",
        )
    )
    ids = g.candidate_artifact_ids(["legacy"])
    assert ids is not None and "m-other" in ids


def test_artifacts_by_ids(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m-1", content="alpha", source="s-1")
    _write(g, aid="m-2", content="beta", source="s-2")

    rows = g.artifacts_by_ids(["m-2", "m-2", "missing"])
    assert [r["artifact_id"] for r in rows] == ["m-2"]
    assert g.artifacts_by_ids([]) == []


def test_recorded_answer_anchoring_survives_fingerprint_mode(tmp_path) -> None:
    """In fingerprint mode content is hashed, so lexical overlap is impossible —
    but the answer edge still anchors attribution via deterministic fp equality."""
    g = _graph(tmp_path, fingerprint_mode=True, fingerprint_salt="test-salt")
    _write(g, aid="m-ctx", content="Enterprise renewals receive a discount.", source="s-1")

    answer = "done, the discount has been applied"
    g.record_answer(answer_id="turn-9", content=answer, tenant_id="acme", artifact_ids=["m-ctx"])

    result = attribute_answer(answer, lineage=g, tenant_id="acme")

    assert result.top is not None
    assert result.top.artifact_id == "m-ctx"
    assert result.top.method == "recorded-answer"
