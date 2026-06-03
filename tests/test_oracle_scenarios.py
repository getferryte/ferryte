from pathlib import Path

import ferryte
from ferryte.adapters.vector import InMemoryVectorStore
from ferryte.instrument import current_instrumentation
from ferryte.oracle.runner import Severity, run_scenarios


def test_source_revocation_fails_on_leaky_store(fresh_ferryte: Path) -> None:
    ferryte.instrument()
    InMemoryVectorStore(leak_summaries=True)
    handle = current_instrumentation()
    assert handle is not None
    results = run_scenarios(instrumentation=handle, names=["source-revocation"])
    assert len(results) == 1
    r = results[0]
    assert r.artifacts_seeded > 0
    assert r.artifacts_deleted > 0
    assert r.severity in {Severity.FAIL, Severity.WARN}
    assert any(f.code in {"marker_in_derived_artifact", "revoked_marker_in_probe"} for f in r.findings)


def test_source_revocation_passes_on_clean_store(fresh_ferryte: Path) -> None:
    ferryte.instrument()
    InMemoryVectorStore(leak_summaries=False)
    handle = current_instrumentation()
    results = run_scenarios(instrumentation=handle, names=["source-revocation"])
    r = results[0]
    assert r.severity in {Severity.PASS, Severity.WARN}
    assert not any(f.code == "marker_in_undeleted_artifact" for f in r.findings)


def test_cross_tenant_isolation(fresh_ferryte: Path) -> None:
    ferryte.instrument()
    InMemoryVectorStore()
    handle = current_instrumentation()
    results = run_scenarios(instrumentation=handle, names=["cross-tenant-isolation"])
    assert len(results) == 1
    assert results[0].artifacts_seeded > 0


def test_memory_poisoning_detects_planted_payload(fresh_ferryte: Path) -> None:
    ferryte.instrument()
    InMemoryVectorStore()
    handle = current_instrumentation()
    results = run_scenarios(instrumentation=handle, names=["memory-poisoning"])
    r = results[0]
    assert r.severity == Severity.FAIL
    assert any(f.code == "poison_retrieved" for f in r.findings)


def test_run_all_scenarios(fresh_ferryte: Path) -> None:
    ferryte.instrument()
    InMemoryVectorStore()
    handle = current_instrumentation()
    results = run_scenarios(instrumentation=handle, names=["all"])
    names = {r.scenario for r in results}
    assert {"source-revocation", "cross-tenant-isolation", "stale-fact", "memory-poisoning"} <= names
