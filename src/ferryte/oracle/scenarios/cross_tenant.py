"""Cross-tenant isolation scenario.

Hypothesis: data written under tenant A's namespace must never surface to
tenant B's agent, even when B asks a question whose embedding is very similar.

We seed two tenants with disjoint canary markers, then probe each tenant for
the *other* tenant's marker and fail if it appears.
"""

from __future__ import annotations

from typing import Any

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


@register_scenario("cross-tenant-isolation")
def run(ctx: ScenarioContext) -> ScenarioResult:
    tenant_a = ctx.options.get("tenant_a", "tenant-A")
    tenant_b = ctx.options.get("tenant_b", "tenant-B")
    count = int(ctx.options.get("count", 2))

    facts_a = generate_canary_facts(
        scenario="cross-tenant-A", tenant_id=tenant_a, count=count
    )
    facts_b = generate_canary_facts(
        scenario="cross-tenant-B", tenant_id=tenant_b, count=count
    )

    findings: list[Finding] = []
    seeded_total = 0
    tracked = ctx.tracked_clients()
    if not tracked:
        findings.append(
            Finding(
                severity=Severity.WARN,
                code="no_clients",
                summary="No instrumented memory clients detected.",
            )
        )
        return ScenarioResult(
            scenario="cross-tenant-isolation",
            severity=Severity.WARN,
            findings=findings,
            coverage={"clients": 0},
        )

    for tc in tracked:
        seeded_total += _seed_for_client(client=tc.client, adapter=tc.adapter, facts=facts_a)
        seeded_total += _seed_for_client(client=tc.client, adapter=tc.adapter, facts=facts_b)

        findings.extend(
            _check_cross(tc=tc, victim_tenant=tenant_a, attacker_tenant=tenant_b, victim_facts=facts_a)
        )
        findings.extend(
            _check_cross(tc=tc, victim_tenant=tenant_b, attacker_tenant=tenant_a, victim_facts=facts_b)
        )

    sev = Severity.PASS
    if any(fi.severity == Severity.FAIL for fi in findings):
        sev = Severity.FAIL
    elif any(fi.severity == Severity.WARN for fi in findings):
        sev = Severity.WARN

    blast = _blast_for(
        [f.source_id for f in facts_a] + [f.source_id for f in facts_b], ctx.lineage
    )
    return ScenarioResult(
        scenario="cross-tenant-isolation",
        severity=sev,
        findings=findings,
        artifacts_seeded=seeded_total,
        coverage={
            "clients": len(tracked),
            "backends": sorted({tc.backend.value for tc in tracked}),
            "tenants": [tenant_a, tenant_b],
            "canary_count": len(facts_a) + len(facts_b),
        },
        blast=blast,
    )


def _check_cross(
    *, tc: Any, victim_tenant: str, attacker_tenant: str, victim_facts: list[Any]
) -> list[Finding]:
    out: list[Finding] = []
    for f in victim_facts:
        try:
            results = tc.adapter.probe(
                tc.client,
                query=f"What was the secret code I told you ({attacker_tenant})?",
                tenant_id=attacker_tenant,
                limit=10,
            )
        except Exception as exc:  # noqa: BLE001
            out.append(
                Finding(
                    severity=Severity.WARN,
                    code="probe_failed",
                    summary=f"Cross-tenant probe raised {type(exc).__name__}: {exc}",
                    path=[tc.backend.value, attacker_tenant],
                )
            )
            continue
        for r in results:
            if f.marker in (r.content or ""):
                out.append(
                    Finding(
                        severity=Severity.FAIL,
                        code="cross_tenant_leak",
                        summary=(
                            f"Tenant '{attacker_tenant}' retrieved tenant '{victim_tenant}' marker "
                            f"'{f.marker}' (artifact {r.artifact_id})."
                        ),
                        path=[tc.backend.value, attacker_tenant, victim_tenant, r.artifact_id or "?"],
                        detail={
                            "marker": f.marker,
                            "victim_source": f.source_id,
                            "victim_tenant": victim_tenant,
                            "attacker_tenant": attacker_tenant,
                            "artifact_id": r.artifact_id,
                            "score": r.score,
                            "snippet": (r.content or "")[:240],
                        },
                    )
                )
    return out
