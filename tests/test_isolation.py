"""Tests for the standalone isolation check.

These use a deliberately-leaky fake store rather than a real database so the
suite stays fast and driver-free. The fake models the three real-world shapes
the checker must distinguish:

  * a store that honours its tenant filter          -> PASS
  * a store whose filter is broken                  -> FAIL (filtered leak)
  * a store whose filter works but whose *ranking*
    surfaces a neighbour's content to a similar
    query                                            -> FAIL (semantic leak)

The third case is the one that matters commercially: nothing is misconfigured
in an obvious way, and no log shows an error.
"""

from __future__ import annotations

from typing import Any

import pytest

from ferryte.oracle.isolation import run_isolation_check
from ferryte.oracle.runner import Severity


class FakeStore:
    """Minimal store with a switchable isolation bug."""

    def __init__(self, rows: list[dict[str, Any]], *, honour_filter: bool = True) -> None:
        self.rows = rows
        self.honour_filter = honour_filter

    def search(
        self, *, query: str, tenant_id: str | None = None, limit: int = 5
    ) -> list[dict[str, Any]]:
        terms = {t for t in query.lower().split() if len(t) > 2}
        scope = self.rows
        if tenant_id is not None and self.honour_filter:
            scope = [r for r in self.rows if r.get("tenant_id") == tenant_id]
        hits = []
        for r in scope:
            content = str(r.get("content", "")).lower()
            overlap = sum(1 for t in terms if t in content)
            if overlap:
                hits.append((overlap, r))
        hits.sort(key=lambda kv: kv[0], reverse=True)
        return [dict(r, score=float(n)) for n, r in hits[:limit]]

    def search_unfiltered(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.search(query=query, tenant_id=None, limit=limit)

    def documents_for_tenant(self, tenant_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        # Every real vector store can enumerate by tenant (SELECT / get / scroll);
        # the fake mirrors that so the semantic probe has something to derive from.
        return [r for r in self.rows if r.get("tenant_id") == tenant_id][:limit]

    def tenants(self, *, limit: int = 100) -> list[str]:
        out: list[str] = []
        for r in self.rows:
            t = r.get("tenant_id")
            if t and t not in out:
                out.append(str(t))
        return out[:limit]


@pytest.fixture()
def rows() -> list[dict[str, Any]]:
    return [
        {
            "id": "a1",
            "tenant_id": "acme",
            "content": "Acme quarterly revenue forecast shows margin compression in Q3",
        },
        {
            "id": "a2",
            "tenant_id": "acme",
            "content": "Acme renewal terms include a bespoke discount of eighteen percent",
        },
        {
            "id": "g1",
            "tenant_id": "globex",
            "content": "Globex quarterly revenue forecast shows margin compression in Q3",
        },
        {
            "id": "g2",
            "tenant_id": "globex",
            "content": "Globex onboarding checklist for new enterprise accounts",
        },
    ]


def test_clean_store_passes(rows: list[dict[str, Any]]) -> None:
    store = FakeStore(rows, honour_filter=True)
    report = run_isolation_check(
        store,
        queries=["quarterly revenue forecast"],
        backend="fake",
    )
    assert report.filtered_leaks == []
    assert report.semantic_leaks == []
    # Unfiltered exposure is expected and is NOT a failure — it is the measured
    # blast radius of a hypothetical missing filter.
    assert report.unfiltered_exposure
    assert report.severity in {Severity.PASS, Severity.WARN}


def test_broken_filter_is_a_hard_fail(rows: list[dict[str, Any]]) -> None:
    store = FakeStore(rows, honour_filter=False)
    report = run_isolation_check(
        store,
        tenants=["acme", "globex"],
        queries=["quarterly revenue forecast"],
        backend="fake",
    )
    assert report.filtered_leaks, "a broken tenant filter must surface as a filtered leak"
    assert report.severity == Severity.FAIL
    leak = report.filtered_leaks[0]
    assert leak.querying_tenant != leak.owning_tenant
    assert leak.excerpt  # evidence is mandatory — a finding without it is unusable


def test_semantic_probe_finds_neighbour_leak(rows: list[dict[str, Any]]) -> None:
    """The filter is broken only for ranking-adjacent content.

    This models the published failure mode: an ordinary question from one tenant
    pulls a semantically similar document belonging to another.
    """

    class RankingLeakStore(FakeStore):
        def search(
            self, *, query: str, tenant_id: str | None = None, limit: int = 5
        ) -> list[dict[str, Any]]:
            # Honour the filter for short/simple queries but not for long
            # content-derived ones — exactly the shape that hides in production.
            honour = len(query.split()) < 6
            saved = self.honour_filter
            self.honour_filter = honour
            try:
                return super().search(query=query, tenant_id=tenant_id, limit=limit)
            finally:
                self.honour_filter = saved

    store = RankingLeakStore(rows)
    report = run_isolation_check(
        store,
        tenants=["acme", "globex"],
        queries=None,
        semantic_probe=True,
        backend="fake",
    )
    assert report.semantic_leaks, "semantic probe should catch ranking-based cross-tenant reach"
    assert report.severity == Severity.FAIL


def test_single_tenant_is_not_reported_as_a_pass() -> None:
    store = FakeStore([{"id": "x", "tenant_id": "solo", "content": "only tenant here"}])
    report = run_isolation_check(store, backend="fake")
    assert report.severity == Severity.WARN
    assert any("single tenant" in b.lower() for b in report.blind_spots)
    assert not report.passed


def test_search_failures_become_blind_spots_not_silence(rows: list[dict[str, Any]]) -> None:
    class ExplodingStore(FakeStore):
        def search(self, **kwargs: Any) -> list[dict[str, Any]]:
            raise RuntimeError("connection reset")

    report = run_isolation_check(
        ExplodingStore(rows),
        tenants=["acme", "globex"],
        queries=["anything"],
        backend="fake",
    )
    assert report.blind_spots
    assert any("connection reset" in b for b in report.blind_spots)
    # A store we could not query must never be reported as clean.
    assert not report.passed


def test_report_serialises_with_evidence(rows: list[dict[str, Any]]) -> None:
    report = run_isolation_check(
        FakeStore(rows, honour_filter=False),
        tenants=["acme", "globex"],
        queries=["quarterly revenue forecast"],
        backend="fake",
    )
    payload = report.to_dict()
    assert payload["check"] == "isolation"
    assert payload["severity"] == "fail"
    assert payload["filtered_leaks"][0]["excerpt"]
    findings = report.to_findings()
    assert any(f.code == "cross_tenant_filtered_leak" for f in findings)
