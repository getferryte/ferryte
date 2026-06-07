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
from ..detect import ResidueCalibrator, Rung, detect_leak, token_embedder
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

    # Detection ladder: a token embedder (no model dependency) powers Rung 3
    # semantic-residue; sibling canary sentences form the null distribution so
    # the boilerplate template doesn't trip a false positive.
    embedder = token_embedder()

    for tc in tracked:
        seeded_total += _seed_for_client(client=tc.client, adapter=tc.adapter, facts=facts)

        for f in facts:
            n = tc.adapter.delete_source(tc.client, source_id=f.source_id, tenant_id=tenant)
            deleted_total += n

        for f in facts:
            # null distribution: sibling secrets + this fact's planted decoy (a
            # topically-adjacent near-miss). Rung 3 must clear the secret over both.
            background = [g.sentence for g in facts if g.source_id != f.source_id]
            if getattr(f, "decoy", ""):
                background.append(f.decoy)
            calibrator = ResidueCalibrator(embedder).calibrate(
                secret_text=f.sentence, background=background
            )
            findings.extend(
                _check_one(tc=tc, fact=f, tenant=tenant, embedder=embedder, calibrator=calibrator)
            )

        _inspect_store(tc=tc, facts=facts, findings=findings)

    sev = Severity.PASS
    if any(fi.severity == Severity.FAIL for fi in findings):
        sev = Severity.FAIL
    elif any(fi.severity == Severity.WARN for fi in findings):
        sev = Severity.WARN

    # J4: worst-case recoverability across every surviving artifact (0 = fully
    # forgotten, 1 = secret fully reconstructable). A graded metric for triage +
    # the dashboard, richer than the binary PASS/FAIL verdict.
    recoverabilities = [
        fi.detail.get("recoverability", 0.0)
        for fi in findings
        if isinstance(fi.detail, dict) and "recoverability" in fi.detail
    ]
    max_recoverability = round(max(recoverabilities), 3) if recoverabilities else 0.0

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
            "max_recoverability": max_recoverability,
        },
        blast=blast,
    )


def _check_one(
    *, tc: Any, fact: Any, tenant: str, embedder: Any = None, calibrator: Any = None
) -> list[Finding]:
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
        verdict = detect_leak(
            r.content or "",
            marker=fact.marker,
            secret_text=fact.sentence,
            embedder=embedder,
            calibrator=calibrator,
        )
        if verdict.clean:
            continue
        kind = r.metadata.get("kind", "raw") if isinstance(r.metadata, dict) else "raw"
        if verdict.blind:
            out.append(
                Finding(
                    severity=Severity.WARN,
                    code="blind_spot",
                    summary=(
                        f"Revoked source '{fact.source_id}' surfaced a retrieval on tenant "
                        f"'{tenant}' that could not be cleared as forget-safe (no semantic "
                        "detector available to rule out paraphrase)."
                    ),
                    path=[tc.backend.value, fact.source_id, r.artifact_id or "?"],
                    detail={"marker": fact.marker, "snippet": (r.content or "")[:240]},
                )
            )
            continue
        # leaked: exact/normalized are deterministic FAILs; semantic residue is a WARN
        is_semantic = verdict.rung == Rung.SEMANTIC
        out.append(
            Finding(
                severity=Severity.WARN if is_semantic else Severity.FAIL,
                code="semantic_residue_in_probe" if is_semantic else "revoked_marker_in_probe",
                summary=(
                    f"Revoked source '{fact.source_id}' still surfaces the secret via retrieval "
                    f"on tenant '{tenant}' (rung={verdict.rung.value if verdict.rung else '?'}, "
                    f"confidence={verdict.confidence:.2f}, artifact kind={kind})."
                ),
                path=[tc.backend.value, fact.source_id, r.artifact_id or "?"],
                detail={
                    "marker": fact.marker,
                    "rung": verdict.rung.value if verdict.rung else None,
                    "confidence": verdict.confidence,
                    "recoverability": verdict.recoverability,
                    "semantic_score": verdict.score,
                    "evidence": verdict.evidence,
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
