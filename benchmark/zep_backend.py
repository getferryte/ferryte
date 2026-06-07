"""Zep Cloud backend for The Forgetting Report + Ferryte's Zep adapter.

The system-under-test is a real Zep Cloud knowledge graph. We write each canary
as a graph **episode** (``graph.add``); Zep extracts derived **edges/nodes**
(facts) from it. The benchmark then revokes the source (delete the episode) and
probes whether the derived facts still surface the canary — the documented
temporal-graph leak.

Requires ``zep-cloud`` and a live ``ZEP_API_KEY``. Like the Mem0 backend skips
itself without ``mem0ai``, this raises a clear error when the key is absent so
the matrix simply reports it as unavailable rather than failing silently.

NOTE: this live path is pending validation against a Zep Cloud account; the
adapter logic itself is covered by ``tests/test_instrument_zep.py`` against a
faithful in-process fake. The leaderboard keeps Zep as "pending" until a live run.
"""

from __future__ import annotations

import os
import time
from typing import Any

from ferryte.adapters.zep import ZepAdapter, _MARKER_RE, _iter_facts


class ZepClient:
    """Flat system-under-test surface (add/search) over Zep Cloud's graph API.

    Exposes ``.graph`` (the real zep_cloud graph) so the ZepAdapter patches the
    same object the live client extracts facts into."""

    def __init__(
        self, *, api_key: str | None = None, extraction_timeout_s: float = 90.0
    ) -> None:
        from zep_cloud.client import Zep  # noqa: PLC0415 - lazy optional dep

        self._zep = Zep(api_key=api_key or os.environ["ZEP_API_KEY"])
        self.graph = self._zep.graph
        self._users: set[str] = set()
        self._extraction_timeout_s = extraction_timeout_s

    def _ensure_user(self, user_id: str) -> None:
        if user_id in self._users:
            return
        self._users.add(user_id)
        try:
            self._zep.user.add(user_id=user_id)
        except Exception:  # noqa: BLE001 - already-exists / API drift is non-fatal here
            pass

    def add(
        self,
        content: str | None = None,
        *,
        tenant_id: str | None = None,
        source_id: str | None = None,  # consumed via ferryte.tag context
        messages: list[dict[str, Any]] | None = None,
        user_id: str | None = None,
        **_: Any,
    ) -> Any:
        uid = tenant_id or user_id or "default"
        self._ensure_user(uid)
        data = content if content is not None else _messages_to_text(messages)
        result = self.graph.add(user_id=uid, type="text", data=data)
        # Zep extraction is async: block until the canary marker actually shows up
        # as a derived graph fact, so the delete-after-revoke test isn't racing the
        # extraction pipeline. Times out honestly (caller will see no leak vs BLIND).
        self._await_extraction(data=data, user_id=uid)
        return result

    def _await_extraction(self, *, data: str, user_id: str) -> bool:
        markers = _MARKER_RE.findall(data or "")
        if not markers:
            time.sleep(3)
            return True
        deadline = time.time() + self._extraction_timeout_s
        while time.time() < deadline:
            for scope in ("edges", "nodes"):
                try:
                    res = self.graph.search(query=data, user_id=user_id, scope=scope, limit=10)
                except Exception:  # noqa: BLE001 - transient; keep polling
                    res = None
                if any(m in f["text"] for f in _iter_facts(res) for m in markers):
                    return True
            time.sleep(5)
        # Honest BLIND: we planted the canary but Zep never surfaced it as a derived
        # fact within the window, so the delete-after-revoke test is inconclusive for
        # this fact. Record it rather than letting the probe trivially "pass".
        try:
            from ferryte.lineage import get_lineage  # noqa: PLC0415

            get_lineage().record_blindspot(
                backend="zep",
                kind="extraction_timeout",
                detail=(
                    f"Zep did not surface canary {markers!r} as a derived graph fact within "
                    f"{self._extraction_timeout_s:.0f}s (graph extraction is async/selective); "
                    "the forgetting test is inconclusive for this fact."
                ),
            )
        except Exception:  # noqa: BLE001 - never break the run on instrumentation
            pass
        return False

    def search(
        self,
        query: str | None = None,
        *,
        user_id: str | None = None,
        tenant_id: str | None = None,
        limit: int = 5,
        **_: Any,
    ) -> Any:
        return self.graph.search(
            query=query or "", user_id=user_id or tenant_id, scope="edges", limit=limit
        )


def _messages_to_text(messages: list[dict[str, Any]] | None) -> str:
    if not messages:
        return ""
    return " | ".join(str(m.get("content", "")) for m in messages)


def build_zep() -> tuple[ZepClient, ZepAdapter]:
    if not os.environ.get("ZEP_API_KEY"):
        raise RuntimeError(
            "ZEP_API_KEY not set — the Zep benchmark needs a live Zep Cloud key. "
            "The Zep adapter logic is covered by tests/test_instrument_zep.py."
        )
    return ZepClient(), ZepAdapter()
