"""Client-facing audit report — the deliverable behind ``ferryte audit``.

``ferryte test`` writes an engineer-facing run report. This module renders the
*customer* deliverable for a paid Agent Memory Audit: an executive summary, the
scenario verdicts, every attributed wrong answer with its evidence chain, the
honest blind-spot map, and a prioritized fix list — as a single self-contained,
print-friendly HTML file (print to PDF for delivery).

Everything here is presentation. All findings come from the same engine that
powers ``ferryte test`` and ``ferryte why``.
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import __version__
from ..oracle.attribute import Attribution
from ..oracle.runner import ScenarioResult, Severity
from .coverage import CoverageReport

_SEV_LABEL = {
    Severity.PASS: ("PASS", "#10b981"),
    Severity.WARN: ("WARN", "#d97706"),
    Severity.FAIL: ("FAIL", "#dc2626"),
}

_DIAGNOSIS_EXPLANATION = {
    "phantom-memory": (
        "Phantom memory",
        "Derived from a source that was revoked; the deletion did not propagate.",
        "Delete this artifact and audit every other artifact derived from the same source.",
    ),
    "zombie-memory": (
        "Zombie memory",
        "Soft-deleted but still being retrieved into the agent's context.",
        "Verify the backend's delete actually removes the record from retrieval, not just from listings.",
    ),
    "cross-tenant": (
        "Cross-tenant leak",
        "A memory belonging to one tenant surfaced in another tenant's context.",
        "Treat as an incident: verify tenant scoping at the retrieval layer, then purge and re-test.",
    ),
    "stale-belief": (
        "Stale belief",
        "A newer fact on the same subject exists; the agent answered from the outdated one.",
        "Delete or supersede the stale artifact; add record_supersession() at the update site.",
    ),
    "hub-memory": (
        "Hub memory",
        "Outlier retrieval fan-out across distinct queries — the access signature of "
        "injected records and over-broad summaries.",
        "Review the artifact's origin; split or delete over-broad summaries; investigate injection.",
    ),
    "active-memory": (
        "Active memory",
        "A live memory with no structural fault detected.",
        "No action needed unless its content is itself wrong.",
    ),
}


@dataclass
class AuditMeta:
    """Engagement details stamped onto the report."""

    client_name: str = "Client"
    auditor: str = "Ferryte"
    engagement_id: str = ""
    environment: str = ""
    notes: str = ""
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    )


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def _overall_verdict(
    results: list[ScenarioResult], attributions: list[Attribution]
) -> tuple[str, str]:
    failed = sum(1 for r in results if r.severity == Severity.FAIL)
    warned = sum(1 for r in results if r.severity == Severity.WARN)
    bad_diags = {
        d for a in attributions for c in a.candidates for d in c.diagnoses if d != "active-memory"
    }
    if failed or {"cross-tenant", "phantom-memory", "zombie-memory"} & bad_diags:
        return (
            "ACTION REQUIRED",
            "#dc2626",
        )
    if warned or bad_diags:
        return ("ISSUES FOUND", "#d97706")
    return ("HEALTHY", "#10b981")


def _recommendations(
    results: list[ScenarioResult], attributions: list[Attribution]
) -> list[tuple[str, str]]:
    """(severity-color, text) fix list derived from findings + diagnoses, deduped, worst first."""
    recs: list[tuple[int, str, str]] = []  # (rank, color, text)
    seen: set[str] = set()

    for a in attributions:
        for c in a.candidates:
            for d in c.diagnoses:
                if d == "active-memory":
                    continue
                label, _, fix = _DIAGNOSIS_EXPLANATION.get(d, (d, "", ""))
                key = f"{d}:{c.artifact_id}"
                if key in seen or not fix:
                    continue
                seen.add(key)
                rank = 0 if d in ("cross-tenant", "phantom-memory", "zombie-memory") else 1
                color = "#dc2626" if rank == 0 else "#d97706"
                recs.append((rank, color, f"{label} ({c.artifact_id}): {fix}"))

    for r in results:
        for f in r.findings:
            if f.severity == Severity.PASS:
                continue
            key = f"finding:{f.code}:{f.summary}"
            if key in seen:
                continue
            seen.add(key)
            rank = 0 if f.severity == Severity.FAIL else 1
            color = _SEV_LABEL[f.severity][1]
            recs.append((rank, color, f"[{r.scenario}] {f.summary}"))

    recs.sort(key=lambda t: t[0])
    return [(color, text) for _, color, text in recs]


def _scenario_rows(results: list[ScenarioResult]) -> str:
    rows = []
    for r in results:
        label, color = _SEV_LABEL[r.severity]
        rows.append(
            f"<tr><td class='mono b'>{_esc(r.scenario)}</td>"
            f"<td><span class='pill' style='background:{color}'>{label}</span></td>"
            f"<td>{r.artifacts_seeded}</td><td>{r.artifacts_deleted}</td>"
            f"<td>{len(r.findings)}</td><td>{r.duration_ms:.0f} ms</td></tr>"
        )
    return "".join(rows)


def _findings_block(results: list[ScenarioResult]) -> str:
    items = []
    for r in results:
        for f in r.findings:
            label, color = _SEV_LABEL[f.severity]
            path = f" <span class='dim mono'>{_esc(' → '.join(f.path))}</span>" if f.path else ""
            items.append(
                f"<li><span class='pill' style='background:{color}'>{label}</span> "
                f"<span class='mono'>{_esc(f.code)}</span> — {_esc(f.summary)}{path}</li>"
            )
    return (
        f"<ul class='findings'>{''.join(items)}</ul>"
        if items
        else "<p class='dim'>No scenario findings.</p>"
    )


def _candidate_block(index: int, c: Any) -> str:
    worst = (
        "#dc2626"
        if any(d in ("phantom-memory", "zombie-memory", "cross-tenant") for d in c.diagnoses)
        else (
            "#d97706" if "stale-belief" in c.diagnoses or "hub-memory" in c.diagnoses else "#5a8a96"
        )
    )
    diags = ", ".join(_DIAGNOSIS_EXPLANATION.get(d, (d, "", ""))[0] for d in c.diagnoses) or "—"

    lines = []
    content = (c.content or "").strip()
    if len(content) > 300:
        content = content[:297] + "…"
    if content:
        lines.append(f"<div class='kv'><span>belief</span><div>{_esc(content)}</div></div>")
    if c.tenant_id:
        lines.append(
            f"<div class='kv'><span>tenant</span><div class='mono'>{_esc(c.tenant_id)}</div></div>"
        )
    for s in c.sources:
        revoked = " <b style='color:#dc2626'>← source revoked</b>" if s.get("revoked_at") else ""
        lines.append(
            f"<div class='kv'><span>source</span><div class='mono'>{_esc(s.get('source_id'))}{revoked}</div></div>"
        )
    if c.retrieved:
        lines.append(
            f"<div class='kv'><span>retrieval</span><div><b>retrieved {c.retrieval_count}× into "
            "context</b> — this memory actually reached the prompt</div></div>"
        )
    else:
        lines.append(
            "<div class='kv'><span>retrieval</span><div class='dim'>not seen in retrieval trace — "
            "matched on content only</div></div>"
        )
    ev = getattr(c, "evidence", {}) or {}
    if ev.get("span"):
        lines.append(
            f"<div class='kv'><span>shared span</span><div>“<b>{_esc(ev['span'])}</b>”</div></div>"
        )
    if ev.get("recorded_answer_id"):
        lines.append(
            "<div class='kv'><span>anchor</span><div><b>recorded in context for this exact answer</b> "
            f"<span class='dim mono'>({_esc(ev['recorded_answer_id'])})</span></div></div>"
        )
    if ev.get("superseded_by"):
        lines.append(
            f"<div class='kv'><span>superseded by</span><div class='mono'>{_esc(ev['superseded_by'])}</div></div>"
        )
    for d in c.diagnoses:
        label, expl, _ = _DIAGNOSIS_EXPLANATION.get(d, (d, "", ""))
        if expl and d != "active-memory":
            lines.append(
                f"<div class='kv'><span>diagnosis</span><div><b>{label}</b> — {expl}</div></div>"
            )

    return (
        f"<div class='card' style='border-left:3px solid {worst}'>"
        f"<div class='cardhead'><span class='mono b'>#{index} · {_esc(c.artifact_id)}</span>"
        f"<span class='dim'>{_esc(diags)} · confidence {c.score:.2f} · {_esc(c.backend)}</span></div>"
        f"{''.join(lines)}</div>"
    )


def _attribution_sections(attributions: list[Attribution]) -> str:
    if not attributions:
        return (
            "<p class='dim'>No wrong-answer attributions were requested for this audit. "
            "The scenario battery above covers structural verification.</p>"
        )
    sections = []
    for i, a in enumerate(attributions, start=1):
        head = f"<h3>Answer {i}: “{_esc(a.answer if len(a.answer) <= 120 else a.answer[:117] + '…')}”</h3>"
        meta = []
        if a.query:
            meta.append(f"question: “{_esc(a.query)}”")
        if a.tenant_id:
            meta.append(f"tenant: {_esc(a.tenant_id)}")
        meta_html = f"<p class='dim'>{' · '.join(meta)}</p>" if meta else ""
        if not a.candidates:
            body = "<p class='dim'>No memory in the lineage graph matched this answer.</p>"
        else:
            body = "".join(_candidate_block(j, c) for j, c in enumerate(a.candidates, start=1))
        sections.append(head + meta_html + body)
    return "".join(sections)


def _blindspot_rows(report: CoverageReport) -> tuple[str, str]:
    blind = (
        "".join(
            f"<tr><td>{_esc(b['backend'])}</td><td>{_esc(b['kind'])}</td><td>{_esc(b['detail'])}</td></tr>"
            for b in report.blindspots
        )
        or "<tr><td colspan='3' class='dim'>No blind spots observed on this run.</td></tr>"
    )
    gaps = (
        "".join(
            f"<tr><td>{_esc(g['backend'])}</td><td class='mono'>{_esc(g['capability'])}</td>"
            f"<td>{_esc(g['detail'])}</td></tr>"
            for g in report.structural_gaps
        )
        or "<tr><td colspan='3' class='dim'>No structural capability gaps.</td></tr>"
    )
    return blind, gaps


def write_audit_report(
    *,
    path: Path,
    meta: AuditMeta,
    report: CoverageReport,
    results: list[ScenarioResult],
    attributions: list[Attribution],
) -> None:
    """Render the client-facing audit deliverable as self-contained HTML."""
    verdict, verdict_color = _overall_verdict(results, attributions)
    recs = _recommendations(results, attributions)
    blind_rows, gap_rows = _blindspot_rows(report)
    s = report.summary

    recs_html = (
        "".join(
            f"<li><span class='dot' style='background:{color}'></span>{_esc(text)}</li>"
            for color, text in recs
        )
        or "<li><span class='dot' style='background:#10b981'></span>No remediation required from this run.</li>"
    )

    backends = ", ".join(s.get("backends_instrumented", [])) or "—"
    notes_html = f"<h2>Auditor notes</h2><p>{_esc(meta.notes)}</p>" if meta.notes else ""

    body = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>Agent Memory Audit — {_esc(meta.client_name)}</title>
<style>
  :root {{ --ink:#0e1116; --dim:#5c6570; --rule:#e3e6ea; --deep:#0d3d4e; --mid:#5a8a96; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,system-ui,'Segoe UI',sans-serif; color:var(--ink);
         max-width:860px; margin:0 auto; padding:48px 32px; line-height:1.55; font-size:15px; }}
  .mono {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:0.92em; }}
  .b {{ font-weight:600; }} .dim {{ color:var(--dim); }}
  header {{ border-bottom:2px solid var(--deep); padding-bottom:20px; margin-bottom:28px; }}
  header .brand {{ font-weight:700; letter-spacing:-0.02em; color:var(--deep); font-size:14px;
                   text-transform:uppercase; }}
  h1 {{ font-size:30px; letter-spacing:-0.025em; margin:6px 0 2px; }}
  h2 {{ font-size:19px; letter-spacing:-0.018em; margin:34px 0 10px; border-bottom:1px solid var(--rule);
        padding-bottom:6px; }}
  h3 {{ font-size:15.5px; margin:22px 0 6px; }}
  table {{ width:100%; border-collapse:collapse; margin:10px 0 18px; font-size:14px; }}
  th,td {{ border:1px solid var(--rule); padding:7px 10px; text-align:left; vertical-align:top; }}
  th {{ background:#f4f6f7; font-weight:600; }}
  .pill {{ display:inline-block; padding:1px 9px; border-radius:999px; color:#fff; font-size:11.5px;
           font-weight:700; letter-spacing:0.04em; }}
  .verdict {{ display:inline-block; padding:5px 14px; border-radius:6px; color:#fff; font-weight:700;
              letter-spacing:0.05em; font-size:13px; background:{verdict_color}; }}
  .metagrid {{ display:grid; grid-template-columns:1fr 1fr; gap:2px 24px; margin-top:14px;
               font-size:13.5px; color:var(--dim); }}
  .card {{ border:1px solid var(--rule); border-radius:8px; padding:12px 16px; margin:10px 0; }}
  .cardhead {{ display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;
               margin-bottom:8px; }}
  .kv {{ display:flex; gap:10px; margin:3px 0; }}
  .kv > span {{ min-width:110px; color:var(--dim); font-size:12.5px; text-transform:uppercase;
                letter-spacing:0.05em; padding-top:2px; }}
  .kv > div {{ flex:1; }}
  ul.findings li, ol.recs li {{ margin:6px 0; }}
  ol.recs {{ counter-reset:rec; list-style:none; padding-left:0; }}
  ol.recs li {{ display:flex; align-items:baseline; gap:10px; }}
  .dot {{ width:10px; height:10px; border-radius:999px; display:inline-block; flex:none;
          position:relative; top:1px; }}
  footer {{ margin-top:44px; padding-top:14px; border-top:1px solid var(--rule); color:var(--dim);
            font-size:12px; }}
  @media print {{ body {{ padding:0; font-size:13px; }} h2 {{ break-after:avoid; }}
                  .card {{ break-inside:avoid; }} }}
</style></head><body>
<header>
  <div class="brand">Ferryte · Agent Memory Audit</div>
  <h1>{_esc(meta.client_name)}</h1>
  <span class="verdict">{verdict}</span>
  <div class="metagrid">
    <div>Prepared by: <b>{_esc(meta.auditor)}</b></div>
    <div>Date: <b>{_esc(meta.generated_at)}</b></div>
    <div>Environment: <b>{_esc(meta.environment) or "—"}</b></div>
    <div>Engagement: <b>{_esc(meta.engagement_id) or "—"}</b></div>
  </div>
</header>

<h2>Executive summary</h2>
<p>
  This audit instrumented the agent's memory layer ({_esc(backends)}), ran
  {len(results)} Ferryte structural verification scenario{"s" if len(results) != 1 else ""},
  and attributed {len(attributions)}
  reported wrong answer{"s" if len(attributions) != 1 else ""} to the memories that caused them.
  Result: <b>{s.get("passed", 0)} scenario{"s" if s.get("passed", 0) != 1 else ""} passed,
  {s.get("warned", 0)} warned, {s.get("failed", 0)} failed</b>, with
  {s.get("blindspot_observations", 0)} observed blind-spot{"s" if s.get("blindspot_observations", 0) != 1 else ""}
  and {s.get("structural_gaps", 0)} structural capability gap{"s" if s.get("structural_gaps", 0) != 1 else ""}.
</p>

<h2>Prioritized fix list</h2>
<ol class="recs">{recs_html}</ol>

<h2>Scenario verification</h2>
<p class="dim">Each scenario seeds canary data, actuates the backend's own delete/scoping APIs,
  and verifies both retrieval results and raw store contents — reducing the risk of a
  "canary passed but tainted context still stored" false positive.</p>
<table>
  <tr><th>Scenario</th><th>Verdict</th><th>Seeded</th><th>Deleted</th><th>Findings</th><th>Duration</th></tr>
  {_scenario_rows(results)}
</table>
{_findings_block(results)}

<h2>Wrong-answer attribution</h2>
{_attribution_sections(attributions)}

<h2>What this audit could not verify</h2>
<p class="dim">Ferryte reports its own limits. Anything listed here was <i>not</i> proven safe —
it was unverifiable on this backend, on this run.</p>
<table><tr><th>Backend</th><th>Kind</th><th>Detail</th></tr>{blind_rows}</table>
<table><tr><th>Backend</th><th>Missing capability</th><th>Why it matters</th></tr>{gap_rows}</table>
{notes_html}

<h2>Methodology</h2>
<p>
  Ferryte instruments every memory write, retrieval, and delete via
  <span class="mono">ferryte.instrument()</span>, building a lineage graph from each source to
  every derived artifact. Attribution ranks memories against a wrong answer using recorded
  answer→memory edges (when available), retrieval traces, IDF-weighted content overlap with
  shared-span evidence, and semantic residue. Counterfactual replay ablates a suspect from live
  retrieval to show what the agent's context would have been without it. All checks run inside
  the client's environment. Ferryte sends no memory content to a hosted Ferryte service; this
  local report may contain excerpts and should be reviewed before it is shared.
</p>

<footer>
  Generated by Ferryte {_esc(__version__)} · ferryte.dev · This report reflects the state of the instrumented
  environment at the time of the run. Verification is evidence of tested behavior, not a general
  guarantee of future behavior.
</footer>
</body></html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
