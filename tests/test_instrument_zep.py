"""Zep adapter: capture + lineage-driven cascade over a faithful fake graph.

The fake models Zep's documented leak shape: ``graph.add`` stores a raw *episode*
AND extracts a derived *edge* (a graph fact) that absorbs the episode's content.
Deleting the episode leaves the derived edge behind — exactly the temporal-graph
leak Ferryte exists to catch. No live Zep / network is required.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import ferryte
from ferryte.adapters.zep import ZepAdapter
from ferryte.lineage import get_lineage

MARKER = "KILO-VEGA-77"
SENTENCE = f"User acme confidential note: the secret code is {MARKER}. Do not disclose."


class _Episode:
    def __init__(self, content: str) -> None:
        self.uuid_ = str(uuid.uuid4())
        self.content = content


class _Edge:
    def __init__(self, fact: str) -> None:
        self.uuid_ = str(uuid.uuid4())
        self.fact = fact


class _SearchResult:
    def __init__(self, edges: list[_Edge]) -> None:
        self.edges = edges
        self.nodes: list = []


class _DeleteAPI:
    def __init__(self, store: dict) -> None:
        self._store = store

    def delete(self, *, uuid_: str | None = None) -> None:
        if uuid_ not in self._store:
            raise ValueError(f"not found: {uuid_}")
        del self._store[uuid_]


class _Graph:
    """Minimal stand-in for ``zep_cloud`` ``client.graph``."""

    def __init__(self) -> None:
        self.episodes: dict[str, _Episode] = {}
        self.edges: dict[str, _Edge] = {}
        self.episode = _DeleteAPI(self.episodes)
        self.edge = _DeleteAPI(self.edges)
        self.node = _DeleteAPI({})

    def add(self, *, user_id=None, group_id=None, type=None, data="") -> _Episode:
        ep = _Episode(data)
        self.episodes[ep.uuid_] = ep
        # Zep extracts a derived graph fact (edge) that absorbs the episode —
        # this survives episode deletion unless something cascades it.
        edge = _Edge(f"fact: {data}")
        self.edges[edge.uuid_] = edge
        return ep

    def search(self, *, query="", user_id=None, group_id=None, scope="edges", limit=10):
        if scope == "nodes":
            return _SearchResult([])
        toks = [t for t in str(query).lower().split() if t]
        hits = [e for e in self.edges.values() if any(t in e.fact.lower() for t in toks)]
        return _SearchResult(hits[:limit])


class Zep:  # named to exercise instrument's by-class-name adapter pick
    def __init__(self) -> None:
        self.graph = _Graph()


def _seed(client: Zep) -> None:
    with ferryte.tag(source_id="src-zep", tenant_id="acme"):
        client.graph.add(user_id="acme", type="message", data=SENTENCE)


def test_zep_write_is_captured_as_episode(fresh_ferryte: Path) -> None:
    client = Zep()
    ferryte.instrument(clients=[client])
    _seed(client)
    arts = get_lineage().artifacts_for_source("src-zep")
    assert any(MARKER in (a["content"] or "") for a in arts)
    assert any(a.get("kind") == "episode" for a in arts)


def test_zep_baseline_leaks_derived_fact(fresh_ferryte: Path) -> None:
    client = Zep()
    handle = ferryte.instrument(clients=[client])
    adapter = handle.adapter_for(client)
    assert isinstance(adapter, ZepAdapter)
    _seed(client)

    adapter.cascade_derived = False  # naive baseline: revoke episode only
    adapter.delete_source(client, source_id="src-zep", tenant_id="acme")

    hits = adapter.probe(client, query=MARKER, tenant_id="acme")
    assert any(MARKER in h.content for h in hits), "derived graph fact must still leak"


def test_zep_cascade_forgets_derived_fact(fresh_ferryte: Path) -> None:
    client = Zep()
    handle = ferryte.instrument(clients=[client])
    adapter = handle.adapter_for(client)
    _seed(client)

    adapter.cascade_derived = True  # the Ferryte cascade
    adapter.delete_source(client, source_id="src-zep", tenant_id="acme")

    hits = adapter.probe(client, query=MARKER, tenant_id="acme")
    assert not any(MARKER in h.content for h in hits), "cascade must delete the derived fact"
