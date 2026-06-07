"""Mem0 native backend for the benchmark.

Mem0 is a real agent-memory framework: it runs its own LLM fact-extraction on
every write and stores derived memories in a vector DB. We test it through its
OWN write/delete APIs (not the shared SummaryMemory layer), and we instrument it
with the *shipped* `ferryte.adapters.mem0.Mem0Adapter` — i.e. the benchmark
dogfoods the exact adapter our users would use.

`Mem0Client` is a thin shim that exposes the legacy-style surface the adapter
expects (`search(query, user_id=...)`, `delete(memory_id=...)`) while calling the
current mem0 2.x API underneath (which moved `user_id` into `filters=`).

Needs OPENAI_API_KEY and the Qdrant container (docker-compose) on :6333.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from typing import Any


class Mem0Client:
    def __init__(
        self,
        *,
        model: str = "gpt-4o-mini",
        embed_model: str = "text-embedding-3-small",
        qdrant_url: str | None = None,
    ) -> None:
        from mem0 import Memory  # noqa: PLC0415 - lazy optional dep

        collection = f"mem0_bench_{uuid.uuid4().hex[:8]}"
        # A non-empty QDRANT_URL targets a real Qdrant server (the publishable run).
        # When it's empty/unset we fall back to qdrant's embedded local mode (a temp
        # path) so the Mem0 benchmark runs with NO Docker — same spirit as the
        # generic vector backends' ":memory:" mode.
        url = qdrant_url or os.environ.get("QDRANT_URL", "").strip()
        if url:
            host = url.split("://", 1)[-1].split(":")[0]
            port = int(url.rsplit(":", 1)[-1]) if url.rsplit(":", 1)[-1].isdigit() else 6333
            qdrant_cfg: dict[str, Any] = {"host": host, "port": port, "collection_name": collection}
        else:
            qdrant_cfg = {
                "path": tempfile.mkdtemp(prefix="mem0_qdrant_"),
                "collection_name": collection,
            }
        cfg = {
            "vector_store": {"provider": "qdrant", "config": qdrant_cfg},
            # temperature=0 for the most reproducible fact-extraction we can get
            # from a live LLM (the benchmark still notes LLM variance honestly).
            "llm": {"provider": "openai", "config": {"model": model, "temperature": 0}},
            "embedder": {"provider": "openai", "config": {"model": embed_model}},
        }
        self._m = Memory.from_config(cfg)

    def add(
        self,
        messages: Any = None,
        *,
        content: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        # Force the caller (the runner) onto the messages+user_id path: without a
        # user_id Mem0 can't scope the memory and the scenario would be meaningless.
        if user_id is None:
            raise TypeError("Mem0Client.add requires user_id")
        if messages is None:
            messages = [{"role": "user", "content": content or ""}]
        return self._m.add(messages=messages, user_id=user_id, metadata=metadata or {})

    def search(self, query: str, *, user_id: str | None = None, limit: int = 5, **_: Any) -> Any:
        filters = {"user_id": user_id} if user_id else None
        return self._m.search(query, filters=filters, limit=limit)

    def delete(self, *, memory_id: str | None = None, **_: Any) -> Any:
        return self._m.delete(memory_id=memory_id)

    def delete_all(self, *, user_id: str | None = None, **_: Any) -> Any:
        return self._m.delete_all(user_id=user_id)


def build_mem0():
    """Return (client, adapter) using the shipped ferryte Mem0 adapter."""
    from ferryte.adapters.mem0 import Mem0Adapter

    return Mem0Client(), Mem0Adapter()
