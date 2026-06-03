"""`ferryte` CLI.

Commands:

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
import sys
from pathlib import Path
from typing import List, Optional

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
    help="Ferryte — verification for agent forgetting.",
)
console = Console()


_BANNER = (
    "[bold]Ferryte[/bold] — verification for agent forgetting "
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
        from .adapters.vector import InMemoryVectorStore

        InMemoryVectorStore()
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
