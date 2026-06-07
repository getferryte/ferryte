"""Adapter for Zep / Graphiti (the temporal knowledge-graph memory layer).

Zep is the #2 memory framework the ICP reaches for after Mem0. Its distinctive
shape — and its documented leak surface — is the **temporal knowledge graph**:

  - You ``graph.add(...)`` raw data as an **episode**.
  - Zep asynchronously extracts **graph facts** from that episode: entity **edges**
    (``the secret code is KILO-VEGA-77``) and entity **nodes** (summaries that
    *absorb multiple episodes*).
  - Deleting the source **episode** does **not** delete the derived edges/nodes it
    produced — the fact survives in the graph. That is the exact failure shape
    Ferryte exists to catch (and the reason a shared node summary is dangerous:
    one node can carry facts distilled from many revoked sources).

We import ``zep_cloud`` lazily and tolerate its absence. The adapter is duck-typed
on the v3 client surface (``client.graph.add`` / ``client.graph.search`` plus
``client.graph.episode/edge/node.delete``); a flat client exposing ``add`` /
``search`` / ``delete`` works too, which keeps it testable without a live Zep.

``cascade_derived`` mirrors the other adapters: when False (the naive baseline)
``delete_source`` only revokes the raw episode, so the derived graph facts leak;
when True (the Ferryte default) it also deletes every derived edge/node that still
encodes the revoked source's high-entropy markers — the lineage-driven cascade.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterable
from typing import Any

from ..context import current_context
from ..lineage import get_lineage
from .base import AdapterCapability, BackendKind, RetrievalRecord, WriteRecord

# Canary-style markers (e.g. KILO-VEGA-77, ORION-DELTA-9F2A1B). Used to find the
# derived graph facts that still encode a revoked source during the cascade.
_MARKER_RE = re.compile(r"[A-Z0-9]{2,}(?:-[A-Z0-9]+)+")


class ZepAdapter:
    name: str = "zep"
    backend: BackendKind = BackendKind.ZEP
    capabilities: frozenset[AdapterCapability] = frozenset(
        {
            AdapterCapability.WRITE_CAPTURE,
            AdapterCapability.READ_CAPTURE,
            AdapterCapability.SOURCE_DELETE,
            AdapterCapability.TENANT_SCOPING,
            AdapterCapability.DERIVED_ENUMERATION,
        }
    )

    # See module docstring. True = product default (cascade derived graph facts);
    # the benchmark flips it to False to model the naive baseline that leaks.
    cascade_derived: bool = True

    def patch(self, client: Any) -> Any:
        if getattr(client, "_ferryte_patched", False):
            return client

        graph = getattr(client, "graph", None)
        if graph is None or not hasattr(graph, "add") or not hasattr(graph, "search"):
            get_lineage().record_blindspot(
                backend=self.backend.value,
                kind="incompatible_client",
                detail=(
                    "Zep client missing expected graph.add/graph.search; "
                    "Ferryte could not instrument it."
                ),
            )
            return client

        lineage = get_lineage()
        original_add = graph.add
        original_search = graph.search

        def add(*args: Any, **kwargs: Any) -> Any:
            ctx = current_context()
            sid = kwargs.pop("source_id", None) or ctx.source_id
            tid = kwargs.get("user_id") or kwargs.get("group_id") or ctx.tenant_id
            data = kwargs.get("data") if "data" in kwargs else (args[0] if args else "")
            result = original_add(*args, **kwargs)
            episode_id = _episode_id(result)
            lineage.record_write(
                WriteRecord(
                    backend=self.backend,
                    artifact_id=episode_id,
                    content=_as_text(data),
                    source_id=sid,
                    tenant_id=tid,
                    kind="episode",
                    metadata={"type": kwargs.get("type")},
                )
            )
            return result

        def search(*args: Any, **kwargs: Any) -> Any:
            ctx = current_context()
            query = kwargs.get("query") if "query" in kwargs else (args[0] if args else "")
            tid = kwargs.get("user_id") or kwargs.get("group_id") or ctx.tenant_id
            result = original_search(*args, **kwargs)
            for fact in _iter_facts(result):
                lineage.record_retrieval(
                    RetrievalRecord(
                        backend=self.backend,
                        query=_as_text(query),
                        artifact_id=fact["id"],
                        content=fact["text"],
                        score=fact.get("score"),
                        tenant_id=tid,
                        metadata={"kind": fact["kind"]},
                    )
                )
            return result

        graph.add = add  # type: ignore[assignment]
        graph.search = search  # type: ignore[assignment]
        client._ferryte_patched = True
        client._ferryte_zep_graph = graph
        client._ferryte_zep_originals = {"add": original_add, "search": original_search}
        return client

    def unpatch(self, client: Any) -> None:
        if not getattr(client, "_ferryte_patched", False):
            return
        graph = getattr(client, "_ferryte_zep_graph", None)
        originals = getattr(client, "_ferryte_zep_originals", {})
        if graph is not None:
            if originals.get("add") is not None:
                graph.add = originals["add"]
            if originals.get("search") is not None:
                graph.search = originals["search"]
        client._ferryte_patched = False

    def delete_source(self, client: Any, *, source_id: str, tenant_id: str | None = None) -> int:
        lineage = get_lineage()
        lineage.mark_source_revoked(source_id)

        graph = getattr(client, "_ferryte_zep_graph", None) or getattr(client, "graph", None)
        records = list(lineage.artifacts_for_source(source_id))

        # 1) Revoke the raw episode(s) — what a naive Zep user would do.
        n = self._delete_episodes(graph, [r["artifact_id"] for r in records], lineage)

        # Without the cascade, the derived graph facts/nodes Zep extracted from the
        # episode survive (the documented temporal-graph leak) -> the probe still
        # surfaces the marker -> FAIL. This is the gap Ferryte closes.
        if not getattr(self, "cascade_derived", True):
            return n

        # 2) Cascade: delete every derived edge/node that still encodes one of the
        #    revoked source's high-entropy markers.
        markers = _markers_from(records)
        n += self._cascade_graph(graph, markers=markers, tenant_id=tenant_id, lineage=lineage)
        return n

    def _delete_episodes(self, graph: Any, episode_ids: list[str], lineage: Any) -> int:
        if graph is None:
            return 0
        deleter = _episode_deleter(graph)
        n = 0
        for eid in dict.fromkeys(e for e in episode_ids if e):
            if deleter is None:
                lineage.mark_artifact_deleted(eid)
                n += 1
                continue
            if _try_delete(deleter, eid):
                lineage.mark_artifact_deleted(eid)
                n += 1
            else:
                lineage.record_blindspot(
                    backend=self.backend.value,
                    kind="delete_failed",
                    detail=f"Zep episode delete failed for {eid}",
                )
        return n

    def _cascade_graph(
        self, graph: Any, *, markers: list[str], tenant_id: str | None, lineage: Any
    ) -> int:
        if graph is None or not markers:
            return 0
        edge_del = _component_deleter(graph, "edge")
        node_del = _component_deleter(graph, "node")
        n = 0
        seen: set[str] = set()
        for marker in markers:
            for scope, deleter in (("edges", edge_del), ("nodes", node_del)):
                if deleter is None:
                    continue
                for fact in _iter_facts(_safe_search(graph, marker, tenant_id, scope)):
                    fid = fact["id"]
                    if not fid or fid in seen or marker not in fact["text"]:
                        continue
                    seen.add(fid)
                    if _try_delete(deleter, fid):
                        lineage.mark_artifact_deleted(fid)
                        n += 1
        return n

    def list_artifacts_for_source(
        self, client: Any, *, source_id: str, tenant_id: str | None = None
    ) -> Iterable[WriteRecord]:
        lineage = get_lineage()
        for a in lineage.artifacts_for_source(source_id):
            yield WriteRecord(
                backend=self.backend,
                artifact_id=a["artifact_id"],
                content=a.get("content") or "",
                source_id=source_id,
                tenant_id=a.get("tenant_id"),
                kind=a.get("kind", "episode"),
                metadata=a.get("metadata") or {},
            )

    def probe(
        self, client: Any, *, query: str, tenant_id: str | None = None, limit: int = 5
    ) -> list[RetrievalRecord]:
        graph = getattr(client, "_ferryte_zep_graph", None) or getattr(client, "graph", None)
        if graph is None:
            return []
        out: list[RetrievalRecord] = []
        seen: set[str] = set()
        for scope in ("edges", "nodes"):
            for fact in _iter_facts(_safe_search(graph, query, tenant_id, scope, limit=limit)):
                if fact["id"] in seen:
                    continue
                seen.add(fact["id"])
                out.append(
                    RetrievalRecord(
                        backend=self.backend,
                        query=query,
                        artifact_id=fact["id"],
                        content=fact["text"],
                        score=fact.get("score"),
                        tenant_id=tenant_id,
                        metadata={"kind": fact["kind"]},
                    )
                )
        return out


# --- parsing helpers (tolerate both zep_cloud objects and plain dicts) ---------


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("content") or value.get("text") or value.get("data") or value)
    return str(value)


def _get(obj: Any, *names: str) -> Any:
    for name in names:
        if isinstance(obj, dict):
            if name in obj:
                return obj[name]
        elif hasattr(obj, name):
            return getattr(obj, name)
    return None


def _episode_id(result: Any) -> str:
    if result is None:
        return str(uuid.uuid4())
    episode = _get(result, "episode") or result
    eid = _get(episode, "uuid_", "uuid", "id")
    return str(eid) if eid else str(uuid.uuid4())


def _iter_facts(result: Any) -> list[dict[str, Any]]:
    """Normalise a graph.search result into [{id, text, kind, score}].

    Handles a result object/dict carrying ``edges`` and/or ``nodes`` lists, or a
    bare list of edge/node objects.
    """
    if result is None:
        return []
    out: list[dict[str, Any]] = []

    def add_edge(e: Any) -> None:
        eid = _get(e, "uuid_", "uuid", "id")
        text = _get(e, "fact", "name", "content", "text") or ""
        if eid:
            out.append(
                {"id": str(eid), "text": _as_text(text), "kind": "graph_edge", "score": _get(e, "score")}
            )

    def add_node(node: Any) -> None:
        nid = _get(node, "uuid_", "uuid", "id")
        text = " ".join(
            str(p) for p in (_get(node, "name"), _get(node, "summary")) if p
        )
        if nid:
            out.append(
                {"id": str(nid), "text": _as_text(text), "kind": "graph_node", "score": _get(node, "score")}
            )

    edges = _get(result, "edges")
    nodes = _get(result, "nodes")
    if edges is None and nodes is None and isinstance(result, list):
        for item in result:
            (add_node if _get(item, "summary") is not None else add_edge)(item)
        return out
    for e in edges or []:
        add_edge(e)
    for node in nodes or []:
        add_node(node)
    return out


def _markers_from(records: list[dict[str, Any]]) -> list[str]:
    markers: list[str] = []
    for r in records:
        markers.extend(_MARKER_RE.findall(r.get("content") or ""))
    return list(dict.fromkeys(markers))


def _episode_deleter(graph: Any) -> Any:
    episode = getattr(graph, "episode", None)
    if episode is not None and hasattr(episode, "delete"):
        return episode.delete
    for name in ("delete_episode", "delete"):
        fn = getattr(graph, name, None)
        if callable(fn):
            return fn
    return None


def _component_deleter(graph: Any, kind: str) -> Any:
    comp = getattr(graph, kind, None)  # graph.edge / graph.node
    if comp is not None and hasattr(comp, "delete"):
        return comp.delete
    fn = getattr(graph, f"delete_{kind}", None)
    return fn if callable(fn) else None


def _try_delete(deleter: Any, artifact_id: str) -> bool:
    for call in (lambda: deleter(uuid_=artifact_id), lambda: deleter(artifact_id)):
        try:
            call()
            return True
        except TypeError:
            continue
        except Exception as exc:  # noqa: BLE001
            msg = str(exc).lower()  # already gone -> forgetting is idempotent
            return "not found" in msg or "does not exist" in msg
    return False


def _safe_search(
    graph: Any, query: str, tenant_id: str | None, scope: str, *, limit: int = 10
) -> Any:
    search = getattr(graph, "search", None)
    if search is None:
        return None
    attempts = (
        lambda: search(query=query, user_id=tenant_id, scope=scope, limit=limit),
        lambda: search(query=query, scope=scope, limit=limit),
        lambda: search(query=query),
        lambda: search(query),
    )
    for call in attempts:
        try:
            return call()
        except TypeError:
            continue
        except Exception:  # noqa: BLE001
            return None
    return None
