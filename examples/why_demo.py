"""`ferryte why` end-to-end demo — the exact scenario on the homepage.

Runs a real, self-contained agent-memory bug and shows Ferryte tracing a wrong
answer back to the stale memory that caused it. Nothing is mocked: it uses the
shipped in-memory vector store, real instrumentation, the real lineage graph, and
the real attribution engine.

Run it::

    python examples/why_demo.py

It seeds a fresh lineage DB under ``examples/.ferryte-why-demo`` and prints the
attribution. To reproduce the CLI verbatim afterwards::

    FERRYTE_STATE_DIR=examples/.ferryte-why-demo \\
        ferryte why "Legacy Free plan" \\
        --query "what plan is this customer on?" --tenant acme
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

# Point Ferryte at a demo-local state dir *before* importing the package so the
# CLI (run afterwards with the same FERRYTE_STATE_DIR) reads the same DB.
STATE_DIR = Path(__file__).parent / ".ferryte-why-demo"
if STATE_DIR.exists():
    shutil.rmtree(STATE_DIR)
os.environ["FERRYTE_STATE_DIR"] = str(STATE_DIR)

import ferryte  # noqa: E402
from ferryte.adapters.vector import InMemoryVectorStore  # noqa: E402
from ferryte.oracle.attribute import attribute_answer  # noqa: E402
from ferryte.oracle.replay import replay_query  # noqa: E402


def main() -> None:
    # One line — auto-patches the memory client so every write/read is captured.
    ferryte.instrument()

    # A support agent's memory of one customer. Don't leak the app-summary noise
    # into this teaching demo — we want the two raw facts to be the story.
    mem = InMemoryVectorStore(leak_summaries=False)

    # April: a support ticket teaches the agent the customer is on the free plan.
    with ferryte.tag(source_id="zendesk-ticket-8821", tenant_id="acme"):
        mem.add(
            content="Customer acme is on the Legacy Free plan.",
            source_id="zendesk-ticket-8821",
            tenant_id="acme",
        )

    # June: the customer upgrades; a billing sync writes the fresh fact. The old
    # fact is never removed — it just stops being true.
    with ferryte.tag(source_id="billing-sync-0601", tenant_id="acme"):
        mem.add(
            content="Customer acme upgraded to the Pro plan.",
            source_id="billing-sync-0601",
            tenant_id="acme",
        )

    # The agent answers a question. Retrieval pulls memories into context — the
    # instrumented search records exactly what reached the prompt.
    question = "what plan is this customer on?"
    retrieved = mem.search(query=question, tenant_id="acme", limit=5)

    # The agent replied with the stale fact. Optional (one extra line per turn):
    # record the answer + its context, and `why` becomes exact, not inferred.
    bad_answer = "You're on the Legacy Free plan."
    ferryte.record_answer(
        answer_id="turn-0001",
        content=bad_answer,
        query=question,
        tenant_id="acme",
        artifact_ids=[item.artifact_id for item, _score in retrieved],
    )

    # Now: which memory caused that answer?
    result = attribute_answer(
        bad_answer, query=question, tenant_id="acme", limit=5
    )

    print(f'\nagent answered:  "{bad_answer}"')
    print(f"attributed to {len(result.candidates)} candidate memory(ies):\n")
    for i, c in enumerate(result.candidates, 1):
        print(f"  #{i}  {c.artifact_id[:8]}  conf={c.score:.2f}  {c.method}")
        print(f"      belief: {c.content}")
        for s in c.sources:
            rev = "  ← REVOKED" if s.get("revoked_at") else ""
            print(f"      from: {s['source_id']}{rev}")
        print(f"      retrieved into context: {c.retrieved} ({c.retrieval_count}x)")
        print(f"      diagnosis: {', '.join(c.diagnoses)}\n")

    top = result.top
    if top:
        print(f"root cause: {top.artifact_id[:8]} — {', '.join(top.diagnoses)}")

        # Counterfactual replay (ContextCite-style, at the retrieval layer):
        # ablate the suspect and show what the agent's context becomes without it.
        replay = replay_query(question, top.artifact_id, tenant_id="acme", limit=1)
        if replay.causal and replay.replacement is not None:
            print(
                f"\ncounterfactual: without {top.artifact_id[:8]}, the top of context becomes:\n"
                f'  "{replay.replacement.content}"'
            )

    print(
        "\nreproduce via CLI:\n"
        f'  FERRYTE_STATE_DIR={STATE_DIR} ferryte why "Legacy Free plan" '
        '--query "what plan is this customer on?" --tenant acme\n'
        "(--replay also works when your app module is loaded in-process via --module)\n"
    )


if __name__ == "__main__":
    main()
