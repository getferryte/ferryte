"""Render reports for humans (rich tables) and machines (JSON, HTML)."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..oracle.runner import ScenarioResult, Severity
from .coverage import CoverageReport

_SEV_STYLE = {
    Severity.PASS: ("PASS", "green"),
    Severity.WARN: ("WARN", "yellow"),
    Severity.FAIL: ("FAIL", "red"),
}


def render_results_table(results: list[ScenarioResult], console: Console) -> None:
    table = Table(title="Ferryte — scenario results", expand=True)
    table.add_column("Scenario", style="bold")
    table.add_column("Severity")
    table.add_column("Seeded", justify="right")
    table.add_column("Deleted", justify="right")
    table.add_column("Findings", justify="right")
    table.add_column("Duration", justify="right")

    for r in results:
        label, style = _SEV_STYLE[r.severity]
        table.add_row(
            r.scenario,
            f"[{style}]{label}[/{style}]",
            str(r.artifacts_seeded),
            str(r.artifacts_deleted),
            str(len(r.findings)),
            f"{r.duration_ms:.0f} ms",
        )
    console.print(table)

    for r in results:
        if not r.findings:
            continue
        label, style = _SEV_STYLE[r.severity]
        body = Table.grid(padding=(0, 1))
        body.add_column(style="bold")
        body.add_column()
        for fi in r.findings:
            f_label, f_style = _SEV_STYLE[fi.severity]
            body.add_row(
                f"[{f_style}]{f_label}[/{f_style}] {fi.code}",
                fi.summary,
            )
        console.print(
            Panel.fit(
                body,
                title=f"[{style}]{r.scenario}[/{style}]",
                border_style=style,
            )
        )


def render_coverage_table(report: CoverageReport, console: Console) -> None:
    s = report.summary
    table = Table(title="Ferryte — coverage", expand=True)
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    table.add_row("Scenarios run", str(s.get("scenarios_run", 0)))
    table.add_row("Passed", f"[green]{s.get('passed', 0)}[/green]")
    table.add_row("Warned", f"[yellow]{s.get('warned', 0)}[/yellow]")
    table.add_row("Failed", f"[red]{s.get('failed', 0)}[/red]")
    table.add_row("Backends instrumented", ", ".join(s.get("backends_instrumented", [])) or "—")
    table.add_row("Blind-spot observations", str(s.get("blindspot_observations", 0)))
    table.add_row("Structural capability gaps", str(s.get("structural_gaps", 0)))
    counts = report.lineage_counts
    table.add_row("Lineage: sources", str(counts.get("sources", 0)))
    table.add_row("Lineage: artifacts", str(counts.get("artifacts", 0)))
    table.add_row("Lineage: derivations", str(counts.get("derivations", 0)))
    table.add_row("Lineage: retrievals", str(counts.get("retrievals", 0)))
    console.print(table)

    if report.backends:
        bk = Table(title="Backends", expand=True)
        bk.add_column("Backend")
        bk.add_column("Adapter")
        bk.add_column("Clients", justify="right")
        bk.add_column("Capabilities")
        for b in report.backends:
            bk.add_row(
                b["backend"],
                b["adapter"],
                str(b["client_count"]),
                ", ".join(b["capabilities"]),
            )
        console.print(bk)


def render_blindspots_table(report: CoverageReport, console: Console) -> None:
    if not report.blindspots and not report.structural_gaps:
        console.print("[green]No blind spots observed. (Run more scenarios to be sure.)[/green]")
        return
    if report.blindspots:
        bs = Table(title="Observed blind spots", expand=True)
        bs.add_column("Backend")
        bs.add_column("Kind")
        bs.add_column("Detail")
        for b in report.blindspots:
            bs.add_row(b["backend"], b["kind"], b["detail"])
        console.print(bs)
    if report.structural_gaps:
        sg = Table(title="Structural capability gaps", expand=True)
        sg.add_column("Backend")
        sg.add_column("Missing capability")
        sg.add_column("Why it matters")
        for g in report.structural_gaps:
            sg.add_row(g["backend"], g["capability"], g["detail"])
        console.print(sg)


def write_json_report(
    *,
    path: Path,
    report: CoverageReport,
    results: list[ScenarioResult],
) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "coverage": report.to_dict(),
        "results": [r.to_dict() for r in results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_html_report(
    *,
    path: Path,
    report: CoverageReport,
    results: list[ScenarioResult],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[str] = []
    for r in results:
        label, color = _SEV_STYLE[r.severity]
        rows.append(
            f"<tr><td><b>{html.escape(r.scenario)}</b></td>"
            f"<td style='color:{color};font-weight:600'>{label}</td>"
            f"<td>{r.artifacts_seeded}</td><td>{r.artifacts_deleted}</td>"
            f"<td>{len(r.findings)}</td><td>{r.duration_ms:.0f} ms</td></tr>"
        )

    findings_html: list[str] = []
    for r in results:
        for fi in r.findings:
            sev_label, color = _SEV_STYLE[fi.severity]
            findings_html.append(
                f"<li><span style='color:{color};font-weight:600'>{sev_label}</span> "
                f"<code>{html.escape(fi.code)}</code> — {html.escape(fi.summary)}</li>"
            )

    blind_rows = "".join(
        f"<tr><td>{html.escape(b['backend'])}</td><td>{html.escape(b['kind'])}</td>"
        f"<td>{html.escape(b['detail'])}</td></tr>"
        for b in report.blindspots
    ) or "<tr><td colspan='3'><i>no observed blind spots</i></td></tr>"

    struct_rows = "".join(
        f"<tr><td>{html.escape(g['backend'])}</td><td><code>{html.escape(g['capability'])}</code></td>"
        f"<td>{html.escape(g['detail'])}</td></tr>"
        for g in report.structural_gaps
    ) or "<tr><td colspan='3'><i>no structural gaps</i></td></tr>"

    s = report.summary
    body = f"""
