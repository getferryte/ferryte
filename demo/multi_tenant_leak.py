"""multi_tenant_leak.py — the 30-second X demo.

Two tenants share an agent on top of an agent-memory backend. The "user" of
tenant ``acme`` confides a secret, then asks the platform to forget it.
The platform calls the backend's official delete API. The agent answers a
follow-up — and still leaks the secret, because a derived summary absorbed it.

That is the exact failure AWS Bedrock AgentCore and Zep document in their
own docs. Ferryte catches it.

Run:

    python demo/multi_tenant_leak.py

The script:
  1) prints a "before" trace of the leak with no instrumentation
  2) turns on Ferryte and re-runs the scenario suite
  3) prints the findings + the report path

It uses the bundled ``InMemoryVectorStore`` so it requires zero external
services or API keys. Real Mem0 / pgvector behave the same way — swap the
adapter and the demo is identical.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Use a throwaway state dir so repeated runs do not accumulate.
_STATE = Path(tempfile.mkdtemp(prefix="ferryte-demo-"))
os.environ["FERRYTE_STATE_DIR"] = str(_STATE)

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402

import ferryte  # noqa: E402
from ferryte.adapters.vector import InMemoryVectorStore  # noqa: E402
from ferryte.instrument import current_instrumentation  # noqa: E402
from ferryte.lineage import get_lineage  # noqa: E402
from ferryte.oracle.runner import run_scenarios  # noqa: E402
from ferryte.reports import (  # noqa: E402
    build_coverage_report,
    render_results_table,
    write_html_report,
    write_json_report,
)


console = Console()


def naive_agent_answer(store: InMemoryVectorStore, *, tenant_id: str, question: str) -> str:
    """A deliberately dumb agent that just splats the top retrieved memory.

    Real agents do prompt-engineering on top of this — but if the leaky memory
    is in retrieval, it almost always ends up in the prompt and then the answer.
    """
    hits = store.search(query=question, tenant_id=tenant_id, limit=3)
    if not hits:
        return "(no memory found)"
    top = hits[0][0]
    return f"Based on what I remember: {top.content}"


def act_one_before_ferryte() -> None:
    console.rule("[bold]Act 1[/bold]  ·  no Ferryte installed — the leak is silent")
    store = InMemoryVectorStore(leak_summaries=True)
    store.add(
        content="the launch code is ORION-DELTA-77",
        source_id="acme-doc-1",
        tenant_id="acme",
    )
    store.add(
        content="quarterly target is 2.3M",
        source_id="acme-doc-2",
        tenant_id="acme",
    )
    store.add(
        content="server credentials rotate weekly",
        source_id="globex-doc-1",
        tenant_id="globex",
    )

    deleted = store.delete_by_source("acme-doc-1")
    console.print(
        f"  [yellow]→ delete_by_source('acme-doc-1') deleted {deleted} primary record(s).[/yellow]"
    )
    answer = naive_agent_answer(
        store, tenant_id="acme", question="What was the launch code?"
    )
    console.print(
        Panel.fit(
            f"[bold]agent answer (tenant=acme, AFTER delete):[/bold]\n{answer}",
            title="leak",
            border_style="red",
        )
    )
    console.print(
        "  [red]The launch code is still in retrieval, hiding inside the per-tenant summary.[/red]"
    )
    console.print(
        "  [red]Source data was 'deleted' but the agent still acts on it. "
        "No tool currently catches this in CI.[/red]\n"
    )


def act_two_with_ferryte() -> int:
    console.rule("[bold]Act 2[/bold]  ·  Ferryte on — same backend, same code, but tested")
    ferryte.instrument()
    InMemoryVectorStore(leak_summaries=True)
    handle = current_instrumentation()
    assert handle is not None
    console.print(
        f"  [green]instrumented[/green]: {len(handle.list_clients())} memory client(s) detected"
    )

    results = run_scenarios(
        instrumentation=handle,
        names=["source-revocation", "cross-tenant-isolation", "memory-poisoning"],
    )
    render_results_table(results, console)
    report = build_coverage_report(
        instrumentation=handle, lineage=get_lineage(), results=results
    )
    out = _STATE / "reports"
    write_json_report(path=out / "latest.json", report=report, results=results)
    write_html_report(path=out / "latest.html", report=report, results=results)

    console.print(
        Panel.fit(
            f"json report: [bold]{out / 'latest.json'}[/bold]\n"
            f"html report: [bold]{out / 'latest.html'}[/bold]",
            title="report",
            border_style="green",
        )
    )

    fails = sum(1 for r in results if r.severity.value == "fail")
    return 1 if fails else 0


def main() -> int:
    console.print(
        Panel.fit(
            "[bold]Ferryte demo[/bold] — multi-tenant agent memory leak\n"
            "Two tenants, one agent. Acme writes a secret, then deletes it.\n"
            "The agent still leaks it. Ferryte catches it.",
            border_style="cyan",
        )
    )
    act_one_before_ferryte()
    exit_code = act_two_with_ferryte()
    console.print(
        "\n[bold]Takeaway:[/bold] deletion APIs are fire-and-forget. "
        "Derived memories outlive their sources. "
        "Without a forgetting oracle, you find out from a customer."
    )
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
