from pathlib import Path

import ferryte
from ferryte.adapters.vector import InMemoryVectorStore
from ferryte.lineage import get_lineage


def test_one_line_instrument_then_construct(fresh_ferryte: Path) -> None:
    handle = ferryte.instrument()
    store = InMemoryVectorStore()
    assert handle.list_clients(), "auto-discovery should pick up the new store"
    with ferryte.tag(source_id="src-1", tenant_id="acme"):
        store.add(content="the secret is BANANA-42")
    lineage = get_lineage()
    sources = lineage.sources()
    assert {s["source_id"] for s in sources} == {"src-1"}
    arts = lineage.artifacts_for_source("src-1")
    assert any("BANANA-42" in (a["content"] or "") for a in arts)


def test_explicit_client_instrument(fresh_ferryte: Path) -> None:
    store = InMemoryVectorStore()
    ferryte.instrument(clients=[store])
    with ferryte.tag(source_id="src-2", tenant_id="acme"):
        store.add(content="ANOTHER secret token Z9")
    arts = get_lineage().artifacts_for_source("src-2")
    assert any("Z9" in (a["content"] or "") for a in arts)


def test_retrieval_is_captured(fresh_ferryte: Path) -> None:
    ferryte.instrument()
    store = InMemoryVectorStore()
    with ferryte.tag(source_id="s-r", tenant_id="t"):
        store.add(content="lookup MARKER-X please")
    _ = store.search(query="lookup MARKER-X please", tenant_id="t")
    lineage = get_lineage()
    rets = lineage.retrievals_matching(query_substring="MARKER-X")
    assert rets, "retrieval should be captured"
