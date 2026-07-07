"""Counterfactual replay — "what would the agent have seen without this memory?"

Attribution (:mod:`ferryte.oracle.attribute`) ranks suspects by evidence that is
*corroborative*: content overlap, retrieval history, recorded answer inputs. The
gold standard for attribution, per ContextCite (Cohen-Wang et al., NeurIPS 2024),
is *contributive*: ablate the source and observe whether the output changes.

Full generation-level ablation needs the app's LLM in the loop (that spend lives
in Cloud). But the retrieval layer — which memories enter the context window —
is deterministic and free to replay, and for memory bugs it is the layer that
matters: if the suspect never enters context, it cannot have caused the answer;
if it does, ablating it shows exactly which memory would have taken its place.

So replay does the ContextCite move at the retrieval layer:

  1. probe the live (instrumented) memory client with the debugged query,
  2. locate the suspect in the returned context,
  3. rebuild the top-k *without* it — the counterfactual context,
  4. name the replacement: the memory that enters (or wins) instead.

The killer output for the stale-belief case: "without ``mem-old``, the top of
context becomes ``mem-new`` — the current fact." That's a confirmed root cause
and a verified fix in one step.

Note: probing goes through the patched client, so replay probes are themselves
recorded in the retrieval trace like any scenario probe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..instrument import Instrumentation, current_instrumentation

# Overfetch beyond the context size so the counterfactual top-k can be filled
# after the suspect is removed.
_OVERFETCH = 4


@dataclass(frozen=True)
class ContextItem:
    """One memory as it appears in the retrieved context."""

    rank: int
    artifact_id: str | None
    content: str
    score: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "artifact_id": self.artifact_id,
            "content": self.content,
            "score": self.score,
        }


@dataclass
class ReplayReport:
    """Outcome of one retrieval-layer counterfactual."""

    query: str
    tenant_id: str | None
    suspect_artifact_id: str
    backend: str | None = None
    # verdicts: "causal"        — suspect is in the live top-k context
    #           "not-retrieved" — suspect does not enter context for this query
    #           "no-clients"    — nothing instrumented to probe
    verdict: str = "no-clients"
    suspect_rank: int | None = None
    suspect_score: float | None = None
    factual: list[ContextItem] = field(default_factory=list)
    counterfactual: list[ContextItem] = field(default_factory=list)
    replacement: ContextItem | None = None

    @property
    def causal(self) -> bool:
        return self.verdict == "causal"

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "tenant_id": self.tenant_id,
            "suspect_artifact_id": self.suspect_artifact_id,
            "backend": self.backend,
            "verdict": self.verdict,
            "causal": self.causal,
            "suspect_rank": self.suspect_rank,
            "suspect_score": self.suspect_score,
            "factual": [c.to_dict() for c in self.factual],
            "counterfactual": [c.to_dict() for c in self.counterfactual],
            "replacement": self.replacement.to_dict() if self.replacement else None,
        }


def replay_query(
    query: str,
    suspect_artifact_id: str,
    *,
    tenant_id: str | None = None,
    limit: int = 5,
    instrumentation: Instrumentation | None = None,
    clients: list[tuple[Any, Any]] | None = None,
) -> ReplayReport:
    """Ablate ``suspect_artifact_id`` from retrieval for ``query`` and diff.

    ``limit``   the context size to reason about (the agent's top-k).
    ``clients`` explicit ``(client, adapter)`` pairs; defaults to every client
                tracked by the active instrumentation.
    """
    report = ReplayReport(
        query=query, tenant_id=tenant_id, suspect_artifact_id=suspect_artifact_id
    )

    pairs: list[tuple[Any, Any, str]] = []
    if clients:
        pairs = [(c, a, getattr(getattr(a, "backend", None), "value", "custom")) for c, a in clients]
    else:
        handle = instrumentation or current_instrumentation()
        if handle is not None:
            pairs = [(tc.client, tc.adapter, tc.backend.value) for tc in handle.list_clients()]
    if not pairs:
        return report

    fallback: tuple[str, list[Any]] | None = None
    for client, adapter, backend in pairs:
        try:
            results = adapter.probe(
                client, query=query, tenant_id=tenant_id, limit=limit + _OVERFETCH
            )
        except Exception:  # noqa: BLE001 — a broken client shouldn't kill the replay
            continue
        results = list(results)
        if any(r.artifact_id == suspect_artifact_id for r in results):
            return _diff(report, backend=backend, results=results, limit=limit)
        if fallback is None:
            fallback = (backend, results)

    if fallback is not None:
        # No client ever surfaces the suspect for this query.
        backend, results = fallback
        report.backend = backend
        report.verdict = "not-retrieved"
        report.factual = _top(results, limit)
        report.counterfactual = report.factual
    return report


def _diff(report: ReplayReport, *, backend: str, results: list[Any], limit: int) -> ReplayReport:
    report.backend = backend
    factual = _top(results, limit)
    without = [r for r in results if r.artifact_id != report.suspect_artifact_id]
    counterfactual = _top(without, limit)

    report.factual = factual
    report.counterfactual = counterfactual

    suspect = next(
        (c for c in factual if c.artifact_id == report.suspect_artifact_id), None
    )
    if suspect is None:
        # Retrieved by the backend, but below the context cut — it does not reach
        # the prompt at this limit.
        report.verdict = "not-retrieved"
        return report

    report.verdict = "causal"
    report.suspect_rank = suspect.rank
    report.suspect_score = suspect.score

    factual_ids = {c.artifact_id for c in factual}
    report.replacement = next(
        (c for c in counterfactual if c.artifact_id not in factual_ids),
        counterfactual[0] if counterfactual and suspect.rank == 1 else None,
    )
    return report


def _top(results: list[Any], limit: int) -> list[ContextItem]:
    return [
        ContextItem(
            rank=i + 1,
            artifact_id=r.artifact_id,
            content=(r.content or ""),
            score=r.score,
        )
        for i, r in enumerate(results[:limit])
    ]
