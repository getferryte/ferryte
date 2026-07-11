"""`ferryte` CLI.

Commands:

    ferryte why "<bad answer>"         # trace a wrong answer to the memory that caused it
    ferryte audit                      # run the client-facing audit battery + report
    ferryte init                       # create local state dir, write ferryte.toml stub
    ferryte test [--scenario NAME]     # run scenarios, write reports/latest.{json,html}
    ferryte coverage                   # render the coverage + blind-spot map
    ferryte list-scenarios             # list registered scenarios
    ferryte serve                      # start the dashboard API (FastAPI)

The CLI is deliberately tiny — the heavy lifting is in the library. This makes
it trivial to run from CI, from a notebook, or as a library call.
"""

from __future__ import annotations

import importlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .config import get_config, set_config
from .instrument import current_instrumentation, instrument
from .lineage import get_lineage
from .oracle.runner import ScenarioRegistry, Severity, run_scenarios
from .reports import (
    build_coverage_report,
    render_blindspots_table,
    render_coverage_table,
    render_results_table,
    write_html_report,
    write_json_report,
)

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Ferryte — memory debugging for AI agents.",
)
console = Console()


_BANNER = (
    "[bold]Ferryte[/bold] — memory debugging for AI agents "
    f"[dim]v{__version__}[/dim]"
)


def _state_dir_option() -> Path:
    return get_config().state_dir


def _maybe_load_user_module(module: Optional[str]) -> None:
    """If --module=foo.bar is passed, import it to let it set up its agents."""
    if not module:
        return
    sys.path.insert(0, str(Path.cwd()))
    importlib.import_module(module)


def _bootstrap_vector_client(handle: Any) -> Any:
    """Create and retain the built-in demo store for the current CLI command."""
    from .adapters.vector import InMemoryVectorStore

    client = InMemoryVectorStore()
    if handle.adapter_for(client) is None:
        adapter = next((a for a in handle.adapters if a.name == "vector"), None)
        if adapter is not None:
            handle.track(client, adapter)
    return client


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"ferryte {__version__}")
        raise typer.Exit()


