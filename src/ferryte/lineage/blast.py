"""Compute the revocation blast radius.

When a source is revoked, the blast radius is every derived artifact, the
retrievals those artifacts have participated in, and a confidence score
reflecting whether the lineage was captured deterministically (1.0) or
inferred (e.g. via content-substring fallback when the backend lost the id).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .graph import LineageGraph


@dataclass
class BlastRadius:
    source_id: str
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    retrievals: list[dict[str, Any]] = field(default_factory=list)
    blindspots: list[dict[str, Any]] = field(default_factory=list)
    # J2: actions that already consumed artifacts derived from this source.
    # These are *propagated* consequences — deletion cannot undo them.
    propagated_actions: list[dict[str, Any]] = field(default_factory=list)

    @property
    def artifact_count(self) -> int:
        return len(self.artifacts)

    @property
    def retrieval_count(self) -> int:
        return len(self.retrievals)

    @property
    def propagated_count(self) -> int:
        return len(self.propagated_actions)

    @property
    def propagated(self) -> bool:
        """True if the secret already drove an action — a leak deletion can't reverse."""
        return bool(self.propagated_actions)

    @property
    def min_confidence(self) -> float:
        if not self.artifacts:
            return 1.0
        return min(float(a.get("confidence", 1.0)) for a in self.artifacts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "artifact_count": self.artifact_count,
            "retrieval_count": self.retrieval_count,
            "propagated_count": self.propagated_count,
            "propagated": self.propagated,
            "min_confidence": self.min_confidence,
            "artifacts": self.artifacts,
            "retrievals": self.retrievals,
            "blindspots": self.blindspots,
            "propagated_actions": self.propagated_actions,
        }


def compute_blast_radius(
    lineage: LineageGraph,
    *,
    source_id: str,
    since: float | None = None,
) -> BlastRadius:
    artifacts = lineage.artifacts_for_source(source_id)
    retrievals: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for art in artifacts:
        for r in lineage.retrievals_for_artifact(art["artifact_id"], since=since):
            if r["id"] in seen_ids:
                continue
            seen_ids.add(r["id"])
            retrievals.append(r)
    return BlastRadius(
        source_id=source_id,
        artifacts=artifacts,
        retrievals=retrievals,
        blindspots=lineage.blindspots(),
        propagated_actions=lineage.actions_consuming_source(source_id),
    )
