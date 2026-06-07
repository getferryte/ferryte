"""The Forgetting Report — matrix runner.

Runs the backend x scenario matrix and emits results.json + a readable table.

    python -m benchmark.run --backends inmemory,qdrant,chroma --scenarios all
    python -m benchmark.run --backends qdrant --embedder openai --summarizer openai

Embedder/summarizer default to the dependency-free stubs so the harness runs in
CI; pass `--embedder openai --summarizer openai` (with OPENAI_API_KEY set) for a
real, publishable run.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

import ferryte
from ferryte.config import FerryteConfig
from ferryte.lineage.graph import reset_lineage_for_tests
from ferryte.oracle import run_scenarios

from .adapter import SummaryMemoryAdapter
from .memory import ConcatSummarizer, OpenAISummarizer, SummaryMemory
from .stores import HashEmbedder, InMemoryVS, OpenAIEmbedder

ALL_SCENARIOS = [
    "source-revocation",
    "cross-tenant-isolation",
    "stale-fact",
    "memory-poisoning",
]


def load_env(path: str | None = None) -> None:
    """Minimal .env loader (no extra dependency). Existing env vars win."""
    path = path or os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(path):
        return
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def _store_factory(name: str) -> Callable[[], Any]:
    if name == "inmemory":
        return InMemoryVS
    if name == "chroma":
        from .backends import ChromaVS

        return ChromaVS
    if name == "qdrant":
        from .backends import QdrantVS

        return QdrantVS
    if name == "lancedb":
        from .backends import LanceDBVS

        return LanceDBVS
    if name == "pinecone":
        from .backends import PineconeVS

        return PineconeVS
    if name == "pgvector":
        from .backends import PgvectorVS  # type: ignore[attr-defined]

        dsn = os.environ.get("PGVECTOR_DSN", "postgresql://ferryte:ferryte@localhost:5432/ferryte")
        return lambda: PgvectorVS(dsn=dsn)
    raise ValueError(f"unknown backend: {name}")


def _make_embedder(kind: str):
    return OpenAIEmbedder() if kind == "openai" else HashEmbedder()


def _make_summarizer(kind: str):
    return OpenAISummarizer() if kind == "openai" else ConcatSummarizer()


NATIVE_BACKENDS = {"agentcore", "mem0", "zep"}


def _build_native(backend: str):
    """Native frameworks tested through their own write/delete APIs (not the
    shared SummaryMemory layer)."""
    if backend == "agentcore":
        from .agentcore import AgentCoreAdapter, AgentCoreMemory

        return AgentCoreMemory(), AgentCoreAdapter()
    if backend == "mem0":
        from .mem0_backend import build_mem0

        return build_mem0()
    if backend == "zep":
        from .zep_backend import build_zep

        return build_zep()
    raise ValueError(f"unknown native backend: {backend}")


def run_backend(
    backend: str,
    *,
    scenarios: list[str],
    embedder_kind: str,
    summarizer_kind: str,
    count: int,
    with_ferryte: bool = False,
) -> dict[str, Any]:
    """Run one backend. ``with_ferryte=False`` is the naive baseline (raw delete only);
    ``with_ferryte=True`` enables the lineage-driven cascade delete that Ferryte
    provides, so the report can show Before vs After per backend."""
    ferryte.uninstrument()
    # Isolate each backend run in its own fresh lineage DB. Canary source_ids are
    # deterministic, so a shared/persistent lineage would accumulate stale artifact
    # ids from previous runs and corrupt the cascade. One temp state dir per run.
    reset_lineage_for_tests()
    bench_cfg = FerryteConfig(state_dir=Path(tempfile.mkdtemp(prefix=f"ferryte_bench_{backend}_")))
    if backend in NATIVE_BACKENDS:
        client, adapter = _build_native(backend)
        # Native adapters check this attribute to decide whether to cascade.
        if hasattr(adapter, "cascade_derived"):
            adapter.cascade_derived = bool(with_ferryte)  # type: ignore[attr-defined]
    else:
        adapter = SummaryMemoryAdapter()
        client = SummaryMemory(
            store=_store_factory(backend)(),
            embedder=_make_embedder(embedder_kind),
            summarizer=_make_summarizer(summarizer_kind),
            # leak_summaries=True is the naive baseline; flipping it models the
            # lineage cascade that Ferryte gives you for free.
            leak_summaries=not with_ferryte,
        )
    inst = ferryte.instrument(config=bench_cfg, adapters=[adapter])
    inst.track(client, adapter)
    results = run_scenarios(instrumentation=inst, names=scenarios, options={"count": count})
    cells = {
        r.scenario: {"severity": r.severity.value, "findings": len(r.findings)} for r in results
    }
    passed = sum(1 for r in results if r.severity.value == "pass")
    return {"cells": cells, "score": round(100.0 * passed / max(len(results), 1), 1)}


def main() -> None:
    load_env()
    ap = argparse.ArgumentParser(description="The Forgetting Report benchmark runner")
    ap.add_argument("--backends", default="inmemory,qdrant,chroma,pgvector")
    ap.add_argument("--scenarios", default="all")
    ap.add_argument("--embedder", default="hash", choices=["hash", "openai"])
    ap.add_argument("--summarizer", default="concat", choices=["concat", "openai"])
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument(
        "--with-ferryte",
        action="store_true",
        help="Enable Ferryte's lineage-driven cascade delete (the 'after' column).",
    )
    ap.add_argument("--out", default="benchmark/results.json")
    args = ap.parse_args()

    backends = [b.strip() for b in args.backends.split(",") if b.strip()]
    scenarios = ALL_SCENARIOS if args.scenarios == "all" else args.scenarios.split(",")

    matrix: dict[str, Any] = {}
    for b in backends:
        try:
            matrix[b] = run_backend(
                b,
                scenarios=scenarios,
                embedder_kind=args.embedder,
                summarizer_kind=args.summarizer,
                count=args.count,
                with_ferryte=args.with_ferryte,
            )
        except Exception as exc:  # noqa: BLE001
            matrix[b] = {"error": f"{type(exc).__name__}: {exc}", "cells": {}, "score": None}

    report = {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "embedder": args.embedder,
        "summarizer": args.summarizer,
        "scenarios": scenarios,
        "matrix": matrix,
    }
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)

    _print_table(scenarios, matrix)
    print(f"\nWrote {args.out}")


def _glyph(sev: str | None) -> str:
    return {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}.get(sev or "", " -  ")


def _print_table(scenarios: list[str], matrix: dict[str, Any]) -> None:
    short = {s: s.split("-")[0][:8] for s in scenarios}
    header = f"{'backend':10} " + " ".join(f"{short[s]:>8}" for s in scenarios) + f"{'score':>8}"
    print("\n" + header)
    print("-" * len(header))
    for b, data in matrix.items():
        if data.get("error"):
            print(f"{b:10} {data['error']}")
            continue
        cells = data["cells"]
        row = f"{b:10} " + " ".join(f"{_glyph(cells.get(s, {}).get('severity')):>8}" for s in scenarios)
        print(row + f"{str(data['score']) + '%':>8}")


if __name__ == "__main__":
    main()
