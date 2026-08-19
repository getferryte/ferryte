"""Standalone multi-tenant isolation check.

This is deliberately *not* just the ``cross-tenant-isolation`` scenario with a
nicer name. The scenario answers "did our seeded canary cross tenants?" against
an instrumented app. This module answers a harder, more commercially useful
question against a store it has never seen:

    Given a live vector store with several tenants in it, can tenant B's
    ordinary queries surface tenant A's data — and if the application ever
    dropped its filter, how much would spill?

Three probes, in increasing order of what they prove:

1. **Filtered probe** — query as tenant B *with* the tenant filter the app
   normally uses. A hit belonging to tenant A here is a hard FAIL: the filter
   itself is broken.
2. **Unfiltered probe** — query with no filter at all. This models a single
   forgotten ``where`` clause. It is not proof of a live bug; it is a measure of
   **blast radius** if one is ever introduced. Reported as WARN with a count,
   never as a FAIL, because an unfiltered query is not by itself a defect.
3. **Semantic-neighbour probe** — take tenant A's own documents, derive queries
   *from* them, and run those queries as tenant B. This is the path the
   published research says actually bites: leakage through semantic similarity
   rather than a missing predicate. A hit here means B can reach A's content by
   asking a natural question, which is the failure mode that does not look like
   a bug in any log.

Every finding carries the evidence that produced it — the query, the offending
row id, the owning tenant, and a content excerpt — because a report a security
reviewer cannot audit is not worth sending.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol

from .runner import Finding, Severity

# How much of an offending document to quote in a finding. Enough to prove the
# leak, short enough not to turn the report itself into a data-exfiltration
# artifact — reports get emailed around.
_EXCERPT_CHARS = 160


class IsolationStore(Protocol):
    """The surface an isolation check needs.

    Deliberately narrower than the full Adapter protocol: any store that can be
    queried per-tenant and enumerated can be checked, even read-only, even one
    Ferryte has never written to.
    """

    def search(
        self, *, query: str, tenant_id: str | None = ..., limit: int = ...
    ) -> list[dict[str, Any]]: ...

    def tenants(self, *, limit: int = ...) -> list[str]: ...


@dataclass
class IsolationFinding:
    """One concrete cross-tenant exposure, with its evidence."""

    probe: str
    querying_tenant: str
    owning_tenant: str
    query: str
    artifact_id: str
    excerpt: str
    score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "probe": self.probe,
            "querying_tenant": self.querying_tenant,
            "owning_tenant": self.owning_tenant,
            "query": self.query,
            "artifact_id": self.artifact_id,
            "excerpt": self.excerpt,
            "score": self.score,
        }


@dataclass
class IsolationReport:
    """The artifact. Designed to be pasted into a security questionnaire."""

    backend: str
    tenants_checked: list[str] = field(default_factory=list)
    queries_run: int = 0
    filtered_leaks: list[IsolationFinding] = field(default_factory=list)
    unfiltered_exposure: list[IsolationFinding] = field(default_factory=list)
    semantic_leaks: list[IsolationFinding] = field(default_factory=list)
    blind_spots: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    started_at: float = field(default_factory=time.time)

    @property
    def severity(self) -> Severity:
        if self.filtered_leaks or self.semantic_leaks:
            return Severity.FAIL
        if self.blind_spots:
            return Severity.WARN
        return Severity.PASS

    @property
    def passed(self) -> bool:
        return self.severity == Severity.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": "isolation",
            "backend": self.backend,
            "severity": self.severity.value,
            "passed": self.passed,
            "tenants_checked": list(self.tenants_checked),
            "queries_run": self.queries_run,
            "filtered_leaks": [f.to_dict() for f in self.filtered_leaks],
            "unfiltered_exposure": [f.to_dict() for f in self.unfiltered_exposure],
            "semantic_leaks": [f.to_dict() for f in self.semantic_leaks],
            "blind_spots": list(self.blind_spots),
            "duration_ms": self.duration_ms,
            "started_at": self.started_at,
        }

    def to_findings(self) -> list[Finding]:
        """Convert to the runner's Finding type so existing renderers work."""
        out: list[Finding] = []
        for f in self.filtered_leaks:
            out.append(
                Finding(
                    severity=Severity.FAIL,
                    code="cross_tenant_filtered_leak",
                    summary=(
                        f"Tenant {f.querying_tenant} retrieved data owned by "
                        f"{f.owning_tenant} *with the tenant filter applied*."
                    ),
                    path=[f.querying_tenant, f.artifact_id],
                    detail=f.to_dict(),
                )
            )
        for f in self.semantic_leaks:
            out.append(
                Finding(
                    severity=Severity.FAIL,
                    code="cross_tenant_semantic_leak",
                    summary=(
                        f"A natural question derived from {f.owning_tenant}'s own content "
                        f"surfaced that content to tenant {f.querying_tenant}."
                    ),
                    path=[f.querying_tenant, f.artifact_id],
                    detail=f.to_dict(),
                )
            )
        if self.unfiltered_exposure:
            out.append(
                Finding(
                    severity=Severity.WARN,
                    code="unfiltered_blast_radius",
                    summary=(
                        f"{len(self.unfiltered_exposure)} documents across other tenants "
                        "would be reachable by a single query missing its tenant filter. "
                        "Not a live defect — a measure of what one forgotten predicate costs."
                    ),
                    detail={"sample": [f.to_dict() for f in self.unfiltered_exposure[:5]]},
                )
            )
        for b in self.blind_spots:
            out.append(
                Finding(
                    severity=Severity.WARN,
                    code="isolation_blind_spot",
                    summary=b,
                )
            )
        return out


