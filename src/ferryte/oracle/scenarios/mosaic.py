"""Mosaic / triangulation scenario (J1).

Hypothesis: a secret can be **fragmented** across several memories such that no
single artifact contains the whole thing — so a naive per-artifact leak check
clears each one — yet the fragments, taken together, **reassemble** the secret.
After revoking the sources, if every fragment still survives somewhere (e.g. in
a concatenating summary, or scattered derived artifacts), an attacker or the
agent can triangulate the secret back. Nobody else tests this recombination.

  baseline (no cascade)  → fragments survive in the summary → reassemblable → FAIL
  with Ferryte (cascade) → lineage deletes the derived artifacts → PASS
"""

from __future__ import annotations

import hashlib
from typing import Any

from ...context import tag
from ..canary import make_entity
from ..detect import detect_mosaic
from ..runner import (
    Finding,
    ScenarioContext,
    ScenarioResult,
    Severity,
    _blast_for,
    _client_add,
    register_scenario,
)


def _secret(seed: str, idx: int) -> str:
    return hashlib.sha256(f"mosaic:{seed}:{idx}".encode()).hexdigest()[:12].upper()


def _fragments(secret: str, k: int = 3) -> list[str]:
    """Split into k chunks; no single chunk is the whole secret."""
    n = max(1, -(-len(secret) // k))  # ceil
    chunks = [secret[i : i + n] for i in range(0, len(secret), n)]
    if len(chunks) > k:  # fold any remainder into the last chunk
        chunks[k - 1 :] = ["".join(chunks[k - 1 :])]
    return chunks


@register_scenario("mosaic")
def run(ctx: ScenarioContext) -> ScenarioResult:
    tenant = ctx.options.get("tenant_id", "design-partner")
    count = int(ctx.options.get("count", 1))

    findings: list[Finding] = []
    seeded = 0
    source_ids: list[str] = []
    tracked = ctx.tracked_clients()
    if not tracked:
        return ScenarioResult(
            scenario="mosaic",
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

    deleted = 0
    for tc in tracked:
        for idx in range(count):
            secret = _secret(f"{tenant}:{tc.backend.value}", idx)
            entity = make_entity("mosaic", tenant, idx)
            frags = _fragments(secret, 3)
            frag_sids: list[str] = []
            for j, frag in enumerate(frags):
                sid = f"ferryte-mosaic-{tenant}-{idx}-{j}"
                frag_sids.append(sid)
                source_ids.append(sid)
                sentence = (
                    f"{entity} configuration segment {j + 1} of {len(frags)}: {frag}. "
                    f"(Tenant {tenant}, do not share.)"
                )
                with tag(source_id=sid, tenant_id=tenant):
                    _client_add(tc.client, content=sentence, tenant_id=tenant)
                seeded += 1

            # revoke every fragment's source
            for sid in frag_sids:
                deleted += tc.adapter.delete_source(tc.client, source_id=sid, tenant_id=tenant)

            findings.extend(
                _check_reassembly(
                    tc=tc, tenant=tenant, entity=entity, secret=secret, frags=frags
                )
            )

    sev = Severity.PASS
    if any(fi.severity == Severity.FAIL for fi in findings):
        sev = Severity.FAIL
    elif any(fi.severity == Severity.WARN for fi in findings):
        sev = Severity.WARN

    return ScenarioResult(
        scenario="mosaic",
        severity=sev,
        findings=findings,
        artifacts_seeded=seeded,
        artifacts_deleted=deleted,
        coverage={
            "clients": len(tracked),
            "backends": sorted({tc.backend.value for tc in tracked}),
            "tenant": tenant,
            "secrets": count,
            "fragments_per_secret": 3,
        },
        blast=_blast_for(source_ids, ctx.lineage),
    )


def _check_reassembly(
    *, tc: Any, tenant: str, entity: str, secret: str, frags: list[str]
) -> list[Finding]:
    try:
        results = tc.adapter.probe(
            tc.client, query=f"{entity} configuration segments", tenant_id=tenant, limit=20
        )
    except Exception as exc:  # noqa: BLE001
        return [
            Finding(
                severity=Severity.WARN,
                code="probe_failed",
                summary=f"Mosaic probe raised {type(exc).__name__}: {exc}",
                path=[tc.backend.value, tenant],
            )
        ]

    artifacts = [(r.content or "") for r in results]
    verdict = detect_mosaic(artifacts, fragments=frags, secret=secret)
    if not verdict.reassemblable:
        return []  # fragments did not all survive — secret cannot be triangulated

    kind = "mosaic_reassembly" if verdict.mosaic_only else "reassembly_via_single_artifact"
    note = (
        "no single surviving artifact held the whole secret, but its fragments did — "
        "a per-artifact leak check would have passed"
        if verdict.mosaic_only
        else "the secret was reassemblable (a surviving artifact concatenated the fragments)"
    )
    return [
        Finding(
            severity=Severity.FAIL,
            code=kind,
            summary=(
                f"After revoking all sources, secret for '{entity}' is still reassemblable on "
                f"tenant '{tenant}' ({verdict.fragments_present}/{verdict.fragments_total} "
                f"fragments survive). {note}."
            ),
            path=[tc.backend.value, tenant, entity],
            detail={
                "secret": secret,
                "fragments_present": verdict.fragments_present,
                "fragments_total": verdict.fragments_total,
                "mosaic_only": verdict.mosaic_only,
                "single_full": verdict.single_full,
            },
        )
    ]
