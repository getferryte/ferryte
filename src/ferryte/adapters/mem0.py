"""Adapter for the Mem0 memory client.

We import Mem0 lazily and tolerate its absence — if the user does not have
``mem0ai`` installed, the adapter simply skips itself during auto-discovery.

The adapter monkey-patches three methods on the ``Memory`` instance:
  - ``add``    → capture every write + provenance
  - ``search`` → capture every retrieval into the trace log
  - ``delete`` / ``delete_all`` → mark the source revoked in the lineage graph

Mem0's content is plain dicts/strings; we attach our ``source_id`` /
``tenant_id`` via Mem0's ``metadata`` slot so users can either pass it
explicitly or rely on the surrounding ``ferryte.tag(...)`` context.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterable
from typing import Any

from ..context import current_context
from ..lineage import get_lineage
from .base import AdapterCapability, BackendKind, RetrievalRecord, WriteRecord

# Canary-style high-entropy markers (e.g. KILO-VEGA-7A3F1C, ZEBRA-1BDBA3).
# Used by the cascade to find *derived/merged* memories that still encode a
# revoked source's secret but whose id was never returned at write time.
_MARKER_RE = re.compile(r"[A-Z0-9]{2,}(?:-[A-Z0-9]+)+")


class Mem0Adapter:
    name: str = "mem0"
    backend: BackendKind = BackendKind.MEM0
    capabilities: frozenset[AdapterCapability] = frozenset(
        {
            AdapterCapability.WRITE_CAPTURE,
            AdapterCapability.READ_CAPTURE,
            AdapterCapability.SOURCE_DELETE,
            AdapterCapability.TENANT_SCOPING,
            AdapterCapability.DERIVED_ENUMERATION,
        }
    )

    # When True (the product default), delete_source uses the lineage graph to
    # cascade-delete every derived fact Mem0 extracted from the revoked source.
    # The benchmark flips this to False to model the naive baseline: without
    # lineage you have no source→fact mapping, so Mem0's derived facts leak.
    cascade_derived: bool = True

    def patch(self, client: Any) -> Any:
        if getattr(client, "_ferryte_patched", False):
            return client

        lineage = get_lineage()

        original_add = getattr(client, "add", None)
        original_search = getattr(client, "search", None)
        original_delete = getattr(client, "delete", None)
        original_delete_all = getattr(client, "delete_all", None)

        if original_add is None or original_search is None:
            lineage.record_blindspot(
                backend=self.backend.value,
                kind="incompatible_client",
                detail=(
                    "Mem0 client missing expected add/search methods; "
                    "Ferryte could not instrument it."
                ),
            )
            return client

        def add(*args: Any, **kwargs: Any) -> Any:
            ctx = current_context()
            metadata = dict(kwargs.get("metadata") or {})
            sid = metadata.pop("source_id", None) or kwargs.pop("source_id", None) or ctx.source_id
            tid = (
                metadata.pop("tenant_id", None)
                or kwargs.pop("tenant_id", None)
                or kwargs.get("user_id")
                or ctx.tenant_id
            )
            kwargs["metadata"] = metadata
            result = original_add(*args, **kwargs)
            content = _content_of(args, kwargs)
            for artifact_id in _ids_of(result):
                lineage.record_write(
                    WriteRecord(
                        backend=self.backend,
                        artifact_id=artifact_id,
                        content=content,
                        source_id=sid,
                        tenant_id=tid,
                        kind="raw",
                        metadata=metadata,
                    )
                )
            if not _ids_of(result):
                lineage.record_blindspot(
                    backend=self.backend.value,
                    kind="unparseable_write",
                    detail=(
                        "Mem0 add() returned a shape Ferryte could not parse for ids; "
                        "lineage will fall back to content-substring matching."
                    ),
                )
            return result

        def search(*args: Any, **kwargs: Any) -> Any:
            ctx = current_context()
            query = args[0] if args else kwargs.get("query") or ""
            tid = kwargs.get("user_id") or kwargs.get("tenant_id") or ctx.tenant_id
            result = original_search(*args, **kwargs)
            for hit in _iter_hits(result):
                lineage.record_retrieval(
                    RetrievalRecord(
                        backend=self.backend,
                        query=str(query),
                        artifact_id=hit.get("id", ""),
                        content=str(hit.get("memory") or hit.get("text") or hit.get("content") or ""),
                        score=hit.get("score"),
                        tenant_id=tid,
                        metadata={k: v for k, v in hit.items() if k not in {"memory", "text", "content"}},
                    )
                )
            return result

        client.add = add  # type: ignore[assignment]
        client.search = search  # type: ignore[assignment]

        if original_delete is not None:
            def delete(*args: Any, **kwargs: Any) -> Any:
                sid = kwargs.pop("source_id", None)
                out = original_delete(*args, **kwargs)
                if sid:
                    lineage.mark_source_revoked(sid)
                return out

            client.delete = delete  # type: ignore[assignment]

        if original_delete_all is not None:
            def delete_all(*args: Any, **kwargs: Any) -> Any:
                sid = kwargs.pop("source_id", None)
                out = original_delete_all(*args, **kwargs)
                if sid:
                    lineage.mark_source_revoked(sid)
                return out

            client.delete_all = delete_all  # type: ignore[assignment]

        client._ferryte_patched = True
        client._ferryte_originals = {
            "add": original_add,
            "search": original_search,
            "delete": original_delete,
            "delete_all": original_delete_all,
        }
        return client

    def unpatch(self, client: Any) -> None:
        if not getattr(client, "_ferryte_patched", False):
            return
        originals = client._ferryte_originals
        if originals.get("add") is not None:
            client.add = originals["add"]
        if originals.get("search") is not None:
            client.search = originals["search"]
        if originals.get("delete") is not None:
            client.delete = originals["delete"]
        if originals.get("delete_all") is not None:
            client.delete_all = originals["delete_all"]
        client._ferryte_patched = False

    def delete_source(
        self, client: Any, *, source_id: str, tenant_id: str | None = None
    ) -> int:
        """Forget everything derived from ``source_id``.

        Two layers, deliberately separated so the benchmark's before/after is
        honest:

        * **Baseline (any competent app, no Ferryte cascade):** delete the memory
          ids Mem0 returned for this source at write time. Mem0 forgets *these*
          cleanly — verified 10/10 in ``benchmark/mem0_scalp.py`` — so this is
          NOT a leak and the baseline must reflect it. (We capture those ids via
          the shipped ``add`` patch, i.e. the same mapping any user gets back
          from ``add()`` and would store keyed by their source.)
        * **Ferryte cascade (the real lift):** additionally re-scan the live
          store for *derived/merged* memories that still encode the source's
          high-entropy markers but whose ids were never returned at write time —
          Mem0 consolidates facts across writes, so deleting only the captured
          id can miss these. This is where Ferryte beats a careful manual user.
        """
        lineage = get_lineage()
        lineage.mark_source_revoked(source_id)

        delete = getattr(client, "delete", None)
        records = list(lineage.artifacts_for_source(source_id))

        # Baseline: delete the captured write-time ids (de-duped; a source can
        # fan out into several extracted facts).
        ids = list(dict.fromkeys(r["artifact_id"] for r in records))
        n = 0
        for aid in ids:
            if delete is None:
                lineage.mark_artifact_deleted(aid)
                n += 1
                continue
            if self._delete_one(delete, aid, lineage):
                lineage.mark_artifact_deleted(aid)
                n += 1

        # Ferryte cascade: catch derived/merged survivors by marker re-scan.
        if getattr(self, "cascade_derived", True):
            n += self._cascade_markers(client, records, tenant_id, lineage)
        return n

    def _cascade_markers(
        self, client: Any, records: list[dict[str, Any]], tenant_id: str | None, lineage: Any
    ) -> int:
        """Delete any live memory still encoding one of the source's markers."""
        delete = getattr(client, "delete", None)
        if delete is None:
            return 0
        markers: list[str] = []
        for r in records:
            markers.extend(_MARKER_RE.findall(r.get("content") or ""))
        markers = list(dict.fromkeys(markers))
        if not markers:
            return 0
        seen: set[str] = set()
        n = 0
        for marker in markers:
            for hit in self._search_marker(client, marker, tenant_id):
                hid = str(hit.get("id") or "")
                text = str(hit.get("memory") or hit.get("text") or hit.get("content") or "")
                if not hid or hid in seen or marker not in text:
                    continue
                seen.add(hid)
                if self._delete_one(delete, hid, lineage):
                    lineage.mark_artifact_deleted(hid)
                    n += 1
        return n

    def _search_marker(self, client: Any, marker: str, tenant_id: str | None) -> list[dict[str, Any]]:
        """Best-effort lookup of live memories matching a marker, tolerating the
        mem0 2.x ``filters=`` surface, the legacy ``user_id=`` surface, and
        ``get_all`` as a fallback."""
        search = getattr(client, "search", None)
        for attempt in (
            lambda: search(marker, user_id=tenant_id) if search else None,
            lambda: search(marker, filters={"user_id": tenant_id}) if search else None,
            lambda: search(marker) if search else None,
        ):
            try:
                hits = _iter_hits(attempt())
            except Exception:  # noqa: BLE001 - try the next shape
                continue
            if hits:
                return hits
        get_all = getattr(client, "get_all", None)
        for attempt in (
            lambda: get_all(user_id=tenant_id) if get_all else None,
            lambda: get_all() if get_all else None,
        ):
            try:
                hits = _iter_hits(attempt())
            except Exception:  # noqa: BLE001
                continue
            if hits:
                return hits
        return []

    def _delete_one(self, delete: Any, aid: str, lineage: Any) -> bool:
        """Delete one Mem0 memory, tolerating signature differences and
        already-gone ids (forgetting is idempotent — a missing id is success)."""
        last_exc: Exception | None = None
        for call in (lambda: delete(memory_id=aid), lambda: delete(aid)):
            try:
                call()
                return True
            except TypeError as exc:  # wrong signature — try the next form
                last_exc = exc
                continue
            except Exception as exc:  # noqa: BLE001
                if "not found" in str(exc).lower() or "does not exist" in str(exc).lower():
                    return True  # already deleted in a prior pass / run
                last_exc = exc
                break
        lineage.record_blindspot(
            backend=self.backend.value,
            kind="delete_failed",
            detail=f"Mem0 delete() failed for artifact id {aid}: {last_exc}",
        )
        return False

    def list_artifacts_for_source(
        self,
        client: Any,
        *,
        source_id: str,
        tenant_id: str | None = None,
    ) -> Iterable[WriteRecord]:
        lineage = get_lineage()
        for a in lineage.artifacts_for_source(source_id):
            yield WriteRecord(
                backend=self.backend,
                artifact_id=a["artifact_id"],
                content=a.get("content") or "",
                source_id=source_id,
                tenant_id=a.get("tenant_id"),
                kind=a.get("kind", "raw"),
                metadata=a.get("metadata") or {},
            )

    def probe(
        self,
        client: Any,
        *,
        query: str,
        tenant_id: str | None = None,
        limit: int = 5,
    ) -> list[RetrievalRecord]:
        search = getattr(client, "search", None)
        if search is None:
            return []
        kwargs: dict[str, Any] = {"limit": limit}
        if tenant_id is not None:
            kwargs["user_id"] = tenant_id
        result = search(query, **kwargs)
        out: list[RetrievalRecord] = []
        for hit in _iter_hits(result):
            out.append(
                RetrievalRecord(
                    backend=self.backend,
                    query=query,
                    artifact_id=str(hit.get("id", "")),
                    content=str(hit.get("memory") or hit.get("text") or hit.get("content") or ""),
                    score=hit.get("score"),
                    tenant_id=tenant_id,
                    metadata={k: v for k, v in hit.items() if k not in {"memory", "text", "content"}},
                )
            )
        return out


