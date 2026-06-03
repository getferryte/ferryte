"""Stale-fact scenario.

Hypothesis: a fact whose validity window has expired (e.g. account-status,
permission, role) should not be returned as a current fact. We seed an "old"
fact with a validity hint, then a fresh contradicting fact, then probe and
fail if the old marker still appears as current.

This is intentionally a weaker assertion than source-revocation (no formal
``valid_until`` is standard across backends); we expose two failure modes:

  - FAIL: the stale marker is returned with a higher score than the fresh one
  - WARN: both markers come back equally (the agent has no way to disambiguate)
"""

from __future__ import annotations

from ..canary import generate_canary_facts
from ..runner import (
    Finding,
    ScenarioContext,
    ScenarioResult,
    Severity,
    _blast_for,
    _seed_for_client,
    register_scenario,
)


@register_scenario("stale-fact")
def run(ctx: ScenarioContext) -> ScenarioResult:
    tenant = ctx.options.get("tenant_id", "design-partner")
    stale = generate_canary_facts(scenario="stale-old", tenant_id=tenant, count=1)[0]
    fresh = generate_canary_facts(scenario="stale-new", tenant_id=tenant, count=1)[0]

    findings: list[Finding] = []
    seeded_total = 0
    tracked = ctx.tracked_clients()
    if not tracked:
        return ScenarioResult(
            scenario="stale-fact",
            severity=Severity.WARN,
            findings=[
                Finding(
                    severity=Severity.WARN,
                    code="no_clients",
                    summary="No instrumented memory clients detected.",
                )
            ],
            coverage={"clients": 0},
        )

    for tc in tracked:
        seeded_total += _seed_for_client(client=tc.client, adapter=tc.adapter, facts=[stale])
        seeded_total += _seed_for_client(client=tc.client, adapter=tc.adapter, facts=[fresh])

        try:
            results = tc.adapter.probe(
                tc.client,
                query=f"What is the current secret code for {tenant}?",
                tenant_id=tenant,
                limit=10,
            )
        except Exception as exc:  # noqa: BLE001
            findings.append(
                Finding(
                    severity=Severity.WARN,
                    code="probe_failed",
                    summary=f"Stale-fact probe raised {type(exc).__name__}: {exc}",
                    path=[tc.backend.value],
                )
            )
            continue

        stale_hits = [r for r in results if stale.marker in (r.content or "")]
        fresh_hits = [r for r in results if fresh.marker in (r.content or "")]

        if stale_hits and not fresh_hits:
            findings.append(
                Finding(
                    severity=Severity.FAIL,
                    code="stale_only",
                    summary=(
                        f"Stale marker '{stale.marker}' returned with no fresh marker; "
                        f"backend has no temporal disambiguation for this query."
                    ),
                    path=[tc.backend.value, tenant],
                    detail={"snippets": [(r.content or "")[:120] for r in stale_hits]},
                )
            )
        elif stale_hits and fresh_hits:
            top_score_stale = max((r.score or 0.0) for r in stale_hits)
            top_score_fresh = max((r.score or 0.0) for r in fresh_hits)
            if top_score_stale > top_score_fresh:
                findings.append(
                    Finding(
                        severity=Severity.FAIL,
                        code="stale_outranks_fresh",
                        summary=(
                            f"Stale marker '{stale.marker}' outranks fresh marker '{fresh.marker}' "
                            f"({top_score_stale:.3f} > {top_score_fresh:.3f})."
                        ),
                        path=[tc.backend.value, tenant],
                        detail={
                            "stale_score": top_score_stale,
                            "fresh_score": top_score_fresh,
                        },
                    )
                )
            else:
                findings.append(
                    Finding(
                        severity=Severity.WARN,
                        code="stale_and_fresh_both_returned",
                        summary=(
                            "Both stale and fresh markers were returned; agent has no native way "
                            "to pick the current fact."
                        ),
                        path=[tc.backend.value, tenant],
                    )
                )

    sev = Severity.PASS
    if any(fi.severity == Severity.FAIL for fi in findings):
        sev = Severity.FAIL
    elif any(fi.severity == Severity.WARN for fi in findings):
        sev = Severity.WARN

    blast = _blast_for([stale.source_id, fresh.source_id], ctx.lineage)
    return ScenarioResult(
        scenario="stale-fact",
        severity=sev,
        findings=findings,
        artifacts_seeded=seeded_total,
        coverage={
            "clients": len(tracked),
            "backends": sorted({tc.backend.value for tc in tracked}),
            "tenant": tenant,
        },
        blast=blast,
    )
