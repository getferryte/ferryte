"""Mem0 forgetting scalp — reproducible, self-contained proof.

Demonstrates the *strong* version of the leak (no constructed baseline):

  1. A user tells the agent a secret (a high-entropy marker) in one message.
  2. Mem0's LLM extracts memories from it; we record every memory id Mem0
     returns for that write — this is everything a careful app could know to
     delete in order to "forget the source".
  3. The user adds a few more related (non-secret) facts, so Mem0's extractor
     consolidates / updates memories the way it does in real use.
  4. The app "forgets the source": it deletes *every memory id Mem0 returned
     for the secret-bearing write* via Mem0's own delete() API.
  5. We re-query. If the secret marker still surfaces, the source was deleted
     but the information survived — a forgetting leak. We print the literal
     surviving memory text as proof.

Run N times to measure how often it leaks (LLM extraction varies even at
temperature=0).

    python -m benchmark.mem0_scalp --runs 10

Needs OPENAI_API_KEY (read from benchmark/.env or the environment). Runs Qdrant
fully embedded (a temp dir) — no Docker, no server.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any


def _load_openai_key() -> None:
    if os.environ.get("OPENAI_API_KEY"):
        return
    env = Path(__file__).with_name(".env")
    if not env.exists():
        return
    for raw in env.read_text().splitlines():
        line = raw.strip()
        if line.startswith("OPENAI_API_KEY=") and "=" in line:
            os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
            return


def _build_memory(
    *, model: str = "gpt-4o-mini", embed_model: str = "text-embedding-3-small"
) -> Any:
    from mem0 import Memory

    cfg = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "path": tempfile.mkdtemp(prefix="mem0_scalp_"),
                "collection_name": f"scalp_{uuid.uuid4().hex[:8]}",
            },
        },
        "llm": {"provider": "openai", "config": {"model": model, "temperature": 0}},
        "embedder": {"provider": "openai", "config": {"model": embed_model}},
    }
    return Memory.from_config(cfg)


def _ids_and_text(add_result: Any) -> list[tuple[str, str]]:
    """Extract (id, memory_text) pairs from a mem0 add()/search() result."""
    out: list[tuple[str, str]] = []
    items = add_result.get("results") if isinstance(add_result, dict) else add_result
    for r in items or []:
        if isinstance(r, dict) and r.get("id"):
            out.append((str(r["id"]), str(r.get("memory") or r.get("text") or "")))
    return out


def one_run(*, marker: str, verbose: bool = False) -> dict[str, Any]:
    m = _build_memory()
    user = "alice"

    secret = (
        f"Please remember this for me: the Project Orion master launch code is "
        f"{marker}. It is highly confidential."
    )
    # 1-2) write the secret; record every memory id Mem0 creates for this write
    add_res = m.add(messages=[{"role": "user", "content": secret}], user_id=user)
    secret_ids = [i for i, _ in _ids_and_text(add_res)]

    # 3) add related, non-secret context so Mem0 consolidates/updates memories
    for ctx in (
        "Project Orion is scheduled to launch in Q3.",
        "The Project Orion team lead is Dana.",
        "Project Orion uses the staging cluster for rehearsals.",
    ):
        m.add(messages=[{"role": "user", "content": ctx}], user_id=user)

    # confirm the secret is retrievable before deletion
    pre = m.search("What is the Project Orion launch code?", filters={"user_id": user}, limit=10)
    pre_pairs = _ids_and_text(pre)
    present_before = any(marker in t for _, t in pre_pairs)

    # 4) "forget the source": delete every memory id Mem0 gave us for the secret write
    for mid in secret_ids:
        try:
            m.delete(memory_id=mid)
        except Exception:  # noqa: BLE001 - already gone is fine
            pass

    # 5) re-query and look for the surviving secret
    post = m.search("What is the Project Orion launch code?", filters={"user_id": user}, limit=10)
    post_pairs = _ids_and_text(post)
    survivors = [(i, t) for i, t in post_pairs if marker in t]
    leaked = bool(survivors)

    if verbose:
        print(f"  marker: {marker}")
        print(f"  memory ids Mem0 returned for the secret write: {secret_ids}")
        print(f"  retrievable before delete: {present_before}")
        print(f"  deleted {len(secret_ids)} source memory id(s)")
        if leaked:
            for i, t in survivors:
                print(f"  >> LEAK: secret survives in memory {i}: {t!r}")
        else:
            print("  clean: secret no longer retrievable")

    return {
        "marker": marker,
        "secret_ids": secret_ids,
        "present_before": present_before,
        "leaked": leaked,
        "survivors": survivors,
    }


def main() -> None:
    _load_openai_key()
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set (env or benchmark/.env).")

    ap = argparse.ArgumentParser(description="Mem0 forgetting scalp")
    ap.add_argument("--runs", type=int, default=10)
    args = ap.parse_args()

    print(f"Mem0 forgetting scalp — {args.runs} run(s)\n")
    leaked = 0
    valid = 0
    transcripts: list[dict[str, Any]] = []
    for n in range(args.runs):
        marker = f"ZEBRA-{uuid.uuid4().hex[:6].upper()}"
        print(f"run {n + 1}/{args.runs}")
        res = one_run(marker=marker, verbose=True)
        print()
        if not res["present_before"]:
            print("  (skipped: secret was not retrievable before delete — extraction miss)\n")
            continue
        valid += 1
        leaked += 1 if res["leaked"] else 0
        transcripts.append(res)

    print("=" * 60)
    if valid:
        print(f"LEAK RATE: {leaked}/{valid} runs leaked the secret after source deletion")
        print(f"           ({100.0 * leaked / valid:.0f}% of runs where the secret was first stored)")
    else:
        print("No valid runs (Mem0 never stored the secret before deletion).")

    out = Path(__file__).with_name("_mem0_scalp_evidence.json")
    out.write_text(json.dumps(transcripts, indent=2))
    print(f"\nEvidence written to {out}")


if __name__ == "__main__":
    main()
