"""`ferryte why` — answer attribution over the lineage graph."""

from __future__ import annotations

import time

from ferryte.adapters.base import BackendKind, RetrievalRecord, WriteRecord
from ferryte.lineage.graph import LineageGraph
from ferryte.lineage.store import LineageStore
from ferryte.oracle.attribute import attribute_answer


def _graph(tmp_path) -> LineageGraph:
    return LineageGraph(LineageStore(tmp_path / "lineage.db"))


def _write(g: LineageGraph, *, aid: str, content: str, source: str, tenant: str) -> None:
    g.record_write(
        WriteRecord(
            backend=BackendKind.VECTOR,
            artifact_id=aid,
            content=content,
            source_id=source,
            tenant_id=tenant,
        )
    )


def test_attributes_answer_to_matching_memory(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m-plan", content="Customer acme is on the Legacy Free plan.", source="ticket-1", tenant="acme")
    _write(g, aid="m-noise", content="Customer acme prefers email over phone.", source="ticket-2", tenant="acme")

    result = attribute_answer("You're on the Legacy Free plan.", lineage=g, tenant_id="acme")

    assert result.top is not None
    assert result.top.artifact_id == "m-plan"
    assert result.top.score > 0.5
    # the source is traced back
    assert result.top.sources[0]["source_id"] == "ticket-1"


def test_retrieved_memory_outranks_merely_similar(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m-retrieved", content="The launch code is orion delta seven.", source="s1", tenant="acme")
    _write(g, aid="m-similar", content="The launch code is orion delta seven.", source="s2", tenant="acme")
    # only one of the two identical memories actually reached the prompt
    g.record_retrieval(
        RetrievalRecord(
            backend=BackendKind.VECTOR,
            query="what is the launch code?",
            artifact_id="m-retrieved",
            content="The launch code is orion delta seven.",
            tenant_id="acme",
        )
    )

    result = attribute_answer(
        "the launch code is orion delta seven",
        lineage=g,
        query="what is the launch code?",
        tenant_id="acme",
    )

    assert result.top is not None
    assert result.top.artifact_id == "m-retrieved"
    assert result.top.retrieved is True


def test_revoked_source_is_flagged_phantom(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m-secret", content="Project atlas access token is zulu nine.", source="doc-1", tenant="acme")
    g.mark_source_revoked("doc-1")

    result = attribute_answer("the atlas access token is zulu nine", lineage=g, tenant_id="acme")

    assert result.top is not None
    assert result.top.artifact_id == "m-secret"
    assert "phantom-memory" in result.top.diagnoses


def test_cross_tenant_memory_is_flagged(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m-b", content="Beta corp revenue is forty two million.", source="doc-b", tenant="beta")

    # tenant 'acme' saw an answer sourced from beta's memory
    result = attribute_answer(
        "beta corp revenue is forty two million", lineage=g, tenant_id="acme"
    )

    assert result.top is not None
    assert "cross-tenant" in result.top.diagnoses


def test_no_match_returns_empty(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m1", content="Customer acme is on the Pro plan.", source="s1", tenant="acme")

    result = attribute_answer("the weather in tokyo is sunny today", lineage=g, tenant_id="acme")

    assert result.candidates == []


def test_idf_rare_token_match_outranks_common_token_match(tmp_path) -> None:
    """Sharing a rare token is evidence; sharing a corpus-common one is noise."""
    g = _graph(tmp_path)
    for i in range(5):
        _write(g, aid=f"m-fill-{i}", content=f"shipping policy update number {i}",
               source=f"s-fill-{i}", tenant="acme")
    # Both candidates share exactly one token with the answer; 'quixote' is rare,
    # 'shipping' appears in every filler memory.
    _write(g, aid="m-rare", content="quixote incident report", source="s-rare", tenant="acme")
    _write(g, aid="m-common", content="shipping incident report", source="s-common", tenant="acme")

    result = attribute_answer("quixote shipping", lineage=g, tenant_id="acme", limit=10)

    assert result.top is not None
    assert result.top.artifact_id == "m-rare"
    by_id = {c.artifact_id: c for c in result.candidates}
    assert "m-common" in by_id
    assert by_id["m-rare"].score > by_id["m-common"].score


def test_shared_span_is_reported_as_evidence(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m-plan", content="Customer acme is on the Legacy Free plan.",
           source="ticket-1", tenant="acme")

    result = attribute_answer(
        "Our records show you are on the Legacy Free plan today.",
        lineage=g, tenant_id="acme",
    )

    assert result.top is not None
    assert result.top.artifact_id == "m-plan"
    assert result.top.method == "span"
    assert "legacy free plan" in result.top.evidence["span"]


def test_recorded_answer_anchors_attribution(tmp_path) -> None:
    """The retrieval→answer edge: a memory recorded in the answer's context is a
    confirmed candidate even with zero lexical overlap."""
    g = _graph(tmp_path)
    _write(g, aid="m-pol", content="Enterprise renewals receive a twenty percent discount.",
           source="policy-7", tenant="acme")
    _write(g, aid="m-other", content="Acme support tier is gold.", source="crm-2", tenant="acme")

    answer = "done, everything has been applied for you"  # no overlap with either memory
    g.record_answer(
        answer_id="turn-42", content=answer, query="apply the discount",
        tenant_id="acme", artifact_ids=["m-pol"],
    )

    result = attribute_answer(answer, lineage=g, tenant_id="acme")

    assert result.top is not None
    assert result.top.artifact_id == "m-pol"
    assert result.top.method == "recorded-answer"
    assert result.top.evidence["recorded_answer_id"] == "turn-42"
    # the un-anchored memory has no signal at all and must not appear
    assert all(c.artifact_id != "m-other" for c in result.candidates)


def test_supersession_edge_makes_stale_belief_structural(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m-old", content="Customer acme is on the Legacy Free plan.",
           source="ticket-1", tenant="acme")
    _write(g, aid="m-new", content="Customer acme upgraded to the Pro plan.",
           source="billing-1", tenant="acme")
    g.record_supersession(old_artifact_id="m-old", new_artifact_id="m-new", reason="billing sync")

    result = attribute_answer("you are on the legacy free plan", lineage=g, tenant_id="acme")

    assert result.top is not None
    assert result.top.artifact_id == "m-old"
    assert "stale-belief" in result.top.diagnoses
    assert result.top.evidence["superseded_by"] == "m-new"


def test_own_summary_does_not_make_a_memory_stale(tmp_path) -> None:
    """A newer artifact derived from the *same* source (a summary/copy of this
    memory) is the same belief restated — not a competing newer fact."""
    g = _graph(tmp_path)
    _write(g, aid="m-fact", content="Customer acme is on the Legacy Free plan.",
           source="ticket-1", tenant="acme")
    time.sleep(0.01)
    # summary re-derives the same single source, later
    _write(g, aid="m-sum", content="Summary: acme is on the Legacy Free plan.",
           source="ticket-1", tenant="acme")

    result = attribute_answer("you are on the legacy free plan", lineage=g, tenant_id="acme")
    top = result.top
    assert top is not None and top.artifact_id in ("m-fact", "m-sum")
    by_id = {c.artifact_id: c for c in result.candidates}
    assert "stale-belief" not in by_id["m-fact"].diagnoses

    # a genuinely newer fact from a different source *does* mark it stale
    time.sleep(0.01)
    _write(g, aid="m-newer", content="Correction: acme moved off the legacy free plan tier.",
           source="billing-2", tenant="acme")
    result = attribute_answer("you are on the legacy free plan", lineage=g, tenant_id="acme")
    by_id = {c.artifact_id: c for c in result.candidates}
    assert "stale-belief" in by_id["m-fact"].diagnoses
    assert by_id["m-fact"].evidence["newer_artifact"] == "m-newer"


def test_hub_memory_flagged_on_outlier_query_fanout(tmp_path) -> None:
    """MINJA-style access signature: one memory retrieved across many distinct
    queries while the rest of the corpus is retrieved normally."""
    g = _graph(tmp_path)
    _write(g, aid="m-hub", content="Wire transfers go to account zz99 route.",
           source="s-hub", tenant="acme")
    _write(g, aid="m-a", content="Invoices are due in thirty days.", source="s-a", tenant="acme")
    _write(g, aid="m-b", content="Refunds require a manager approval.", source="s-b", tenant="acme")

    def _retrieve(aid: str, q: str) -> None:
        g.record_retrieval(RetrievalRecord(
            backend=BackendKind.VECTOR, query=q, artifact_id=aid,
            content="", tenant_id="acme",
        ))

    for i in range(6):
        _retrieve("m-hub", f"unrelated question number {i}")
    _retrieve("m-a", "when are invoices due")
    _retrieve("m-b", "how do refunds work")

    result = attribute_answer("send the wire to account zz99", lineage=g, tenant_id="acme")

    assert result.top is not None
    assert result.top.artifact_id == "m-hub"
    assert "hub-memory" in result.top.diagnoses
    assert result.top.evidence["distinct_queries"] == 6


def test_zombie_requires_retrieval_after_the_delete(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m-z", content="The vault code is nine four eight one tango.",
           source="s-z", tenant="acme")
    g.record_retrieval(RetrievalRecord(
        backend=BackendKind.VECTOR, query="what is the vault code",
        artifact_id="m-z", content="", tenant_id="acme",
    ))
    # deleted *after* that retrieval — history, not a zombie
    g.store.mark_artifact_deleted("m-z", at=time.time() + 1)
    result = attribute_answer("the vault code is nine four eight one tango", lineage=g, tenant_id="acme")
    assert result.top is not None
    assert "zombie-memory" not in result.top.diagnoses

    # now it is retrieved again, after the deletion timestamp — that's the bug
    g.store.mark_artifact_deleted("m-z", at=time.time() - 60)
    g.record_retrieval(RetrievalRecord(
        backend=BackendKind.VECTOR, query="what is the vault code",
        artifact_id="m-z", content="", tenant_id="acme",
    ))
    result = attribute_answer("the vault code is nine four eight one tango", lineage=g, tenant_id="acme")
    assert result.top is not None
    assert "zombie-memory" in result.top.diagnoses


def test_since_window_scopes_retrieval_evidence(tmp_path) -> None:
    g = _graph(tmp_path)
    _write(g, aid="m-s", content="Customer acme is on the Legacy Free plan.",
           source="s-1", tenant="acme")
    g.record_retrieval(RetrievalRecord(
        backend=BackendKind.VECTOR, query="what plan", artifact_id="m-s",
        content="", tenant_id="acme",
    ))

    fresh = attribute_answer("legacy free plan", lineage=g, tenant_id="acme")
    assert fresh.top is not None and fresh.top.retrieved is True

    future_window = attribute_answer(
        "legacy free plan", lineage=g, tenant_id="acme", since=time.time() + 60
    )
    assert future_window.top is not None
    assert future_window.top.retrieved is False
    assert future_window.top.retrieval_count == 0


def test_prefilter_path_finds_the_same_needle(tmp_path) -> None:
    g = _graph(tmp_path)
    for i in range(30):
        _write(g, aid=f"m-noise-{i}", content=f"meeting notes batch {i} action items pending",
               source=f"s-{i}", tenant="acme")
    _write(g, aid="m-needle", content="Customer acme is on the Legacy Free plan.",
           source="ticket-1", tenant="acme")

    full = attribute_answer("you are on the legacy free plan", lineage=g, tenant_id="acme",
                            prefilter=False)
    filtered = attribute_answer("you are on the legacy free plan", lineage=g, tenant_id="acme",
                                prefilter=True)

    assert full.top is not None and full.top.artifact_id == "m-needle"
    if g.store._fts_enabled:  # noqa: SLF001 — FTS availability depends on the SQLite build
        assert filtered.top is not None
        assert filtered.top.artifact_id == "m-needle"
