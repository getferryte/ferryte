"""Counterfactual replay — retrieval-layer ablation of a suspect memory."""

from __future__ import annotations

import ferryte
from ferryte.adapters.vector import InMemoryVectorStore, VectorAdapter
from ferryte.oracle.replay import replay_query


def _seed_store() -> tuple[InMemoryVectorStore, str, str]:
    """A store holding a stale fact (lexically closer to the query) and the
    fresh fact that should have answered instead."""
    store = InMemoryVectorStore(leak_summaries=False)
    old_id = store.add(content="Customer acme is on the Legacy Free plan.")
    new_id = store.add(content="Customer acme upgraded to the Pro plan.")
    return store, old_id, new_id


def test_replay_names_the_replacement_memory() -> None:
    store, old_id, new_id = _seed_store()

    report = replay_query(
        "what plan is customer acme on",
        old_id,
        limit=1,
        clients=[(store, VectorAdapter())],
    )

    assert report.verdict == "causal"
    assert report.causal is True
    assert report.suspect_rank == 1
    assert [c.artifact_id for c in report.factual] == [old_id]
    assert report.replacement is not None
    assert report.replacement.artifact_id == new_id
    assert "Pro plan" in report.replacement.content


def test_replay_when_suspect_shares_context_with_replacement() -> None:
    store, old_id, new_id = _seed_store()

    report = replay_query(
        "what plan is customer acme on",
        old_id,
        limit=3,
        clients=[(store, VectorAdapter())],
    )

    assert report.verdict == "causal"
    # both fit in the top-3, so the "replacement" is what wins the top slot
    assert report.replacement is not None
    assert report.replacement.artifact_id == new_id


def test_replay_reports_not_retrieved() -> None:
    store, _old_id, _new_id = _seed_store()

    report = replay_query(
        "what plan is customer acme on",
        "no-such-artifact",
        limit=3,
        clients=[(store, VectorAdapter())],
    )

    assert report.verdict == "not-retrieved"
    assert report.causal is False
    assert report.factual  # context was still captured for inspection


def test_replay_without_clients_is_honest() -> None:
    ferryte.uninstrument()
    report = replay_query("any question", "some-artifact")
    assert report.verdict == "no-clients"


def test_replay_uses_active_instrumentation() -> None:
    ferryte.instrument()
    store = InMemoryVectorStore(leak_summaries=False)  # auto-tracked by the hook
    old_id = store.add(content="The office wifi password is tango tango nine.")

    report = replay_query("what is the office wifi password", old_id, limit=2)

    assert report.verdict == "causal"
    assert report.suspect_rank == 1
