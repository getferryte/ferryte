"""Source-revocation scenario — the flagship.

Hypothesis: when a source is deleted through the backend's own API, every
derived artifact (raw record, summary, embedding, fact) it influenced should
become un-retrievable. We test both layers:

  1. Probe layer: replay the original probe query and check the agent's
     retrieval results never contain the canary marker.
  2. Store-inspection layer: read directly from the backend and look for the
     marker substring among undeleted artifacts — this catches the "the model
     answered ok but the data is still sitting there" false-confidence trap.
"""

from __future__ import annotations

import time
from typing import Any

from ...adapters.base import BackendKind
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


@register_scenario("source-revocation")
def run(ctx: ScenarioContext) -> ScenarioResult:
    tenant = ctx.options.get("tenant_id", "design-partner")
    count = int(ctx.options.get("count", 3))
    facts = generate_canary_facts(scenario="source-revocation", tenant_id=tenant, count=count)
    seeded_at = time.time()

    seeded_total = 0
    deleted_total = 0
    findings: list[Finding] = []

    tracked = ctx.tracked_clients()
    if not tracked:
        findings.append(
            Finding(
                severity=Severity.WARN,
                code="no_clients",
                summary=(
                    "No instrumented memory clients detected. "
                    "Call ferryte.instrument() before constructing your memory backend."
                ),
            )
        )
        return ScenarioResult(
            scenario="source-revocation",
            severity=Severity.WARN,
            findings=findings,
            coverage={"clients": 0},
        )

    for tc in tracked:
        seeded_total += _seed_for_client(client=tc.client, adapter=tc.adapter, facts=facts)

        for f in facts:
            n = tc.adapter.delete_source(tc.client, source_id=f.source_id, tenant_id=tenant)
            deleted_total += n

        for f in facts:
            findings.extend(_check_one(tc=tc, fact=f, tenant=tenant))

        _inspect_store(tc=tc, facts=facts, findings=findings)

    sev = Severity.PASS
    if any(fi.severity == Severity.FAIL for fi in findings):
        sev = Severity.FAIL
    elif any(fi.severity == Severity.WARN for fi in findings):
        sev = Severity.WARN

    blast = _blast_for([f.source_id for f in facts], ctx.lineage)
    return ScenarioResult(
        scenario="source-revocation",
        severity=sev,
        findings=findings,
        artifacts_seeded=seeded_total,
        artifacts_deleted=deleted_total,
        coverage={
            "clients": len(tracked),
            "backends": sorted({tc.backend.value for tc in tracked}),
            "tenant": tenant,
            "canary_count": len(facts),
            "seeded_at": seeded_at,
        },
        blast=blast,
    )


def _check_one(*, tc: Any, fact: Any, tenant: str) -> list[Finding]:
    out: list[Finding] = []
    try:
        results = tc.adapter.probe(tc.client, query=fact.probe, tenant_id=tenant, limit=10)
    except Exception as exc:  # noqa: BLE001
        out.append(
            Finding(
                severity=Severity.WARN,
                code="probe_failed",
                summary=f"Probe raised {type(exc).__name__}: {exc}",
                path=[tc.backend.value, fact.source_id],
            )
        )
        return out

    for r in results:
        if any(sub in (r.content or "") for sub in fact.forbidden_substrings):
            kind = r.metadata.get("kind", "raw") if isinstance(r.metadata, dict) else "raw"
            out.append(
                Finding(
                    severity=Severity.FAIL,
                    code="revoked_marker_in_probe",
                    summary=(
                        f"Revoked source '{fact.source_id}' still surfaces marker '{fact.marker}' "
                        f"via retrieval on tenant '{tenant}' (artifact kind={kind})."
                    ),
                    path=[tc.backend.value, fact.source_id, r.artifact_id or "?"],
                    detail={
                        "marker": fact.marker,
                        "artifact_id": r.artifact_id,
                        "score": r.score,
                        "snippet": (r.content or "")[:240],
                        "artifact_kind": kind,
                    },
                )
            )
    return out


def _inspect_store(*, tc: Any, facts: list[Any], findings: list[Finding]) -> None:
    if tc.backend != BackendKind.VECTOR:
        return
    client = tc.client
    if not hasattr(client, "raw_items_containing"):
        return
    for f in facts:
        live = [it for it in client.raw_items_containing(f.marker) if not it.deleted]
        for it in live:
            kind = it.metadata.get("kind", "raw")
            sev = Severity.FAIL if kind == "raw" else Severity.WARN
            code = "marker_in_undeleted_artifact" if kind == "raw" else "marker_in_derived_artifact"
            findings.append(
                Finding(
                    severity=sev,
                    code=code,
                    summary=(
                        f"After delete, marker '{f.marker}' is still present in a {kind} "
                        f"artifact ({it.artifact_id}) in store ({tc.backend.value})."
                    ),
                    path=[tc.backend.value, f.source_id, it.artifact_id],
                    detail={
                        "marker": f.marker,
                        "artifact_id": it.artifact_id,
                        "artifact_kind": kind,
                        "snippet": it.content[:240],
                        "absorbed_sources": it.metadata.get("absorbed_sources", []),
                    },
                )
            )
