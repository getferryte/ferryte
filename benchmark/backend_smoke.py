"""Run the source-revocation scenario against each available real store
(Qdrant in-memory, Chroma embedded) with the deterministic embedder — no
Docker, no API key. Proves real DB backends reproduce the derived-memory leak.

    python -m benchmark.backend_smoke
"""

from __future__ import annotations

import ferryte
from benchmark.adapter import SummaryMemoryAdapter
from benchmark.memory import SummaryMemory
from benchmark.stores import HashEmbedder, InMemoryVS
from ferryte.oracle import run_scenarios


def _build_stores():
    stores: list[tuple[str, object]] = [("inmemory", InMemoryVS())]
    try:
        from benchmark.backends import QdrantVS

        stores.append(("qdrant", QdrantVS()))
    except Exception as exc:  # noqa: BLE001
        print(f"  (qdrant skipped: {type(exc).__name__}: {exc})")
    try:
        from benchmark.backends import ChromaVS

        stores.append(("chroma", ChromaVS()))
    except Exception as exc:  # noqa: BLE001
        print(f"  (chroma skipped: {type(exc).__name__}: {exc})")
    return stores


def run_against(store) -> object:
    ferryte.uninstrument()
    adapter = SummaryMemoryAdapter()
    inst = ferryte.instrument(adapters=[adapter])
    mem = SummaryMemory(store=store, embedder=HashEmbedder(), leak_summaries=True)
    inst.track(mem, adapter)
    return run_scenarios(
        instrumentation=inst, names=["source-revocation"], options={"count": 3}
    )[0]


if __name__ == "__main__":
    print("Forgetting backend smoke — source-revocation, naive app, real stores\n")
    for label, store in _build_stores():
        r = run_against(store)
        verdict = r.severity.value.upper()
        flag = "LEAK CAUGHT" if verdict == "FAIL" else "no leak"
        print(f"  {label:9} -> {verdict:4} | {len(r.findings)} findings | {flag}")
    print("\nExpected: every store -> FAIL (the summary leak survives a hard row delete).")
