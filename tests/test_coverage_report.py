from pathlib import Path

import ferryte
from ferryte.adapters.vector import InMemoryVectorStore
from ferryte.instrument import current_instrumentation
from ferryte.lineage import get_lineage
from ferryte.oracle.runner import run_scenarios
from ferryte.reports import build_coverage_report, write_html_report, write_json_report


def test_build_and_write_report(fresh_ferryte: Path) -> None:
    ferryte.instrument()
    InMemoryVectorStore()
    handle = current_instrumentation()
    assert handle is not None
    results = run_scenarios(instrumentation=handle, names=["source-revocation"])
    report = build_coverage_report(
        instrumentation=handle, lineage=get_lineage(), results=results
    )
    assert report.summary["scenarios_run"] == 1
    out = fresh_ferryte / "reports"
    write_json_report(path=out / "latest.json", report=report, results=results)
    write_html_report(path=out / "latest.html", report=report, results=results)
    assert (out / "latest.json").exists()
    assert (out / "latest.html").exists()
    text = (out / "latest.html").read_text()
    assert "Ferryte — verification report" in text
