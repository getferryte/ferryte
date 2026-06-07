"""Smoke test: run real Ferryte scenarios against SummaryMemory on the
in-memory store (no Docker, no API key). Proves the benchmark pipeline and the
leak A/B: a naive app leaks via the derived summary; a good app does not.

    python -m benchmark.smoke
"""

from __future__ import annotations

import ferryte
from benchmark.adapter import SummaryMemoryAdapter
from benchmark.memory import SummaryMemory
from benchmark.stores import HashEmbedder, InMemoryVS
from ferryte.oracle import run_scenarios


def run_once(*, leak: bool, scenario: str = "source-revocation"):
    ferryte.uninstrument()
    adapter = SummaryMemoryAdapter()
    inst = ferryte.instrument(adapters=[adapter])
    mem = SummaryMemory(store=InMemoryVS(), embedder=HashEmbedder(), leak_summaries=leak)
    inst.track(mem, adapter)
    return run_scenarios(instrumentation=inst, names=[scenario], options={"count": 3})[0]


if __name__ == "__main__":
    print("Forgetting smoke test — SummaryMemory on in-memory store\n")
    for leak in (True, False):
        r = run_once(leak=leak)
        label = "naive app (leak_summaries=True)" if leak else "good app  (leak_summaries=False)"
        print(
            f"{label:38} -> {r.severity.value.upper():4} "
            f"| {len(r.findings)} findings | seeded={r.artifacts_seeded} deleted={r.artifacts_deleted}"
        )
        for f in r.findings[:3]:
            print(f"      - [{f.severity.value}] {f.code}: {f.summary[:88]}")
    print("\nExpected: naive -> FAIL (summary leak), good -> PASS.")
