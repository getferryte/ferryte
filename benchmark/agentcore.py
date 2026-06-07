"""AWS Bedrock AgentCore Memory backend + Ferryte adapter.

The system-under-test is a real AgentCore Memory resource. We write raw
conversation turns as **events** (CreateEvent); AgentCore's strategies extract
**derived long-term memory records** (summaries / semantic facts) asynchronously.
The benchmark then "revokes the source" by deleting those events (DeleteEvent)
and probes whether the derived records still surface the canary
(RetrieveMemoryRecords). If they do, that's the leak — deleting source events
does not clear the long-term memory they were extracted into.

Requires a live AgentCore Memory (see setup_agentcore.py) and AWS credentials.
Extraction is asynchronous, so writes poll until records appear (or time out,
reported honestly as BLIND rather than hidden).
"""

from __future__ import annotations

import os
import re
import time
import uuid
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from ferryte.adapters.base import (
    AdapterCapability,
    BackendKind,
    RetrievalRecord,
    WriteRecord,
)
from ferryte.context import current_context
from ferryte.lineage import get_lineage

# Canary markers look like CODE-STYLE tokens (e.g. ORION-DELTA-77); confirming one
# of these landed in a derived record proves extraction ran before we revoke.
_MARKER_RE = re.compile(r"[A-Z0-9]{2,}(?:-[A-Z0-9]+)+")