<!doctype html><html><head><meta charset="utf-8"><title>Ferryte report</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 880px; margin: 2rem auto; color: #111; }}
  h1, h2 {{ font-weight: 700; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
  th, td {{ border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; }}
  th {{ background: #f6f6f6; }}
  code {{ background: #f0f0f0; padding: 1px 4px; border-radius: 3px; }}
  .pill {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; color: #fff; }}
  .pass {{ background: #15803d; }} .warn {{ background: #b45309; }} .fail {{ background: #b91c1c; }}
  ul {{ line-height: 1.5; }}
</style></head><body>
<h1>Ferryte — verification report</h1>
<p>Generated {html.escape(datetime.now(timezone.utc).isoformat())}.</p>
<h2>Summary</h2>
<p>
  <span class="pill pass">{s.get('passed', 0)} passed</span>
  <span class="pill warn">{s.get('warned', 0)} warned</span>
  <span class="pill fail">{s.get('failed', 0)} failed</span>
</p>
<p>Backends: <b>{html.escape(', '.join(s.get('backends_instrumented', [])) or '—')}</b>.
Blind-spot observations: {s.get('blindspot_observations', 0)}.
Structural capability gaps: {s.get('structural_gaps', 0)}.</p>
<h2>Scenarios</h2>
<table><tr><th>Scenario</th><th>Severity</th><th>Seeded</th><th>Deleted</th><th>Findings</th><th>Duration</th></tr>
{''.join(rows)}
</table>
<h2>Findings</h2>
<ul>{''.join(findings_html) or '<li>no findings</li>'}</ul>
<h2>Observed blind spots</h2>
<table><tr><th>Backend</th><th>Kind</th><th>Detail</th></tr>{blind_rows}</table>
<h2>Structural capability gaps</h2>
<table><tr><th>Backend</th><th>Missing capability</th><th>Why it matters</th></tr>{struct_rows}</table>
<p style="margin-top:2rem;color:#666;font-size:12px">Ferryte — verification for agent forgetting.</p>
</body></html>
"""
    path.write_text(body, encoding="utf-8")
