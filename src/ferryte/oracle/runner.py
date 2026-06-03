"""Scenario runner: the engine that the CLI and tests drive.

A scenario is a pure function that receives a ``ScenarioContext`` and returns
a ``ScenarioResult``. Scenarios self-register; the CLI discovers them through
``ScenarioRegistry``.
"""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from ..context import tag
from ..instrument import Instrumentation, TrackedClient
from ..lineage import LineageGraph, compute_blast_radius, get_lineage


class Severity(str, enum.Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class Finding:
    """One concrete leak or blind spot the oracle discovered."""

    severity: Severity
    code: str
    summary: str
    path: list[str] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "summary": self.summary,
            "path": list(self.path),
            "detail": self.detail,
        }


@dataclass
class ScenarioResult:
    scenario: str
    severity: Severity
    findings: list[Finding] = field(default_factory=list)
    artifacts_seeded: int = 0
    artifacts_deleted: int = 0
    duration_ms: float = 0.0
    coverage: dict[str, Any] = field(default_factory=dict)
    blast: list[dict[str, Any]] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.severity == Severity.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "severity": self.severity.value,
            "passed": self.passed,
            "artifacts_seeded": self.artifacts_seeded,
            "artifacts_deleted": self.artifacts_deleted,
            "duration_ms": self.duration_ms,
            "coverage": self.coverage,
            "findings": [f.to_dict() for f in self.findings],
            "blast": self.blast,
        }


@dataclass
class ScenarioContext:
    instrumentation: Instrumentation
    lineage: LineageGraph
    started_at: float
    options: dict[str, Any] = field(default_factory=dict)

    def tracked_clients(self) -> list[TrackedClient]:
        return self.instrumentation.list_clients()

    def seeded_at(self) -> float:
        return self.started_at


ScenarioFn = Callable[[ScenarioContext], ScenarioResult]


class ScenarioRegistry:
    _entries: dict[str, ScenarioFn] = {}

    @classmethod
    def register(cls, name: str, fn: ScenarioFn) -> None:
        cls._entries[name] = fn

    @classmethod
    def get(cls, name: str) -> ScenarioFn | None:
        return cls._entries.get(name)

    @classmethod
    def names(cls) -> list[str]:
        return sorted(cls._entries.keys())


def register_scenario(name: str) -> Callable[[ScenarioFn], ScenarioFn]:
    def decorator(fn: ScenarioFn) -> ScenarioFn:
        ScenarioRegistry.register(name, fn)
        return fn

    return decorator


def run_scenarios(
    *,
    instrumentation: Instrumentation,
    names: list[str] | None = None,
    options: dict[str, Any] | None = None,
) -> list[ScenarioResult]:
    # Trigger scenario imports so the registry is populated.
    from . import scenarios as _scenarios  # noqa: F401

    if names is None or names == ["all"]:
        names = ScenarioRegistry.names()

    lineage = get_lineage()
    results: list[ScenarioResult] = []
    for name in names:
        fn = ScenarioRegistry.get(name)
        if fn is None:
            results.append(
                ScenarioResult(
                    scenario=name,
                    severity=Severity.WARN,
                    findings=[
                        Finding(
                            severity=Severity.WARN,
                            code="unknown_scenario",
                            summary=f"No scenario named '{name}' is registered.",
                        )
                    ],
                )
            )
            continue
        ctx = ScenarioContext(
            instrumentation=instrumentation,
            lineage=lineage,
            started_at=time.time(),
            options=dict(options or {}),
        )
        t0 = time.time()
        try:
            result = fn(ctx)
        except Exception as exc:  # noqa: BLE001 - surfaced as a finding
            result = ScenarioResult(
                scenario=name,
                severity=Severity.FAIL,
                findings=[
                    Finding(
                        severity=Severity.FAIL,
                        code="scenario_error",
                        summary=f"Scenario raised {type(exc).__name__}: {exc}",
                    )
                ],
            )
        result.duration_ms = (time.time() - t0) * 1000.0
        results.append(result)
    return results


def _seed_for_client(
    *,
    client: Any,
    adapter: Any,
    facts: list[Any],
    use_tag_context: bool = True,
) -> int:
    """Seed canary facts into an instrumented client.

    Returns the count actually accepted.
    """
    count = 0
    for f in facts:
        if use_tag_context:
            with tag(source_id=f.source_id, tenant_id=f.tenant_id):
                _client_add(client, content=f.sentence, tenant_id=f.tenant_id)
        else:
            _client_add(
                client,
                content=f.sentence,
                tenant_id=f.tenant_id,
                source_id=f.source_id,
            )
        count += 1
    return count


def _client_add(client: Any, *, content: str, tenant_id: str, source_id: str | None = None) -> None:
    """Call ``client.add`` with whichever signature the backend supports."""
    if hasattr(client, "add"):
        try:
            client.add(content=content, tenant_id=tenant_id, source_id=source_id)
            return
        except TypeError:
            pass
        try:
            client.add(messages=[{"role": "user", "content": content}], user_id=tenant_id)
            return
        except TypeError:
            pass
        try:
            client.add(content)
            return
        except TypeError:
            pass


def _blast_for(source_ids: list[str], lineage: LineageGraph) -> list[dict[str, Any]]:
    return [compute_blast_radius(lineage, source_id=sid).to_dict() for sid in source_ids]