def _excerpt(text: str) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= _EXCERPT_CHARS else text[:_EXCERPT_CHARS] + "…"


def _owner_of(row: dict[str, Any]) -> str | None:
    val = row.get("tenant_id")
    return str(val) if val is not None else None


def _queries_from_documents(rows: Iterable[dict[str, Any]], *, max_queries: int) -> list[str]:
    """Derive natural-looking queries from a tenant's own documents.

    Not clever: take the longest content-bearing span from each document. The
    point is that these are questions a *real* user of another tenant might
    plausibly ask, not adversarial prompts — the research finding is that
    ordinary queries leak, so ordinary queries are what we test with.
    """
    queries: list[str] = []
    for row in rows:
        content = " ".join(str(row.get("content") or "").split())
        if not content:
            continue
        words = content.split()
        if len(words) < 4:
            continue
        # A middle slice avoids boilerplate prefixes like "User acme note #1:".
        start = min(3, max(len(words) // 4, 0))
        span = " ".join(words[start : start + 12])
        if span and span not in queries:
            queries.append(span)
        if len(queries) >= max_queries:
            break
    return queries


def run_isolation_check(
    store: Any,
    *,
    tenants: list[str] | None = None,
    queries: list[str] | None = None,
    limit: int = 10,
    semantic_probe: bool = True,
    max_semantic_queries: int = 5,
    backend: str = "unknown",
) -> IsolationReport:
    """Run the three-probe isolation check against ``store``.

    ``store`` needs ``search(query=..., tenant_id=..., limit=...)`` and
    ideally ``tenants()``, ``search_unfiltered(...)`` and
    ``raw_rows_containing(...)``. Anything missing degrades to a recorded blind
    spot rather than a silent skip.
    """
    t0 = time.time()
    report = IsolationReport(backend=backend)

    # --- who are we checking? ------------------------------------------------
    if tenants is None:
        discover = getattr(store, "tenants", None)
        tenants = list(discover(limit=50)) if callable(discover) else []
        if not tenants:
            report.blind_spots.append(
                "Could not enumerate tenants automatically and none were supplied, "
                "so no cross-tenant comparison was possible. Pass --tenants explicitly."
            )
            report.duration_ms = (time.time() - t0) * 1000.0
            return report
    tenants = [str(t) for t in tenants]
    report.tenants_checked = list(tenants)

    if len(tenants) < 2:
        report.blind_spots.append(
            f"Only one tenant ({tenants[0]}) was found or supplied. Cross-tenant "
            "isolation is undefined with a single tenant — this is not a pass."
        )
        report.duration_ms = (time.time() - t0) * 1000.0
        return report

    base_queries = list(queries or [])

    # --- probe 1: filtered ---------------------------------------------------
    for querying in tenants:
        for q in base_queries:
            rows = _safe_search(store, query=q, tenant_id=querying, limit=limit, report=report)
            report.queries_run += 1
            for row in rows:
                owner = _owner_of(row)
                if owner is not None and owner != querying:
                    report.filtered_leaks.append(
                        IsolationFinding(
                            probe="filtered",
                            querying_tenant=querying,
                            owning_tenant=owner,
                            query=q,
                            artifact_id=str(row.get("id", "")),
                            excerpt=_excerpt(row.get("content", "")),
                            score=row.get("score"),
                        )
                    )

    # --- probe 2: unfiltered blast radius -----------------------------------
    unfiltered = getattr(store, "search_unfiltered", None)
    if callable(unfiltered):
        for q in base_queries or ["*"]:
            try:
                rows = unfiltered(query=q, limit=max(limit * 2, 20))
            except Exception as exc:  # noqa: BLE001
                report.blind_spots.append(f"Unfiltered probe failed for {q!r}: {exc}")
                continue
            report.queries_run += 1
            owners = {t: 0 for t in tenants}
            for row in rows:
                owner = _owner_of(row)
                if owner is None:
                    continue
                owners[owner] = owners.get(owner, 0) + 1
                report.unfiltered_exposure.append(
                    IsolationFinding(
                        probe="unfiltered",
                        querying_tenant="(no filter)",
                        owning_tenant=owner,
                        query=q,
                        artifact_id=str(row.get("id", "")),
                        excerpt=_excerpt(row.get("content", "")),
                        score=row.get("score"),
                    )
                )
    else:
        report.blind_spots.append(
            "This store exposes no unfiltered-query path, so blast radius from a "
            "dropped tenant filter could not be measured."
        )

    # --- probe 3: semantic neighbours ---------------------------------------
    if semantic_probe:
        probed_any = False
        for owner in tenants:
            own_rows = _documents_for(
                store, tenant=owner, limit=max_semantic_queries * 2, report=report
            )
            derived = _queries_from_documents(own_rows, max_queries=max_semantic_queries)
            if not derived:
                continue
            probed_any = True
            for other in tenants:
                if other == owner:
                    continue
                for q in derived:
                    rows = _safe_search(
                        store, query=q, tenant_id=other, limit=limit, report=report
                    )
                    report.queries_run += 1
                    for row in rows:
                        hit_owner = _owner_of(row)
                        if hit_owner is not None and hit_owner == owner:
                            report.semantic_leaks.append(
                                IsolationFinding(
                                    probe="semantic",
                                    querying_tenant=other,
                                    owning_tenant=owner,
                                    query=q,
                                    artifact_id=str(row.get("id", "")),
                                    excerpt=_excerpt(row.get("content", "")),
                                    score=row.get("score"),
                                )
                            )

        if not probed_any:
            report.blind_spots.append(
                "The semantic-neighbour probe could not run: this store exposes no way to "
                "enumerate a tenant's own documents (documents_for_tenant / raw scan). "
                "Similarity-based cross-tenant reach was therefore NOT tested."
            )

    if not base_queries and semantic_probe:
        report.blind_spots.append(
            "No explicit queries were supplied, so probe 1 (filtered) ran zero queries. "
            "Supply --query with real user queries for a stronger result."
        )

    report.duration_ms = (time.time() - t0) * 1000.0
    return report


def _documents_for(
    store: Any, *, tenant: str, limit: int, report: IsolationReport
) -> list[dict[str, Any]]:
    """Enumerate a tenant's own documents, trying the paths a store might offer.

    Ordered cheapest-and-most-explicit first. Every real vector store supports
    at least one of these (scroll, get, SELECT); if none work we return nothing
    and the caller records a blind spot rather than pretending the probe ran.
    """
    lister = getattr(store, "documents_for_tenant", None)
    if callable(lister):
        try:
            return list(lister(tenant, limit=limit))
        except Exception as exc:  # noqa: BLE001
            report.blind_spots.append(
                f"documents_for_tenant({tenant!r}) failed: {type(exc).__name__}: {exc}"
            )

    raw = getattr(store, "raw_rows_containing", None)
    if callable(raw):
        try:
            rows = [r for r in raw("", limit=limit * 10) if _owner_of(r) == tenant]
            if rows:
                return rows[:limit]
        except Exception as exc:  # noqa: BLE001
            report.blind_spots.append(
                f"Raw scan while enumerating {tenant!r} failed: {type(exc).__name__}: {exc}"
            )

    return []


def _safe_search(
    store: Any,
    *,
    query: str,
    tenant_id: str | None,
    limit: int,
    report: IsolationReport,
) -> list[dict[str, Any]]:
    try:
        return list(store.search(query=query, tenant_id=tenant_id, limit=limit))
    except Exception as exc:  # noqa: BLE001 - surfaced honestly, never swallowed
        report.blind_spots.append(
            f"Search failed for tenant={tenant_id!r} query={query!r}: "
            f"{type(exc).__name__}: {exc}"
        )
        return []
