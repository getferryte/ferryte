"""Adapter for Letta (formerly MemGPT) — stateful agents with archival memory.

Letta's distinctive shape is a tiered memory: an agent keeps **core memory**
blocks (always-in-context summaries) plus **archival memory** passages (a vector
store the agent reads from). The leak surface mirrors the others:

  - You insert raw facts as **archival passages**.
  - The agent distills them into **core-memory blocks** / summary passages that
    *absorb multiple sources*.
  - Deleting the original passage does **not** remove the derived summary that
    still encodes the fact — so it survives recall. That is what Ferryte catches.

The adapter is duck-typed on the ``letta_client`` surface — a ``passages``
namespace exposing ``create`` / ``list`` / ``delete`` — and also tolerates the
older flat ``insert_archival_memory`` / ``get_archival_memory`` /
``delete_archival_memory`` methods, so it is testable without a live Letta server.

``cascade_derived`` matches the other adapters: False is the naive baseline that
revokes only the raw passage (derived summaries leak); True is the Ferryte
default that also deletes every derived passage/block still encoding a revoked
source's high-entropy markers.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterable
from typing import Any

from ..context import current_context
from ..lineage import get_lineage
from .base import AdapterCapability, BackendKind, RetrievalRecord, WriteRecord

_MARKER_RE = re.compile(r"[A-Z0-9]{2,}(?:-[A-Z0-9]+)+")


class LettaAdapter:
    name: str = "letta"
    backend: BackendKind = BackendKind.LETTA
    capabilities: frozenset[AdapterCapability] = frozenset(
        {
            AdapterCapability.WRITE_CAPTURE,
            AdapterCapability.READ_CAPTURE,
            AdapterCapability.SOURCE_DELETE,
            AdapterCapability.TENANT_SCOPING,
            AdapterCapability.DERIVED_ENUMERATION,
        }
    )
    cascade_derived: bool = True

    def patch(self, client: Any) -> Any:
        if getattr(client, "_ferryte_patched", False):
            return client
        api = _passages_api(client)
        if api is None:
            get_lineage().record_blindspot(
                backend=self.backend.value,
                kind="incompatible_client",
                detail="Letta client missing archival passage create/list; not instrumented.",
            )
            return client

        lineage = get_lineage()
        create_name, list_name = api["create_name"], api["list_name"]
        target = api["target"]
        original_create = getattr(target, create_name)
        original_list = getattr(target, list_name, None)

        def create(*args: Any, **kwargs: Any) -> Any:
            ctx = current_context()
            sid = kwargs.pop("source_id", None) or ctx.source_id
            tid = kwargs.get("agent_id") or ctx.tenant_id
            text = kwargs.get("text") or kwargs.get("content") or (args[0] if args else "")
            result = original_create(*args, **kwargs)
            lineage.record_write(
                WriteRecord(
                    backend=self.backend,
                    artifact_id=_passage_id(result),
                    content=_as_text(text),
                    source_id=sid,
                    tenant_id=tid,
                    kind="archival_passage",
                )
            )
            return result

        setattr(target, create_name, create)
        if original_list is not None:

            def list_(*args: Any, **kwargs: Any) -> Any:
                ctx = current_context()
                tid = kwargs.get("agent_id") or ctx.tenant_id
                result = original_list(*args, **kwargs)
                for p in _iter_passages(result):
                    lineage.record_retrieval(
                        RetrievalRecord(
                            backend=self.backend,
                            query=kwargs.get("query") or "",
                            artifact_id=p["id"],
                            content=p["text"],
                            tenant_id=tid,
                            metadata={"kind": "archival_passage"},
                        )
                    )
                return result

            setattr(target, list_name, list_)

        client._ferryte_patched = True
        client._ferryte_letta = {
            "target": target,
            "create_name": create_name,
            "list_name": list_name,
            "delete_name": api["delete_name"],
            "originals": {"create": original_create, "list": original_list},
        }
        return client

    def unpatch(self, client: Any) -> None:
        meta = getattr(client, "_ferryte_letta", None)
        if not meta:
            return
        target, originals = meta["target"], meta["originals"]
        setattr(target, meta["create_name"], originals["create"])
        if originals["list"] is not None:
            setattr(target, meta["list_name"], originals["list"])
        client._ferryte_patched = False

    def delete_source(self, client: Any, *, source_id: str, tenant_id: str | None = None) -> int:
        lineage = get_lineage()
        lineage.mark_source_revoked(source_id)
        records = list(lineage.artifacts_for_source(source_id))
        meta = getattr(client, "_ferryte_letta", None)
        if meta is None:
            for r in records:
                lineage.mark_artifact_deleted(r["artifact_id"])
            return len(records)

        deleter = getattr(meta["target"], meta["delete_name"], None)
        n = self._delete_ids(deleter, [r["artifact_id"] for r in records], tenant_id, lineage)
        if not getattr(self, "cascade_derived", True):
            return n

        # cascade: any surviving passage that still encodes a revoked marker
        markers = _markers_from(records)
        n += self._cascade(meta, markers=markers, tenant_id=tenant_id, lineage=lineage)
        return n

    def _delete_ids(
        self, deleter: Any, ids: list[str], tenant_id: str | None, lineage: Any
    ) -> int:
        n = 0
        for pid in dict.fromkeys(p for p in ids if p):
            if deleter is None or _try_delete(deleter, pid, tenant_id):
                lineage.mark_artifact_deleted(pid)
                n += 1
        return n

    def _cascade(
        self, meta: dict[str, Any], *, markers: list[str], tenant_id: str | None, lineage: Any
    ) -> int:
        if not markers:
            return 0
        lister = getattr(meta["target"], meta["list_name"], None)
        deleter = getattr(meta["target"], meta["delete_name"], None)
        if lister is None or deleter is None:
            return 0
        n = 0
        for p in _iter_passages(_safe_list(lister, tenant_id)):
            if any(m in p["text"] for m in markers) and _try_delete(deleter, p["id"], tenant_id):
                lineage.mark_artifact_deleted(p["id"])
                n += 1
        return n

    def list_artifacts_for_source(
        self, client: Any, *, source_id: str, tenant_id: str | None = None
    ) -> Iterable[WriteRecord]:
        for a in get_lineage().artifacts_for_source(source_id):
            yield WriteRecord(
                backend=self.backend,
                artifact_id=a["artifact_id"],
                content=a.get("content") or "",
                source_id=source_id,
                tenant_id=a.get("tenant_id"),
                kind=a.get("kind", "archival_passage"),
                metadata=a.get("metadata") or {},
            )

    def probe(
        self, client: Any, *, query: str, tenant_id: str | None = None, limit: int = 5
    ) -> list[RetrievalRecord]:
        meta = getattr(client, "_ferryte_letta", None)
        if meta is None:
            return []
        lister = getattr(meta["target"], meta["list_name"], None)
        if lister is None:
            return []
        out: list[RetrievalRecord] = []
        for p in _iter_passages(_safe_list(lister, tenant_id, query=query, limit=limit)):
            out.append(
                RetrievalRecord(
                    backend=self.backend,
                    query=query,
                    artifact_id=p["id"],
                    content=p["text"],
                    tenant_id=tenant_id,
                    metadata={"kind": "archival_passage"},
                )
            )
        return out


# --- helpers (tolerate letta_client objects, the flat API, and plain dicts) ----


def _passages_api(client: Any) -> dict[str, Any] | None:
    # modern letta_client: client.agents.passages.{create,list,delete}
    agents = getattr(client, "agents", None)
    passages = getattr(agents, "passages", None) if agents is not None else None
    if passages is None:
        passages = getattr(client, "passages", None)
    if passages is not None and hasattr(passages, "create"):
        return {
            "target": passages,
            "create_name": "create",
            "list_name": "list",
            "delete_name": "delete",
        }
    # older flat API: insert/get/delete_archival_memory on the client itself
    if hasattr(client, "insert_archival_memory"):
        return {
            "target": client,
            "create_name": "insert_archival_memory",
            "list_name": "get_archival_memory",
            "delete_name": "delete_archival_memory",
        }
    return None


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("text") or value.get("content") or value)
    return str(value)


def _get(obj: Any, *names: str) -> Any:
    for name in names:
        if isinstance(obj, dict):
            if name in obj:
                return obj[name]
        elif hasattr(obj, name):
            return getattr(obj, name)
    return None


def _passage_id(result: Any) -> str:
    if isinstance(result, list) and result:
        result = result[0]
    pid = _get(result, "id", "uuid", "memory_id") if result is not None else None
    return str(pid) if pid else str(uuid.uuid4())


def _iter_passages(result: Any) -> list[dict[str, Any]]:
    if result is None:
        return []
    items = result
    if not isinstance(result, list):
        items = _get(result, "passages") or _get(result, "items") or []
    out: list[dict[str, Any]] = []
    for it in items or []:
        pid = _get(it, "id", "uuid", "memory_id")
        text = _get(it, "text", "content", "summary") or ""
        if pid:
            out.append({"id": str(pid), "text": _as_text(text)})
    return out


def _markers_from(records: list[dict[str, Any]]) -> list[str]:
    markers: list[str] = []
    for r in records:
        markers.extend(_MARKER_RE.findall(r.get("content") or ""))
    return list(dict.fromkeys(markers))


def _try_delete(deleter: Any, pid: str, tenant_id: str | None) -> bool:
    attempts = (
        lambda: deleter(agent_id=tenant_id, memory_id=pid),
        lambda: deleter(tenant_id, pid),
        lambda: deleter(memory_id=pid),
        lambda: deleter(pid),
    )
    for call in attempts:
        try:
            call()
            return True
        except TypeError:
            continue
        except Exception as exc:  # noqa: BLE001
            msg = str(exc).lower()
            return "not found" in msg or "does not exist" in msg
    return False


def _safe_list(lister: Any, tenant_id: str | None, *, query: str = "", limit: int = 50) -> Any:
    attempts = (
        lambda: lister(agent_id=tenant_id, query=query, limit=limit),
        lambda: lister(agent_id=tenant_id, limit=limit),
        lambda: lister(agent_id=tenant_id),
        lambda: lister(tenant_id),
        lambda: lister(),
    )
    for call in attempts:
        try:
            return call()
        except TypeError:
            continue
        except Exception:  # noqa: BLE001
            return None
    return None
