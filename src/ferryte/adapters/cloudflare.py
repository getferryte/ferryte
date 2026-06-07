"""Adapter for Cloudflare Agents memory (Vectorize-backed).

Cloudflare's ``agents`` SDK keeps per-agent state in a Durable Object and uses a
**Vectorize** index for semantic memory. The leak surface is the familiar one:
inserting a fact creates a source vector, the agent later writes **derived
summary vectors** that absorb several sources, and deleting the source vector by
id leaves the derived summary behind — still queryable, still leaking.

The adapter is duck-typed on a Vectorize-like index object exposing
``insert`` / ``upsert`` (records ``{id, values, metadata}``), ``query``, and
``deleteByIds`` (a flat ``delete`` is also accepted). Each record's
``metadata.text`` carries the content Ferryte inspects, so the adapter is
testable without a live Cloudflare account.

``cascade_derived``: False is the naive baseline (delete the source vector only);
True is the Ferryte default that also deletes any surviving vector whose metadata
still encodes a revoked source's high-entropy markers.
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


class CloudflareAdapter:
    name: str = "cloudflare"
    backend: BackendKind = BackendKind.CLOUDFLARE
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
        insert_name = _first_attr(client, "insert", "upsert")
        query_name = _first_attr(client, "query")
        if insert_name is None or query_name is None:
            get_lineage().record_blindspot(
                backend=self.backend.value,
                kind="incompatible_client",
                detail="Cloudflare Vectorize index missing insert/query; not instrumented.",
            )
            return client

        lineage = get_lineage()
        original_insert = getattr(client, insert_name)
        original_query = getattr(client, query_name)

        def insert(records: Any, *args: Any, **kwargs: Any) -> Any:
            ctx = current_context()
            result = original_insert(records, *args, **kwargs)
            for rec in _iter_records(records):
                lineage.record_write(
                    WriteRecord(
                        backend=self.backend,
                        artifact_id=rec["id"],
                        content=rec["text"],
                        source_id=kwargs.get("source_id") or ctx.source_id,
                        tenant_id=rec.get("tenant_id") or ctx.tenant_id,
                        kind="vector",
                    )
                )
            return result

        def query(*args: Any, **kwargs: Any) -> Any:
            ctx = current_context()
            result = original_query(*args, **kwargs)
            for m in _iter_matches(result):
                lineage.record_retrieval(
                    RetrievalRecord(
                        backend=self.backend,
                        query=str(kwargs.get("query") or (args[0] if args else "")),
                        artifact_id=m["id"],
                        content=m["text"],
                        score=m.get("score"),
                        tenant_id=ctx.tenant_id,
                        metadata={"kind": "vector"},
                    )
                )
            return result

        setattr(client, insert_name, insert)
        setattr(client, query_name, query)
        client._ferryte_patched = True
        client._ferryte_cf = {
            "insert_name": insert_name,
            "query_name": query_name,
            "delete_name": _first_attr(client, "deleteByIds", "delete"),
            "originals": {"insert": original_insert, "query": original_query},
        }
        return client

    def unpatch(self, client: Any) -> None:
        meta = getattr(client, "_ferryte_cf", None)
        if not meta:
            return
        setattr(client, meta["insert_name"], meta["originals"]["insert"])
        setattr(client, meta["query_name"], meta["originals"]["query"])
        client._ferryte_patched = False

    def delete_source(self, client: Any, *, source_id: str, tenant_id: str | None = None) -> int:
        lineage = get_lineage()
        lineage.mark_source_revoked(source_id)
        records = list(lineage.artifacts_for_source(source_id))
        meta = getattr(client, "_ferryte_cf", None)
        deleter = getattr(client, meta["delete_name"], None) if meta else None

        n = self._delete_ids(deleter, [r["artifact_id"] for r in records], lineage)
        if not getattr(self, "cascade_derived", True):
            return n

        markers = _markers_from(records)
        n += self._cascade(client, meta, markers=markers, lineage=lineage)
        return n

    def _delete_ids(self, deleter: Any, ids: list[str], lineage: Any) -> int:
        ids = [i for i in dict.fromkeys(ids) if i]
        if not ids:
            return 0
        if deleter is None:
            for i in ids:
                lineage.mark_artifact_deleted(i)
            return len(ids)
        if _try_delete(deleter, ids):
            for i in ids:
                lineage.mark_artifact_deleted(i)
            return len(ids)
        return 0

    def _cascade(
        self, client: Any, meta: dict[str, Any] | None, *, markers: list[str], lineage: Any
    ) -> int:
        if not markers or meta is None:
            return 0
        query = getattr(client, meta["query_name"], None)
        deleter = getattr(client, meta["delete_name"], None)
        if query is None or deleter is None:
            return 0
        leaking = [
            m["id"]
            for m in _iter_matches(_safe_query(query))
            if any(mk in m["text"] for mk in markers)
        ]
        return self._delete_ids(deleter, leaking, lineage)

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
                kind=a.get("kind", "vector"),
                metadata=a.get("metadata") or {},
            )

    def probe(
        self, client: Any, *, query: str, tenant_id: str | None = None, limit: int = 5
    ) -> list[RetrievalRecord]:
        meta = getattr(client, "_ferryte_cf", None)
        if meta is None:
            return []
        q = getattr(client, meta["query_name"], None)
        if q is None:
            return []
        return [
            RetrievalRecord(
                backend=self.backend,
                query=query,
                artifact_id=m["id"],
                content=m["text"],
                score=m.get("score"),
                tenant_id=tenant_id,
                metadata={"kind": "vector"},
            )
            for m in _iter_matches(_safe_query(q, q=query, limit=limit))
        ]


# --- helpers -------------------------------------------------------------------


def _first_attr(obj: Any, *names: str) -> str | None:
    for n in names:
        if callable(getattr(obj, n, None)):
            return n
    return None


def _get(obj: Any, *names: str) -> Any:
    for name in names:
        if isinstance(obj, dict):
            if name in obj:
                return obj[name]
        elif hasattr(obj, name):
            return getattr(obj, name)
    return None


def _text_of(metadata: Any) -> str:
    if metadata is None:
        return ""
    return str(_get(metadata, "text", "content") or "")


def _iter_records(records: Any) -> list[dict[str, Any]]:
    if records is None:
        return []
    items = records if isinstance(records, list) else [records]
    out: list[dict[str, Any]] = []
    for it in items:
        rid = _get(it, "id", "uuid")
        md = _get(it, "metadata")
        out.append(
            {
                "id": str(rid) if rid else str(uuid.uuid4()),
                "text": _text_of(md) or str(_get(it, "text", "content") or ""),
                "tenant_id": _get(md, "tenant_id") if md is not None else None,
            }
        )
    return out


def _iter_matches(result: Any) -> list[dict[str, Any]]:
    if result is None:
        return []
    matches = result if isinstance(result, list) else (_get(result, "matches") or [])
    out: list[dict[str, Any]] = []
    for m in matches or []:
        rid = _get(m, "id", "uuid")
        md = _get(m, "metadata")
        if rid:
            out.append(
                {
                    "id": str(rid),
                    "text": _text_of(md) or str(_get(m, "text", "content") or ""),
                    "score": _get(m, "score"),
                }
            )
    return out


def _markers_from(records: list[dict[str, Any]]) -> list[str]:
    markers: list[str] = []
    for r in records:
        markers.extend(_MARKER_RE.findall(r.get("content") or ""))
    return list(dict.fromkeys(markers))


def _try_delete(deleter: Any, ids: list[str]) -> bool:
    attempts = (lambda: deleter(ids=ids), lambda: deleter(ids), lambda: [deleter(i) for i in ids])
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


def _safe_query(fn: Any, *, q: str = "", limit: int = 1000) -> Any:
    attempts = (
        lambda: fn(topK=limit, returnMetadata=True),
        lambda: fn(query=q, top_k=limit),
        lambda: fn(q, top_k=limit),
        lambda: fn(),
    )
    for call in attempts:
        try:
            return call()
        except TypeError:
            continue
        except Exception:  # noqa: BLE001
            return None
    return None
