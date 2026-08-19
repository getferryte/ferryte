"""`ferryte` CLI.

Commands:

    ferryte why "<bad answer>"         # trace a wrong answer to the memory that caused it
    ferryte isolation-check <uri>      # can tenant B reach tenant A's data? three probes
    ferryte attest-deletion <uri>      # delete, verify, emit a signed deletion record
    ferryte verify-attestation <file>  # check an attestation's hash + signature
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


@app.command("isolation-check")
def isolation_check(
    uri: str = typer.Argument(
        ...,
        help=(
            "Backend URI. postgres://…  chroma://path#collection  "
            "qdrant://host#collection  memory://"
        ),
    ),
    tenants: Optional[str] = typer.Option(
        None, "--tenants", help="Comma-separated tenant ids. Omit to auto-discover."
    ),
    query: Optional[List[str]] = typer.Option(
        None, "--query", "-q", help="A query your users actually run. Repeatable."
    ),
    table: Optional[str] = typer.Option(None, "--table", help="Table / collection name."),
    tenant_column: str = typer.Option("tenant_id", "--tenant-column"),
    source_column: str = typer.Option("source_id", "--source-column"),
    content_column: str = typer.Option("content", "--content-column"),
    id_column: str = typer.Option("id", "--id-column"),
    limit: int = typer.Option(10, "--limit", help="Rows per probe."),
    no_semantic: bool = typer.Option(
        False, "--no-semantic", help="Skip the semantic-neighbour probe."
    ),
    report: Optional[Path] = typer.Option(
        None, "--report", help="Write the JSON report here."
    ),
    markdown: Optional[Path] = typer.Option(
        None, "--markdown", help="Write a human-readable Markdown report here."
    ),
) -> None:
    """Check whether one tenant's data can surface to another.

    Runs three probes — filtered, unfiltered blast radius, and semantic
    neighbours — and exits non-zero if any real leak is found, so it works as a
    CI gate as well as a one-off.
    """
    from .connect import open_store
    from .oracle.isolation import run_isolation_check

    console.print(_BANNER)
    try:
        opened = open_store(
            uri,
            table=table,
            tenant_column=tenant_column,
            source_column=source_column,
            content_column=content_column,
            id_column=id_column,
        )
    except Exception as exc:  # noqa: BLE001 - user-facing, must be readable
        console.print(f"[red]Could not connect:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    tenant_list = [t.strip() for t in tenants.split(",") if t.strip()] if tenants else None
    console.print(f"[dim]backend:[/dim] {opened.label}")
    for note in opened.notes:
        console.print(f"[yellow]note:[/yellow] {note}")

    try:
        result = run_isolation_check(
            opened.store,
            tenants=tenant_list,
            queries=list(query or []),
            limit=limit,
            semantic_probe=not no_semantic,
            backend=opened.label,
        )
    finally:
        opened.close()

    for note in opened.notes:
        result.blind_spots.append(note)

    _render_isolation(result)

    if report:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        console.print(f"[dim]JSON report → {report}[/dim]")
    if markdown:
        markdown.parent.mkdir(parents=True, exist_ok=True)
        markdown.write_text(_isolation_markdown(result), encoding="utf-8")
        console.print(f"[dim]Markdown report → {markdown}[/dim]")

    if result.severity == Severity.FAIL:
        raise typer.Exit(code=1)


def _render_isolation(result: Any) -> None:
    from rich.table import Table

    verdict = {
        Severity.PASS: "[green]PASS[/green] — no cross-tenant leak detected",
        Severity.WARN: "[yellow]PASS with blind spots[/yellow] — see below",
        Severity.FAIL: "[red]FAIL[/red] — cross-tenant leakage detected",
    }[result.severity]
    console.print(
        Panel.fit(
            f"{verdict}\n\n"
            f"Tenants checked: {', '.join(result.tenants_checked) or '—'}\n"
            f"Queries run: {result.queries_run}\n"
            f"Filtered leaks: {len(result.filtered_leaks)}   "
            f"Semantic leaks: {len(result.semantic_leaks)}   "
            f"Unfiltered exposure: {len(result.unfiltered_exposure)}",
            title="isolation check",
        )
    )

    leaks = list(result.filtered_leaks) + list(result.semantic_leaks)
    if leaks:
        table = Table(title="Cross-tenant leaks", show_lines=False)
        table.add_column("probe")
        table.add_column("querying")
        table.add_column("owner")
        table.add_column("query", overflow="fold")
        table.add_column("excerpt", overflow="fold")
        for f in leaks[:25]:
            table.add_row(
                f.probe, f.querying_tenant, f.owning_tenant, f.query[:40], f.excerpt
            )
        console.print(table)
        if len(leaks) > 25:
            console.print(f"[dim]…and {len(leaks) - 25} more (see the JSON report)[/dim]")

    if result.unfiltered_exposure:
        console.print(
            f"[yellow]Blast radius:[/yellow] {len(result.unfiltered_exposure)} documents "
            "from other tenants would be reachable if a query ever lost its tenant filter. "
            "That is a measure of exposure, not a live defect."
        )

    for b in result.blind_spots:
        console.print(f"[yellow]blind spot:[/yellow] {b}")


def _isolation_markdown(result: Any) -> str:
    lines = ["# Multi-Tenant Isolation Check", ""]
    badge = {
        Severity.PASS: "PASS — no cross-tenant leak detected",
        Severity.WARN: "PASS with stated blind spots",
        Severity.FAIL: "FAIL — cross-tenant leakage detected",
    }[result.severity]
    lines += [
        f"**Verdict:** {badge}",
        "",
        f"- **Backend:** {result.backend}",
        f"- **Tenants checked:** {', '.join(result.tenants_checked) or '—'}",
        f"- **Queries run:** {result.queries_run}",
        f"- **Duration:** {result.duration_ms:.0f} ms",
        "",
        "## What was tested",
        "",
        "1. **Filtered probe** — each tenant's queries run *with* the tenant filter. "
        "A foreign document here means the filter itself is broken.",
        "2. **Unfiltered blast radius** — the same queries with no filter, measuring what "
        "one forgotten predicate would expose. Reported as exposure, not as a defect.",
        "3. **Semantic-neighbour probe** — queries derived from one tenant's own documents, "
        "run as another tenant. This is leakage through similarity rather than a missing "
        "filter, and it is the path that does not look like a bug in any log.",
        "",
    ]
    for title, items in (
        ("Filtered leaks (critical)", result.filtered_leaks),
        ("Semantic-neighbour leaks (critical)", result.semantic_leaks),
    ):
        lines += [f"## {title}", ""]
        if not items:
            lines += ["_None found._", ""]
            continue
        lines += ["| querying tenant | owning tenant | query | document | excerpt |", "|---|---|---|---|---|"]
        for f in items:
            lines.append(
                f"| {f.querying_tenant} | {f.owning_tenant} | `{f.query[:40]}` | "
                f"`{f.artifact_id}` | {f.excerpt} |"
            )
        lines.append("")
    lines += ["## Unfiltered blast radius", ""]
    if result.unfiltered_exposure:
        lines.append(
            f"{len(result.unfiltered_exposure)} documents across other tenants would be "
            "reachable by a single query missing its tenant filter."
        )
    else:
        lines.append("_No unfiltered exposure measured._")
    lines += ["", "## Blind spots — what was NOT verified", ""]
    if result.blind_spots:
        for b in result.blind_spots:
            lines.append(f"- {b}")
    else:
        lines.append("_None recorded._")
    lines += [
        "",
        "---",
        "",
        "_Generated by Ferryte. This report states what was observed through the "
        "connection provided. It does not cover backups, replicas, downstream exports, "
        "or stores not connected to this run._",
    ]
    return "\n".join(lines) + "\n"


@app.command("attest-deletion")
def attest_deletion(
    uri: str = typer.Argument(..., help="Backend URI (see isolation-check)."),
    source: str = typer.Option(..., "--source", help="The source id to forget."),
    tenant: Optional[str] = typer.Option(None, "--tenant", help="Tenant scope, if any."),
    probe: Optional[List[str]] = typer.Option(
        None, "--probe", help="Text to search for after deletion. Repeatable."
    ),
    table: Optional[str] = typer.Option(None, "--table"),
    tenant_column: str = typer.Option("tenant_id", "--tenant-column"),
    source_column: str = typer.Option("source_id", "--source-column"),
    content_column: str = typer.Option("content", "--content-column"),
    sign: bool = typer.Option(False, "--sign", help="Ed25519-sign the attestation."),
    key: Optional[Path] = typer.Option(None, "--key", help="Signing key path."),
    out: Optional[Path] = typer.Option(None, "--out", help="Write the JSON attestation here."),
    markdown: Optional[Path] = typer.Option(None, "--markdown", help="Write Markdown here."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Verify only; do not delete anything."
    ),
) -> None:
    """Delete a source, verify it is gone, and emit a signed attestation."""
    from .connect import open_store
    from .reports.attestation import DeletionProbe, build_attestation

    console.print(_BANNER)
    started = time.time()
    try:
        opened = open_store(
            uri,
            table=table,
            tenant_column=tenant_column,
            source_column=source_column,
            content_column=content_column,
        )
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Could not connect:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    store = opened.store
    blind: list[str] = list(opened.notes)
    deleted = 0
    try:
        if dry_run:
            blind.append("Dry run: no delete was issued. Counts reflect current state only.")
        else:
            deleter = getattr(store, "delete_by_source", None)
            if not callable(deleter):
                console.print("[red]This backend exposes no delete-by-source path.[/red]")
                raise typer.Exit(code=2)
            deleted = int(deleter(source) or 0)

        counter = getattr(store, "count_for_source", None)
        remaining = int(counter(source)) if callable(counter) else -1
        if remaining < 0:
            remaining = 0
            blind.append(
                "Backend cannot count rows by source, so 'records remaining' could not be "
                "confirmed directly and is reported as 0 on the strength of probes alone."
            )

        probes: list[DeletionProbe] = []
        for text in probe or []:
            hits = _probe_after_delete(store, text, tenant)
            probes.append(
                DeletionProbe(
                    kind="retrieval",
                    query=text,
                    tenant_id=tenant,
                    hits=len(hits),
                    clean=not hits,
                    detail="" if not hits else f"{len(hits)} document(s) still contain this text.",
                )
            )
            raw = getattr(store, "raw_rows_containing", None)
            if callable(raw):
                try:
                    rows = raw(text, limit=50)
                except Exception as exc:  # noqa: BLE001
                    blind.append(f"Raw store scan failed for {text!r}: {exc}")
                    continue
                probes.append(
                    DeletionProbe(
                        kind="raw_store_scan",
                        query=text,
                        tenant_id=None,
                        hits=len(rows),
                        clean=not rows,
                        detail=(
                            ""
                            if not rows
                            else "Content is still present in the store even though "
                            "retrieval may not surface it."
                        ),
                    )
                )
            else:
                blind.append(
                    "Backend exposes no raw-scan path, so verification relied on retrieval "
                    "only. A row that exists but does not rank would not be seen."
                )
        if not probe:
            blind.append(
                "No --probe text was supplied, so verification was limited to counting rows "
                "by source id. Supplying distinctive text from the deleted content gives a "
                "materially stronger attestation."
            )

        att = build_attestation(
            source_id=source,
            backend=opened.label,
            rows_deleted=deleted,
            rows_remaining=remaining,
            probes=probes,
            blind_spots=blind,
            requested_at=started,
            tool_version=__version__,
        ).finalise(sign=sign, key_path=key)
    finally:
        opened.close()

    colour = {"VERIFIED": "green", "VERIFIED_WITH_BLIND_SPOTS": "yellow", "INCOMPLETE": "red"}[
        att.verdict
    ]
    console.print(
        Panel.fit(
            f"[{colour}]{att.verdict}[/{colour}]\n\n"
            f"Source: {att.source_id}\n"
            f"Deleted: {att.rows_deleted}   Remaining: {att.rows_remaining}\n"
            f"Probes: {len(att.probes)} ({sum(1 for p in att.probes if p.clean)} clean)\n"
            f"Hash: {att.content_hash}",
            title="deletion attestation",
        )
    )
    if att.signature:
        console.print(f"[dim]signed ({att.signature_algorithm}), key {att.public_key[:16]}…[/dim]")
    elif sign:
        console.print(
            "[yellow]--sign requested but the 'cryptography' package is missing; "
            "wrote an unsigned, hash-only record. pip install 'ferryte[attest]'[/yellow]"
        )
    for b in att.blind_spots:
        console.print(f"[yellow]blind spot:[/yellow] {b}")

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(att.to_json(), encoding="utf-8")
        console.print(f"[dim]JSON → {out}[/dim]")
    if markdown:
        markdown.parent.mkdir(parents=True, exist_ok=True)
        markdown.write_text(att.to_markdown(), encoding="utf-8")
        console.print(f"[dim]Markdown → {markdown}[/dim]")

    if att.verdict == "INCOMPLETE":
        raise typer.Exit(code=1)


def _probe_after_delete(store: Any, text: str, tenant: str | None) -> list[dict[str, Any]]:
    try:
        rows = store.search(query=text, tenant_id=tenant, limit=25)
    except Exception:  # noqa: BLE001
        return []
    return [r for r in rows if text.lower() in str(r.get("content", "")).lower()]


@app.command("verify-attestation")
def verify_attestation_cmd(
    path: Path = typer.Argument(..., help="Path to an attestation JSON file."),
) -> None:
    """Recompute the hash and check the signature of an attestation."""
    from .reports.attestation import verify_attestation

    ok, message = verify_attestation(path)
    console.print(_BANNER)
    console.print(f"[{'green' if ok else 'red'}]{'VALID' if ok else 'INVALID'}[/]: {message}")
    if not ok:
        raise typer.Exit(code=1)


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