@app.callback()
def root(
    state_dir: Optional[Path] = typer.Option(
        None, "--state-dir", help="Where to store the lineage DB and reports."
    ),
    strict: bool = typer.Option(False, "--strict", help="Raise on adapter errors."),
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    cfg = get_config()
    if state_dir is not None:
        cfg.state_dir = state_dir.expanduser().resolve()
    cfg.strict = strict
    set_config(cfg)
    _ = version  # consumed by callback; silence linter


@app.command()
def init(
    project_name: str = typer.Option("agent", "--name", help="Project name written into ferryte.toml."),
) -> None:
    """Create the local state directory and a minimal config stub."""
    cfg = get_config()
    cfg.ensure_dirs()
    toml_path = Path.cwd() / "ferryte.toml"
    if not toml_path.exists():
        toml_path.write_text(
            "[ferryte]\n"
            f"project = \"{project_name}\"\n"
            f"state_dir = \"{cfg.state_dir.as_posix()}\"\n"
            "\n"
            "[ferryte.scenarios]\n"
            "# Override defaults per scenario, e.g.\n"
            "# 'source-revocation' = { count = 5 }\n",
            encoding="utf-8",
        )
    console.print(_BANNER)
    console.print(
        Panel.fit(
            f"State dir: [bold]{cfg.state_dir}[/bold]\n"
            f"Config:    [bold]{toml_path}[/bold]\n\n"
            "Next:\n"
            "  1) [bold]ferryte.instrument()[/bold] in your app (one line, anywhere before your memory client is built)\n"
            "  2) [bold]ferryte test --module my_app[/bold] to run the forgetting suite\n"
            "  3) [bold]ferryte coverage[/bold] to see what was verified and what wasn't",
            title="initialised",
        )
    )


@app.command("list-scenarios")
def list_scenarios() -> None:
    """List every registered scenario."""
    from .oracle import scenarios as _scenarios  # noqa: F401 - registration side-effect

    names = ScenarioRegistry.names()
    if not names:
        console.print("[yellow]No scenarios registered.[/yellow]")
        raise typer.Exit(code=1)
    console.print(_BANNER)
    for n in names:
        console.print(f"  • [bold]{n}[/bold]")


@app.command()
def test(
    scenario: List[str] = typer.Option(
        ["all"],
        "--scenario",
        "-s",
        help="One or more scenario names (or 'all').",
    ),
    module: Optional[str] = typer.Option(
        None,
        "--module",
        "-m",
        help="Import your app module so its memory clients exist before scenarios run.",
    ),
    bootstrap: bool = typer.Option(
        True,
        "--bootstrap/--no-bootstrap",
        help="If true and no clients are detected, build a self-contained vector store to test against.",
    ),
    report_dir: Optional[Path] = typer.Option(
        None, "--report-dir", help="Override the directory reports are written to."
    ),
    fail_on_warn: bool = typer.Option(
        False,
        "--fail-on-warn",
        help="Treat WARN as a non-zero CI exit code.",
    ),
) -> None:
    """Run scenarios against the instrumented agent and write the report."""
    cfg = get_config()
    handle = current_instrumentation() or instrument()

    _maybe_load_user_module(module)

    if not handle.list_clients() and bootstrap:
        # Keep a strong reference for the duration of the command. Instrumentation
        # intentionally stores clients weakly so it does not own application state.
        _bootstrap_client = _bootstrap_vector_client(handle)
        console.print(
            "[yellow]No instrumented memory clients found — bootstrapped a self-contained "
            "InMemoryVectorStore for this run.[/yellow]"
        )

    if not handle.list_clients():
        console.print(
            "[red]No instrumented clients to test. "
            "Pass --module to import your app, or let --bootstrap stand up a toy store.[/red]"
        )
        raise typer.Exit(code=2)

    console.print(_BANNER)
    results = run_scenarios(instrumentation=handle, names=list(scenario))
    render_results_table(results, console)

    lineage = get_lineage()
    report = build_coverage_report(
        instrumentation=handle, lineage=lineage, results=results
    )

    out_dir = (report_dir or (cfg.state_dir / "reports")).expanduser().resolve()
    write_json_report(path=out_dir / "latest.json", report=report, results=results)
    write_html_report(path=out_dir / "latest.html", report=report, results=results)

    console.print(
        f"\nReport written to [bold]{out_dir / 'latest.html'}[/bold] (and latest.json)."
    )

    fail = any(r.severity == Severity.FAIL for r in results)
    warn = any(r.severity == Severity.WARN for r in results)
    if fail:
        console.print("[red]One or more scenarios FAILED — revoked or leaked data influenced the agent.[/red]")
        raise typer.Exit(code=1)
    if warn and fail_on_warn:
        console.print("[yellow]Warnings present and --fail-on-warn is set.[/yellow]")
        raise typer.Exit(code=1)
    console.print("[green]All scenarios passed.[/green]")


_DIAGNOSIS_LABEL = {
    "phantom-memory": ("phantom memory", "revoked source still answering"),
    "zombie-memory": ("zombie memory", "deleted but retrieved after the delete"),
    "cross-tenant": ("cross-tenant", "another tenant's memory surfaced here"),
    "stale-belief": ("stale belief", "a newer fact on this subject exists"),
    "hub-memory": ("hub memory", "outlier retrieval fan-out — poison/over-broad summary pattern"),
    "active-memory": ("active memory", "live memory, not obviously faulty"),
}


def _parse_since(value: Optional[str]) -> Optional[float]:
    """'45m' / '2h' / '3d' / '90s' -> unix timestamp that far in the past."""
    if not value:
        return None
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([smhd]?)", value.strip().lower())
    if not m:
        raise typer.BadParameter("use e.g. 45m, 2h, 3d, or plain seconds")
    mult = {"": 1.0, "s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0}[m.group(2)]
    return time.time() - float(m.group(1)) * mult


@app.command()
def why(
    answer: str = typer.Argument(
        ...,
        help="The wrong/stale/leaked answer (or a distinctive phrase from it).",
    ),
    query: Optional[str] = typer.Option(
        None, "--query", "-q", help="The question the agent was answering, if known."
    ),
    tenant: Optional[str] = typer.Option(
        None, "--tenant", "-t", help="The tenant/user who saw the answer (enables cross-tenant diagnosis)."
    ),
    limit: int = typer.Option(5, "--limit", "-n", help="Max candidate memories to show."),
    module: Optional[str] = typer.Option(
        None, "--module", "-m", help="Import your app module so its lineage is loaded first."
    ),
    since: Optional[str] = typer.Option(
        None, "--since", help="Only count retrievals in this window (e.g. 45m, 2h, 3d)."
    ),
    replay: bool = typer.Option(
        False,
        "--replay",
        help="Counterfactual check: re-probe the live memory client without the top "
        "suspect and show what the agent's context would have been (needs --query "
        "and an instrumented client, e.g. via --module).",
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable JSON instead of a table."),
) -> None:
    """Explain a bad answer: rank the memories that most likely caused it.

    Reads the lineage graph your instrumented agent has already written, scores
    every stored memory against the answer, and traces the top matches back to
    their source — flagging phantom (revoked), stale, cross-tenant, zombie, and
    hub (poison-pattern) memories along the way. With --replay it then ablates
    the top suspect from live retrieval and shows the counterfactual context.
    """
    from .oracle.attribute import attribute_answer

    if replay and not query:
        raise typer.BadParameter("--replay needs --query (the question the agent was answering)")

    _maybe_load_user_module(module)
    lineage = get_lineage()
    since_ts = _parse_since(since)
    result = attribute_answer(
        answer, lineage=lineage, query=query, tenant_id=tenant, limit=limit, since=since_ts
    )

    replay_report = None
    if replay and result.candidates:
        from .oracle.replay import replay_query

        replay_report = replay_query(
            query or "",
            result.candidates[0].artifact_id,
            tenant_id=tenant,
        )

    if as_json:
        payload = result.to_dict()
        if replay_report is not None:
            payload["replay"] = replay_report.to_dict()
        console.print_json(json.dumps(payload))
        raise typer.Exit(code=0 if result.candidates else 3)

    console.print(_BANNER)
    if not result.candidates:
        console.print(
            Panel.fit(
                "No memory in the lineage graph matches that answer.\n\n"
                "Either the agent isn't instrumented yet ([bold]ferryte.instrument()[/bold]), "
                "no memory was written/retrieved for this, or the phrase is too generic — "
                "try a more distinctive fragment of the answer.",
                title="no attribution",
            )
        )
        raise typer.Exit(code=3)

    top = result.candidates[0]
    console.print(
        f"\n[bold]caused by {len(result.candidates)} "
        f"{'memory' if len(result.candidates) == 1 else 'candidate memories'}[/bold] "
        f"· top confidence [bold]{top.score:.2f}[/bold]\n"
    )

    for i, c in enumerate(result.candidates, start=1):
        _render_candidate(i, c)

    if replay_report is not None:
        _render_replay(replay_report)

    console.print(
        f"\n[dim]Fix the top suspect:[/dim] "
        f"delete [bold]{top.artifact_id}[/bold] from your store, then re-run "
        f"[bold]ferryte why[/bold] to confirm it's gone.\n"
    )


def _render_replay(r: Any) -> None:  # ReplayReport
    lines: list[str] = []
    if r.verdict == "no-clients":
        lines.append(
            "No instrumented memory client to probe. Pass [bold]--module your_app[/bold] "
            "so your client is constructed (after ferryte.instrument()) in this process."
        )
        tone = "yellow"
    elif r.verdict == "not-retrieved":
        lines.append(
            f"[bold]{r.suspect_artifact_id}[/bold] does not enter the retrieved context "
            f"for this query right now [dim]({r.backend})[/dim]."
        )
        lines.append(
            "  Its content match may be historical — check the retrieval trace window "
            "with [bold]--since[/bold], or the memory may already be fixed."
        )
        tone = "yellow"
    else:
        lines.append(
            f"[bold]{r.suspect_artifact_id}[/bold] is live in context at "
            f"[bold]rank {r.suspect_rank}[/bold] for this query [dim]({r.backend})[/dim]."
        )
        if r.replacement is not None:
            snippet = (r.replacement.content or "").strip().replace("\n", " ")
            if len(snippet) > 140:
                snippet = snippet[:137] + "…"
            lines.append("")
            lines.append("  [bold]Without it, the agent's context becomes:[/bold]")
            lines.append(f"  {snippet}")
            if r.replacement.artifact_id:
                lines.append(f"  [dim]({r.replacement.artifact_id})[/dim]")
        tone = "red"

    console.print(
        Panel(
            "\n".join(lines),
            title=f"[{tone}]counterfactual replay · {r.verdict}[/{tone}]",
            title_align="left",
            border_style=tone,
        )
    )


def _render_candidate(index: int, c: Any) -> None:  # MemoryCandidate
    import time as _time

    diags = ", ".join(
        _DIAGNOSIS_LABEL.get(d, (d, ""))[0] for d in c.diagnoses
    )
    tone = "red" if any(
        d in ("phantom-memory", "zombie-memory", "cross-tenant") for d in c.diagnoses
    ) else ("yellow" if "stale-belief" in c.diagnoses else "cyan")

    lines: list[str] = []
    content = (c.content or "").strip().replace("\n", " ")
    if len(content) > 160:
        content = content[:157] + "…"
    lines.append(f"[bold]{c.artifact_id}[/bold]  [dim]{c.backend} · {c.kind}[/dim]")
    if content:
        lines.append(f"  belief: {content}")
    if c.tenant_id:
        lines.append(f"  tenant: {c.tenant_id}")

    for s in c.sources:
        revoked = s.get("revoked_at")
        if revoked:
            lines.append(f"  from '[bold]{s['source_id']}[/bold]'  [red]← source revoked[/red]")
        else:
            lines.append(f"  from '{s['source_id']}'")

    if c.retrieved:
        when = ""
        if c.last_retrieved_at:
            ago = max(0, int(_time.time() - c.last_retrieved_at))
            when = f", last {ago}s ago" if ago < 3600 else ""
        lines.append(
            f"  [bold]retrieved {c.retrieval_count}× into context[/bold]{when} "
            f"[dim](actually reached the prompt)[/dim]"
        )
    else:
        lines.append("  [dim]not seen in retrieval trace — matched on content only[/dim]")

    if c.deleted_at:
        lines.append("  [red]soft-deleted, yet still present[/red]")

    ev = getattr(c, "evidence", {}) or {}
    if ev.get("span") and c.method != "exact":
        lines.append(f'  shared span: "[bold]{ev["span"]}[/bold]"')
    if ev.get("recorded_answer_id"):
        lines.append(
            f"  [bold]recorded in context for this answer[/bold] "
            f"[dim](answer {ev['recorded_answer_id']})[/dim]"
        )
    if ev.get("superseded_by"):
        lines.append(
            f"  superseded by [bold]{ev['superseded_by']}[/bold] "
            f"[dim](recorded supersession edge)[/dim]"
        )
    elif ev.get("newer_artifact"):
        lines.append(f"  newer competing memory: [dim]{ev['newer_artifact']}[/dim]")
    if ev.get("distinct_queries"):
        lines.append(
            f"  retrieved across [bold]{ev['distinct_queries']} distinct queries[/bold]"
        )

    for d in c.diagnoses:
        label, expl = _DIAGNOSIS_LABEL.get(d, (d, ""))
        if expl:
            lines.append(f"  → [bold]{label}[/bold]: {expl}")

    console.print(
        Panel(
            "\n".join(lines),
            title=f"[{tone}]#{index} · {diags} · conf {c.score:.2f} · {c.method}[/{tone}]",
            title_align="left",
            border_style=tone,
        )
    )


@app.command()
def audit(
    client_name: str = typer.Option(
        "Client", "--client", "-c", help="Client/company name stamped on the report."
    ),
    answer: List[str] = typer.Option(
        [], "--answer", "-a", help="A wrong answer to attribute (repeatable, up to 5)."
    ),
    answer_query: List[str] = typer.Option(
        [],
        "--answer-query",
        help="Question paired with the Nth --answer (repeat in the same order; optional).",
    ),
    tenant: Optional[str] = typer.Option(
        None, "--tenant", "-t", help="Tenant/user scope for attribution."
    ),
    module: Optional[str] = typer.Option(
        None, "--module", "-m", help="Import your app module so its memory clients exist."
    ),
    scenario: List[str] = typer.Option(
        ["all"], "--scenario", "-s", help="Scenario names to run (or 'all')."
    ),
    bootstrap: bool = typer.Option(
        True,
        "--bootstrap/--no-bootstrap",
        help="If no clients are detected, build a self-contained vector store (demo mode).",
    ),
    environment: str = typer.Option(
        "", "--environment", help="Environment label for the report (e.g. staging, prod)."
    ),
    auditor: str = typer.Option("Ferryte", "--auditor", help="Who prepared the report."),
    engagement_id: str = typer.Option("", "--engagement", help="Engagement/SOW reference."),
    notes: str = typer.Option("", "--notes", help="Auditor notes appended to the report."),
    out_dir: Optional[Path] = typer.Option(
        None, "--out", help="Output directory (default: <state>/reports/audit)."
    ),
) -> None:
    """Run the full Agent Memory Audit and write the client-facing deliverable.

    One command = the paid audit: runs every scenario, attributes each provided
    wrong answer, and writes audit.json plus a print-ready audit.html
    (print to PDF for delivery).
    """
    from .oracle.attribute import attribute_answer
    from .reports import AuditMeta, write_audit_report

    if len(answer) > 5:
        raise typer.BadParameter("--answer can be given at most 5 times per audit")
    if len(answer_query) > len(answer):
        raise typer.BadParameter("--answer-query cannot be given more times than --answer")

    cfg = get_config()
    handle = current_instrumentation() or instrument()
    _maybe_load_user_module(module)

    if not handle.list_clients() and bootstrap:
        # Keep a strong reference for the duration of the command. Instrumentation
        # intentionally stores clients weakly so it does not own application state.
        _bootstrap_client = _bootstrap_vector_client(handle)
        console.print(
            "[yellow]No instrumented memory clients found — bootstrapped a self-contained "
            "InMemoryVectorStore (demo mode; findings describe the toy store, not your stack).[/yellow]"
        )
    if not handle.list_clients():
        console.print(
            "[red]No instrumented clients to audit. Pass --module to import your app.[/red]"
        )
        raise typer.Exit(code=2)

    console.print(_BANNER)
    console.print(f"[bold]Agent Memory Audit[/bold] · {client_name}\n")

    results = run_scenarios(instrumentation=handle, names=list(scenario))
    render_results_table(results, console)

    lineage = get_lineage()
    report = build_coverage_report(instrumentation=handle, lineage=lineage, results=results)

    attributions = []
    for i, ans in enumerate(answer):
        q = answer_query[i] if i < len(answer_query) else None
        console.print(f"\n[bold]Attributing answer {i + 1}:[/bold] “{ans}”")
        result = attribute_answer(ans, lineage=lineage, query=q, tenant_id=tenant, limit=5)
        if result.candidates:
            for j, c in enumerate(result.candidates, start=1):
                _render_candidate(j, c)
        else:
            console.print("  [dim]no memory matched this answer[/dim]")
        attributions.append(result)

    out = (out_dir or (cfg.state_dir / "reports" / "audit")).expanduser().resolve()
    meta = AuditMeta(
        client_name=client_name,
        auditor=auditor,
        engagement_id=engagement_id,
        environment=environment,
        notes=notes,
    )
    write_audit_report(
        path=out / "audit.html",
        meta=meta,
        report=report,
        results=results,
        attributions=attributions,
    )
    payload = {
        "meta": {
            "client_name": meta.client_name,
            "auditor": meta.auditor,
            "engagement_id": meta.engagement_id,
            "environment": meta.environment,
            "notes": meta.notes,
            "generated_at": meta.generated_at,
        },
        "coverage": report.to_dict(),
        "results": [r.to_dict() for r in results],
        "attributions": [a.to_dict() for a in attributions],
    }
    (out / "audit.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    console.print(
        f"\nDeliverable written to [bold]{out / 'audit.html'}[/bold] (print to PDF) "
        "and audit.json."
    )
    fail = any(r.severity == Severity.FAIL for r in results)
    if fail:
        console.print("[red]Audit surfaced FAIL-severity issues — see the fix list in the report.[/red]")


@app.command()
def coverage(
    report_dir: Optional[Path] = typer.Option(
        None, "--report-dir", help="Where to read the report from (defaults to state dir)."
    ),
) -> None:
    """Render the latest coverage + blind-spot map."""
    cfg = get_config()
    out_dir = (report_dir or (cfg.state_dir / "reports")).expanduser().resolve()
    path = out_dir / "latest.json"
    if not path.exists():
        console.print(
            f"[red]No report at {path}. Run [bold]ferryte test[/bold] first.[/red]"
        )
        raise typer.Exit(code=2)
    payload = json.loads(path.read_text(encoding="utf-8"))
    from .oracle.runner import Finding, ScenarioResult
    from .reports.coverage import CoverageReport

    cov_data = payload["coverage"]
    report = CoverageReport(
        summary=cov_data.get("summary", {}),
        backends=cov_data.get("backends", []),
        scenarios=cov_data.get("scenarios", []),
        blindspots=cov_data.get("blindspots", []),
        structural_gaps=cov_data.get("structural_gaps", []),
        lineage_counts=cov_data.get("lineage_counts", {}),
    )
    results = []
    for r in payload.get("results", []):
        results.append(
            ScenarioResult(
                scenario=r["scenario"],
                severity=Severity(r["severity"]),
                artifacts_seeded=r.get("artifacts_seeded", 0),
                artifacts_deleted=r.get("artifacts_deleted", 0),
                duration_ms=r.get("duration_ms", 0.0),
                coverage=r.get("coverage", {}),
                blast=r.get("blast", []),
                findings=[
                    Finding(
                        severity=Severity(f["severity"]),
                        code=f["code"],
                        summary=f["summary"],
                        path=f.get("path", []),
                        detail=f.get("detail", {}),
                    )
                    for f in r.get("findings", [])
                ],
            )
        )
    console.print(_BANNER)
    render_coverage_table(report, console)
    render_blindspots_table(report, console)
    if results:
        render_results_table(results, console)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8787, "--port"),
) -> None:
    """Start the local HTTP API the dashboard reads from."""
    from .api import serve as _serve

    console.print(_BANNER)
    console.print(f"Serving on http://{host}:{port}")
    _serve(host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    app()
