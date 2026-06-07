"""Cloudflare adapter: capture + cascade over a fake Vectorize index.

The fake models the leak shape: inserting a source vector also writes a derived
summary vector that absorbs the fact. Deleting the source vector by id leaves the
summary behind — the leak Ferryte catches. No live Cloudflare account required.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import ferryte
from ferryte.adapters.cloudflare import CloudflareAdapter
from ferryte.lineage import get_lineage

MARKER = "KILO-VEGA-77"
SENTENCE = f"User acme note: the secret code is {MARKER}. Do not disclose."


class VectorizeIndex:
    def __init__(self) -> None:
        self.vectors: dict[str, dict] = {}

    def insert(self, records):
        for r in records:
            self.vectors[r["id"]] = r
            # a derived summary vector absorbs the fact (the leak surface)
            sid = str(uuid.uuid4())
            self.vectors[sid] = {
                "id": sid,
                "metadata": {"text": f"summary: {r['metadata']['text']}"},
            }
        return {"mutationId": str(uuid.uuid4())}

    def query(self, topK=100, returnMetadata=True, **_):
        return {"matches": list(self.vectors.values())[:topK]}

    def deleteByIds(self, ids=None):
        for i in ids or []:
            self.vectors.pop(i, None)
        return {"count": len(ids or [])}


def _seed(client: VectorizeIndex) -> None:
    with ferryte.tag(source_id="src-cf", tenant_id="acme"):
        client.insert(
            [{"id": "v1", "values": [0.1, 0.2], "metadata": {"text": SENTENCE, "tenant_id": "acme"}}]
        )


def test_cloudflare_write_is_captured(fresh_ferryte: Path) -> None:
    client = VectorizeIndex()
    ferryte.instrument(clients=[client])
    _seed(client)
    arts = get_lineage().artifacts_for_source("src-cf")
    assert any(MARKER in (a["content"] or "") for a in arts)
    assert any(a["artifact_id"] == "v1" for a in arts)


def test_cloudflare_baseline_leaks_derived_summary(fresh_ferryte: Path) -> None:
    client = VectorizeIndex()
    handle = ferryte.instrument(clients=[client])
    adapter = handle.adapter_for(client)
    assert isinstance(adapter, CloudflareAdapter)
    _seed(client)

    adapter.cascade_derived = False
    adapter.delete_source(client, source_id="src-cf", tenant_id="acme")

    hits = adapter.probe(client, query=MARKER, tenant_id="acme")
    assert any(MARKER in h.content for h in hits), "derived summary vector must still leak"


def test_cloudflare_cascade_forgets_derived_summary(fresh_ferryte: Path) -> None:
    client = VectorizeIndex()
    handle = ferryte.instrument(clients=[client])
    adapter = handle.adapter_for(client)
    _seed(client)

    adapter.cascade_derived = True
    adapter.delete_source(client, source_id="src-cf", tenant_id="acme")

    hits = adapter.probe(client, query=MARKER, tenant_id="acme")
    assert not any(MARKER in h.content for h in hits), "cascade must delete the derived summary"
