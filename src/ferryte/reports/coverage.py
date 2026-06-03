"""Coverage + blind-spot computation.

A coverage report answers two questions a buyer actually asks:

  1. *What did Ferryte verify on this run?* — by backend, by adapter capability,
     by scenario severity, by counts.
  2. *What couldn't Ferryte verify?* — every blind spot the run observed,
     plus the structural blind spots inferred from missing adapter
     capabilities (e.g. an adapter without ``DERIVED_ENUMERATION`` means
     "we can't list what was derived from a source on this backend"). This is
     the honesty-as-product piece from the README.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..adapters.base import AdapterCapability
from ..instrument import Instrumentation
from ..lineage import LineageGraph
from ..oracle.runner import ScenarioResult, Severity


@dataclass
class CoverageReport:
    summary: dict[str, Any] = field(default_factory=dict)
    backends: list[dict[str, Any]] = field(default_factory=list)
    scenarios: list[dict[str, Any]] = field(default_factory=list)
    blindspots: list[dict[str, Any]] = field(default_factory=list)
    structural_gaps: list[dict[str, Any]] = field(default_factory=list)
    lineage_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "backends": self.backends,
            "scenarios": self.scenarios,
            "blindspots": self.blindspots,
            "structural_gaps": self.structural_gaps,
            "lineage_counts": self.lineage_counts,
        }


_CAPABILITY_DESCRIPTIONS: dict[AdapterCapability, str] = {
    AdapterCapability.WRITE_CAPTURE: "Captures writes (otherwise no provenance can be built).",
    AdapterCapability.READ_CAPTURE: "Captures retrievals (otherwise we cannot detect re-entry).",
    AdapterCapability.SOURCE_DELETE: "Can call the backend's source-delete API (otherwise we cannot actuate revocation).",
    AdapterCapability.TENANT_SCOPING: "Honors tenant scoping (otherwise cross-tenant tests give false confidence).",
    AdapterCapability.DERIVED_ENUMERATION: "Can enumerate derived artifacts (otherwise blast radius is incomplete).",
}


def build_coverage_report(
    *,
    instrumentation: Instrumentation,
    lineage: LineageGraph,
    results: list[ScenarioResult],
) -> CoverageReport:
    counts = lineage.counts()
    backends_seen: dict[str, dict[str, Any]] = {}
    structural_gaps: list[dict[str, Any]] = []

    for tc in instrumentation.list_clients():
        bid = tc.backend.value
        entry = backends_seen.setdefault(
            bid,
            {
                "backend": bid,
                "adapter": tc.adapter.name,
                "client_count": 0,
                "capabilities": sorted(c.value for c in tc.adapter.capabilities),
            },
        )
        entry["client_count"] += 1
        for cap, desc in _CAPABILITY_DESCRIPTIONS.items():
            if cap not in tc.adapter.capabilities:
                structural_gaps.append(
                    {
                        "backend": bid,
                        "capability": cap.value,
                        "detail": desc,
                    }
                )

    fail = sum(1 for r in results if r.severity == Severity.FAIL)
    warn = sum(1 for r in results if r.severity == Severity.WARN)
    ok = sum(1 for r in results if r.severity == Severity.PASS)
    scenarios = [r.to_dict() for r in results]

    blindspots = lineage.blindspots()

    summary = {
        "scenarios_run": len(results),
        "passed": ok,
        "warned": warn,
        "failed": fail,
        "blindspot_observations": len(blindspots),
        "structural_gaps": len(structural_gaps),
        "backends_instrumented": sorted(backends_seen.keys()),
    }

    return CoverageReport(
        summary=summary,
        backends=list(backends_seen.values()),
        scenarios=scenarios,
        blindspots=blindspots,
        structural_gaps=structural_gaps,
        lineage_counts=counts,
    )