class AgentCoreMemory:
    """Thin client over AgentCore Memory mirroring the benchmark surface
    (add / search / delete_by_source). Tenant -> actorId, source -> sessionId."""

    def __init__(
        self,
        *,
        memory_id: str | None = None,
        namespace: str | None = None,
        region: str | None = None,
        extraction_timeout_s: float = 120.0,
        block_on_extraction: bool = True,
        run_tag: str | None = None,
    ) -> None:
        import boto3  # noqa: PLC0415

        self.memory_id = memory_id or os.environ["AGENTCORE_MEMORY_ID"]
        self.namespace = namespace or os.environ.get("AGENTCORE_NAMESPACE", "/facts/{actorId}")
        self.extraction_timeout_s = extraction_timeout_s
        self.block_on_extraction = block_on_extraction
        # Per-run isolation: the AgentCore Memory resource is shared + persistent
        # across runs, so without this every run reads prior runs' derived records
        # out of /facts/{tenant}. Map each logical tenant to a per-run cloud actor
        # (<run_tag>_<tenant>) → a fresh namespace per run, while keeping different
        # tenants isolated from each other (cross-tenant test stays honest).
        self.run_tag = run_tag or os.environ.get("AGENTCORE_RUN_TAG") or uuid.uuid4().hex[:8]
        region = region or os.environ.get("AWS_REGION", "us-west-2")
        self._dp = boto3.client("bedrock-agentcore", region_name=region)
        # source_id -> list[(sessionId, eventId, actorId)]
        self._events: dict[str, list[tuple[str, str, str]]] = {}
        # logical tenants we've written to (for store-inspection scans)
        self._tenants: set[str] = set()
        self._warm_data_plane()

    def _warm_data_plane(self, *, max_wait_s: float = 60.0, every_s: float = 4.0) -> None:
        """Workaround for AgentCore data-plane propagation: new boto3 clients can
        get "Memory not found" for ~30-60s after the control plane reports ACTIVE.
        Poll a cheap read until it succeeds."""
        deadline = time.time() + max_wait_s
        while time.time() < deadline:
            try:
                self._dp.list_actors(memoryId=self.memory_id, maxResults=1)
                return
            except self._dp.exceptions.ResourceNotFoundException:
                time.sleep(every_s)
        # let the next real call surface the error if still not ready

    def _actor(self, tenant_id: str | None) -> str:
        """Logical tenant -> per-run cloud actorId, so runs don't share namespaces."""
        base = tenant_id or "default"
        return f"{self.run_tag}_{base}" if self.run_tag else base

    def _ns(self, tenant_id: str | None) -> str:
        return self.namespace.replace("{actorId}", self._actor(tenant_id))

    def add(
        self,
        *,
        content: str,
        source_id: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        self._tenants.add(tenant_id or "default")
        actor = self._actor(tenant_id)
        session = source_id or str(uuid.uuid4())
        resp = self._dp.create_event(
            memoryId=self.memory_id,
            actorId=actor,
            sessionId=session,
            eventTimestamp=datetime.now(timezone.utc),
            payload=[{"conversational": {"role": "USER", "content": {"text": content}}}],
        )
        event_id = resp["event"]["eventId"]
        if source_id:
            self._events.setdefault(source_id, []).append((session, event_id, actor))
        if self.block_on_extraction:
            # pass the *logical* tenant; search()/_ns() apply the per-run tag once
            extracted = self._await_extraction(content=content, tenant_id=tenant_id)
            if not extracted:
                # Surface a Ferryte blindspot so the scenario downgrades from PASS
                # to BLIND/WARN. A silent PASS here would be the worst kind of lie.
                try:
                    from ferryte.adapters.base import BackendKind
                    from ferryte.lineage import get_lineage

                    get_lineage().record_blindspot(
                        backend=BackendKind.VECTOR.value,
                        kind="extraction_timeout",
                        detail=(
                            f"AgentCore did not extract a memory record from event {event_id} "
                            f"within {self.extraction_timeout_s:.0f}s; the delete-after-revoke "
                            "test is inconclusive for this fact."
                        ),
                    )
                except Exception:  # noqa: BLE001 - never break the test on instrumentation
                    pass
        return event_id

    def _await_extraction(self, *, content: str, tenant_id: str) -> bool:
        """Block until a canary marker from `content` shows up in a derived record,
        proving AgentCore extracted it BEFORE we revoke the source. Times out
        honestly (caller surfaces BLIND) rather than racing the async pipeline."""
        markers = _MARKER_RE.findall(content)
        if not markers:
            time.sleep(8)  # no marker to track; give extraction a moment
            return True
        deadline = time.time() + self.extraction_timeout_s
        while time.time() < deadline:
            for it, _ in self.search(query=content, tenant_id=tenant_id, limit=10):
                if any(m in (it.content or "") for m in markers):
                    return True
            time.sleep(5)
        return False

    def search(
        self, *, query: str, tenant_id: str | None = None, limit: int = 5
    ) -> list[tuple[Any, float]]:
        resp = self._dp.retrieve_memory_records(
            memoryId=self.memory_id,
            namespace=self._ns(tenant_id),
            searchCriteria={"searchQuery": query, "topK": limit},
            maxResults=limit,
        )
        out: list[tuple[Any, float]] = []
        for rec in resp.get("memoryRecordSummaries", []):
            out.append((_Rec(rec, tenant_id), float(rec.get("score") or 0.0)))
        return out

    def delete_by_source(self, source_id: str, *, tenant_id: str | None = None) -> int:
        """Revoke the source: delete its raw events. Derived records are left
        intact on purpose — that is the behaviour under test."""
        n = 0
        for session, event_id, actor in self._events.get(source_id, []):
            self._dp.delete_event(
                memoryId=self.memory_id, sessionId=session, eventId=event_id, actorId=actor
            )
            n += 1
        return n

    def raw_items_containing(self, needle: str) -> list[Any]:
        """Store-inspection: list the derived memory records in every namespace we
        wrote to and return those still containing the marker. This is the honest
        "is the data still sitting there?" check — `DeleteEvent` does NOT remove
        these derived records (verified empirically), so a naive revoke leaks them
        even when a semantic probe-by-question happens to miss them."""
        out: list[Any] = []
        for tenant in self._tenants or {"default"}:
            ns = self._ns(tenant)
            try:
                items = self._dp.list_memory_records(
                    memoryId=self.memory_id, namespace=ns, maxResults=100
                ).get("memoryRecordSummaries", [])
            except Exception:  # noqa: BLE001 - never break inspection on a list error
                continue
            for rec in items:
                if needle in ((rec.get("content") or {}).get("text", "")):
                    out.append(_Rec(rec, tenant))
        return out


class _Rec:
    """Adapts an AgentCore memoryRecordSummary to the StoredItem-ish surface the
    scenarios read (artifact_id / content / kind)."""

    __slots__ = ("artifact_id", "content", "tenant_id", "kind", "metadata", "source_id", "deleted")

    def __init__(self, rec: dict, tenant_id: str | None) -> None:
        self.artifact_id = rec.get("memoryRecordId", "")
        self.content = (rec.get("content") or {}).get("text", "")
        self.tenant_id = tenant_id
        self.kind = "summary"
        self.source_id = None
        # if it came back from list_memory_records it's live (not deleted)
        self.deleted = False
        self.metadata = {"kind": "summary", "memoryStrategyId": rec.get("memoryStrategyId")}


class AgentCoreAdapter:
    name = "bedrock-agentcore"
    backend = BackendKind.VECTOR
    capabilities = frozenset(
        {
            AdapterCapability.WRITE_CAPTURE,
            AdapterCapability.READ_CAPTURE,
            AdapterCapability.SOURCE_DELETE,
            AdapterCapability.TENANT_SCOPING,
            AdapterCapability.DERIVED_ENUMERATION,
        }
    )
    # When True, delete_source also cascades the derived long-term memory records
    # extracted from those events (the fix AWS's own docs recommend). The runner
    # toggles this to produce the Before/After comparison.
    cascade_derived: bool = False

    # Cascade settling knobs (AgentCore extraction is eventually-consistent and can
    # RE-create a record after deletion). Defaults trade time for reproducibility.
    reextraction_settle_s: float = 25.0  # let in-flight extraction finish first
    quiet_window_s: float = 8.0  # pause between delete passes / quiet checks
    cascade_timeout_s: float = 120.0  # hard cap on the settling loop
    quiet_passes_needed: int = 2  # consecutive empty listings to declare "quiet"

    def patch(self, client: AgentCoreMemory) -> AgentCoreMemory:
        if getattr(client, "_ferryte_patched", False):
            return client
        lineage = get_lineage()
        orig_add, orig_search, orig_delete = client.add, client.search, client.delete_by_source

        def add(*, content, source_id=None, tenant_id=None, metadata=None):
            ctx = current_context()
            sid, tid = source_id or ctx.source_id, tenant_id or ctx.tenant_id
            aid = orig_add(content=content, source_id=sid, tenant_id=tid, metadata=metadata)
            lineage.record_write(
                WriteRecord(
                    backend=self.backend,
                    artifact_id=aid,
                    content=content,
                    source_id=sid,
                    tenant_id=tid,
                    kind="raw",
                    metadata=dict(metadata or {}),
                )
            )
            return aid

        def search(*, query, tenant_id=None, limit=5):
            tid = tenant_id or current_context().tenant_id
            results = orig_search(query=query, tenant_id=tid, limit=limit)
            for it, score in results:
                lineage.record_retrieval(
                    RetrievalRecord(
                        backend=self.backend,
                        query=query,
                        artifact_id=it.artifact_id,
                        content=it.content,
                        score=float(score),
                        tenant_id=tid,
                        metadata={"kind": it.kind},
                    )
                )
            return results

        def delete_by_source(source_id, *, tenant_id=None):
            n = orig_delete(source_id, tenant_id=tenant_id)
            lineage.mark_source_revoked(source_id)
            return n

        client.add, client.search, client.delete_by_source = add, search, delete_by_source
        client._ferryte_patched = True
        client._ferryte_orig = (orig_add, orig_search, orig_delete)
        return client

    def unpatch(self, client: AgentCoreMemory) -> None:
        if not getattr(client, "_ferryte_patched", False):
            return
        client.add, client.search, client.delete_by_source = client._ferryte_orig
        client._ferryte_patched = False

    def delete_source(self, client, *, source_id, tenant_id=None) -> int:
        n = client.delete_by_source(source_id, tenant_id=tenant_id)
        if self.cascade_derived:
            n += self._cascade_derived_records(client, tenant_id=tenant_id)
        return n

    def _cascade_derived_records(self, client, *, tenant_id: str | None) -> int:
        """Enumerate derived memory records for this tenant and delete them
        (the fix AWS's own docs name; lineage-cascade-equivalent for AgentCore).

        AgentCore extraction is eventually-consistent: it can re-create a record
        in the background *after* the source events were deleted but *before* the
        test probes — which is exactly what made an earlier run flaky. To be
        reproducible we:

          1. Wait ``reextraction_settle_s`` so any in-flight extraction from the
             just-deleted events finishes (the source is already gone, so it can't
             start a new one — we only need to drain what was already running).
          2. Delete every derived record, then re-list after a quiet window;
             repeat until the namespace stays empty for ``quiet_passes_needed``
             consecutive checks (a real quiet window, not a single lucky read),
             or we hit ``cascade_timeout_s``.
        """
        if not tenant_id:
            return 0
        ns = client._ns(tenant_id)

        def _list() -> list:
            try:
                return client._dp.list_memory_records(
                    memoryId=client.memory_id, namespace=ns, maxResults=100
                ).get("memoryRecordSummaries", [])
            except Exception:  # noqa: BLE001
                return []

        # 1) Drain in-flight extraction before we start cleaning up.
        time.sleep(self.reextraction_settle_s)

        deleted = 0
        quiet = 0
        deadline = time.time() + self.cascade_timeout_s
        while time.time() < deadline:
            items = _list()
            if not items:
                quiet += 1
                if quiet >= self.quiet_passes_needed:
                    return deleted
                time.sleep(self.quiet_window_s)
                continue
            quiet = 0  # something reappeared (re-extraction) — keep going
            for r in items:
                try:
                    client._dp.delete_memory_record(
                        memoryId=client.memory_id, memoryRecordId=r["memoryRecordId"]
                    )
                    deleted += 1
                except Exception:  # noqa: BLE001
                    pass
            time.sleep(self.quiet_window_s)
        return deleted

    def list_artifacts_for_source(
        self, client, *, source_id, tenant_id=None
    ) -> Iterable[WriteRecord]:
        return []  # derived records aren't enumerable by source via the public API

    def probe(self, client, *, query, tenant_id=None, limit=5) -> list[RetrievalRecord]:
        return [
            RetrievalRecord(
                backend=self.backend,
                query=query,
                artifact_id=it.artifact_id,
                content=it.content,
                score=float(score),
                tenant_id=tenant_id,
                metadata={"kind": it.kind},
            )
            for it, score in client.search(query=query, tenant_id=tenant_id, limit=limit)
        ]