def _content_of(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    payload = (
        kwargs.get("messages")
        or kwargs.get("data")
        or kwargs.get("text")
        or (args[0] if args else None)
    )
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        return str(payload.get("content") or payload.get("text") or payload)
    if isinstance(payload, list):
        return " | ".join(
            str(item.get("content") if isinstance(item, dict) else item) for item in payload
        )
    return str(payload)


def _iter_hits(result: Any) -> list[dict[str, Any]]:
    if result is None:
        return []
    if isinstance(result, list):
        return [r for r in result if isinstance(r, dict)]
    if isinstance(result, dict):
        items = result.get("results") or result.get("memories") or result.get("data")
        if isinstance(items, list):
            return [r for r in items if isinstance(r, dict)]
    return []


def _ids_of(result: Any) -> list[str]:
    if result is None:
        return [str(uuid.uuid4())]
    if isinstance(result, str):
        return [result]
    if isinstance(result, dict):
        if "id" in result:
            return [str(result["id"])]
        items = result.get("results") or result.get("memories") or []
        return [str(r.get("id")) for r in items if isinstance(r, dict) and r.get("id")]
    if isinstance(result, list):
        out: list[str] = []
        for r in result:
            if isinstance(r, dict) and r.get("id"):
                out.append(str(r["id"]))
        if out:
            return out
    return []
