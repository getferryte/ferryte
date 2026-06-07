"""Letta adapter: capture + lineage-driven cascade over a fake archival memory.

The fake models Letta's leak shape: creating an archival passage also distils a
derived *summary passage* that absorbs the fact. Deleting the original passage
leaves the summary behind — the leak Ferryte catches. No live Letta required.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import ferryte
from ferryte.adapters.letta import LettaAdapter
from ferryte.lineage import get_lineage

MARKER = "KILO-VEGA-77"
SENTENCE = f"User acme note: the secret code is {MARKER}. Do not disclose."


class _Passages:
    def __init__(self) -> None:
        self.store: dict[str, dict] = {}

    def create(self, *, agent_id=None, text=""):
        pid = str(uuid.uuid4())
        self.store[pid] = {"id": pid, "text": text, "agent_id": agent_id}
        # Letta distils a derived summary passage that absorbs the fact (the leak)
        sid = str(uuid.uuid4())
        self.store[sid] = {"id": sid, "text": f"summary: {text}", "agent_id": agent_id}
        return {"id": pid}

    def list(self, *, agent_id=None, query="", limit=50):
        items = [v for v in self.store.values() if agent_id in (None, v["agent_id"])]
        if query:
            items = [v for v in items if query.lower() in v["text"].lower()]
        return items[:limit]

    def delete(self, *, agent_id=None, memory_id=None):
        if memory_id not in self.store:
            raise ValueError(f"not found: {memory_id}")
        del self.store[memory_id]


class _Agents:
    def __init__(self) -> None:
        self.passages = _Passages()


class Letta:  # named so instrument's by-shape pick selects the letta adapter
    def __init__(self) -> None:
        self.agents = _Agents()


def _seed(client: Letta) -> None:
    with ferryte.tag(source_id="src-letta", tenant_id="acme"):
        client.agents.passages.create(agent_id="acme", text=SENTENCE)


def test_letta_write_is_captured(fresh_ferryte: Path) -> None:
    client = Letta()
    ferryte.instrument(clients=[client])
    _seed(client)
    arts = get_lineage().artifacts_for_source("src-letta")
    assert any(MARKER in (a["content"] or "") for a in arts)
    assert any(a.get("kind") == "archival_passage" for a in arts)


def test_letta_baseline_leaks_derived_summary(fresh_ferryte: Path) -> None:
    client = Letta()
    handle = ferryte.instrument(clients=[client])
    adapter = handle.adapter_for(client)
    assert isinstance(adapter, LettaAdapter)
    _seed(client)

    adapter.cascade_derived = False
    adapter.delete_source(client, source_id="src-letta", tenant_id="acme")

    hits = adapter.probe(client, query=MARKER, tenant_id="acme")
    assert any(MARKER in h.content for h in hits), "derived summary must still leak"


def test_letta_cascade_forgets_derived_summary(fresh_ferryte: Path) -> None:
    client = Letta()
    handle = ferryte.instrument(clients=[client])
    adapter = handle.adapter_for(client)
    _seed(client)

    adapter.cascade_derived = True
    adapter.delete_source(client, source_id="src-letta", tenant_id="acme")

    hits = adapter.probe(client, query=MARKER, tenant_id="acme")
    assert not any(MARKER in h.content for h in hits), "cascade must delete the derived summary"
