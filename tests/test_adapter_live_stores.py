"""Live integration tests: real chromadb and real Qdrant, in-process.

These are the tests that matter for a claim like "we support Chroma". Unit
tests against fakes prove our own logic is self-consistent; only running against
the actual client library proves the API we call still exists. That distinction
is not academic — the first live run of the Qdrant adapter failed immediately
because qdrant-client replaced ``search()`` with ``query_points()``, which no
amount of mocking would have caught.

Both stores run in-process (Chroma ephemeral, Qdrant ``:memory:``), so these
need no docker and no network. They skip cleanly when the optional driver is
absent.

Chroma note: the default embedding function downloads an ONNX model on first
use. That fails in air-gapped CI and behind egress proxies, so these tests inject
a deterministic offline embedder — which is also what a production deployment
should do, to make Ferryte's queries embed exactly like the application's.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any

import pytest

_WORD = re.compile(r"[a-z0-9]+")

SEED = [
    ("Acme renewal terms include a bespoke discount of eighteen percent", "acme", "s1"),
    ("Acme quarterly revenue forecast shows margin compression in Q3", "acme", "s1"),
    ("Globex onboarding checklist for new enterprise accounts", "globex", "s2"),
]


def _vec(text: str, dim: int = 64) -> list[float]:
    v = [0.0] * dim
    for tok in _WORD.findall((text or "").lower()):
        v[int(hashlib.sha1(tok.encode()).hexdigest(), 16) % dim] += 1.0
    n = sum(x * x for x in v) ** 0.5
    return [x / n for x in v] if n else v


# --------------------------------------------------------------------- Chroma

chromadb = pytest.importorskip("chromadb", reason="chromadb not installed")


@pytest.fixture()
def chroma_store(tmp_path: Any) -> Any:
    from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

    from ferryte.adapters.chroma import ChromaAdapter, ChromaStore
    from ferryte.config import get_config, set_config

    cfg = get_config()
    cfg.state_dir = tmp_path
    set_config(cfg)

    class OfflineEF(EmbeddingFunction):
        def __call__(self, input: Documents) -> Embeddings:  # noqa: A002 - chroma's name
            return [_vec(t) for t in input]

        def name(self) -> str:
            return "ferryte-test-ef"

        @staticmethod
        def build_from_config(config: dict) -> OfflineEF:
            return OfflineEF()

        def get_config(self) -> dict:
            return {}

    # Chroma's EphemeralClient is process-wide and `get_or_create_collection`
    # returns the SAME collection for the same name — so a fixed name would let
    # seeds accumulate across tests. Unique per test.
    store = ChromaStore.connect(
        collection=f"ferryte_test_{uuid.uuid4().hex[:8]}", embedding_function=OfflineEF()
    )
    ChromaAdapter().patch(store)
    for content, tenant, source in SEED:
        store.add(content=content, tenant_id=tenant, source_id=source)
    return store


def test_chroma_tenant_discovery_and_enumeration(chroma_store: Any) -> None:
    assert sorted(chroma_store.tenants()) == ["acme", "globex"]
    assert len(chroma_store.documents_for_tenant("acme")) == 2
    assert len(chroma_store.documents_for_tenant("globex")) == 1


def test_chroma_tenant_filter_actually_isolates(chroma_store: Any) -> None:
    rows = chroma_store.search(query="renewal discount", tenant_id="globex", limit=5)
    assert rows, "query should return globex's own document"
    assert all(r["tenant_id"] == "globex" for r in rows)
    assert not any("bespoke discount" in r["content"] for r in rows)


def test_chroma_unfiltered_query_sees_everything(chroma_store: Any) -> None:
    rows = chroma_store.search_unfiltered(query="renewal discount", limit=10)
    owners = {r["tenant_id"] for r in rows}
    assert owners == {"acme", "globex"}, "unfiltered must cross tenants — that is the point"


def test_chroma_isolation_check_passes_on_a_correct_store(chroma_store: Any) -> None:
    from ferryte.oracle.isolation import run_isolation_check
    from ferryte.oracle.runner import Severity

    report = run_isolation_check(
        chroma_store, queries=["renewal discount terms"], backend="chroma:test"
    )
    assert report.filtered_leaks == []
    assert report.semantic_leaks == []
    assert report.severity in {Severity.PASS, Severity.WARN}
    # Blast radius must still be measured and non-zero.
    assert report.unfiltered_exposure


def test_chroma_delete_by_source_removes_and_verifies(chroma_store: Any) -> None:
    assert chroma_store.count_for_source("s1") == 2
    removed = chroma_store.delete_by_source("s1")
    assert removed == 2
    assert chroma_store.count_for_source("s1") == 0
    # The real check: content is gone from the store, not merely unranked.
    assert chroma_store.raw_rows_containing("bespoke discount") == []
    assert chroma_store.count_for_source("s2") == 1, "other sources untouched"


# --------------------------------------------------------------------- Qdrant

qdrant_client = pytest.importorskip("qdrant_client", reason="qdrant-client not installed")


@pytest.fixture()
def qdrant_store(tmp_path: Any) -> Any:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    from ferryte.adapters.qdrant import QdrantAdapter, QdrantStore
    from ferryte.config import get_config, set_config

    cfg = get_config()
    cfg.state_dir = tmp_path
    set_config(cfg)

    client = QdrantClient(":memory:")
    name = f"ferryte_test_{uuid.uuid4().hex[:8]}"
    client.create_collection(
        name, vectors_config=VectorParams(size=64, distance=Distance.COSINE)
    )
    store = QdrantStore(client=client, collection=name, embedder=_vec)
    QdrantAdapter().patch(store)
    for content, tenant, source in SEED:
        store.add(content=content, tenant_id=tenant, source_id=source)
    return store


def test_qdrant_tenant_discovery_and_enumeration(qdrant_store: Any) -> None:
    assert sorted(qdrant_store.tenants()) == ["acme", "globex"]
    assert len(qdrant_store.documents_for_tenant("acme")) == 2


def test_qdrant_payload_filter_actually_isolates(qdrant_store: Any) -> None:
    rows = qdrant_store.search(query="renewal discount", tenant_id="globex", limit=5)
    assert rows
    assert all(r["tenant_id"] == "globex" for r in rows)


def test_qdrant_unfiltered_query_crosses_tenants(qdrant_store: Any) -> None:
    rows = qdrant_store.search_unfiltered(query="renewal discount", limit=10)
    assert {r["tenant_id"] for r in rows} == {"acme", "globex"}


def test_qdrant_works_on_modern_client_api(qdrant_store: Any) -> None:
    """Regression guard for the query_points/search API split.

    The first live run of this adapter crashed here. If a future qdrant-client
    renames the method again, this fails loudly instead of silently returning
    no results — which would otherwise render as a false PASS on an isolation
    report, the worst possible bug for this product.
    """
    rows = qdrant_store.search(query="onboarding checklist", tenant_id="globex", limit=5)
    assert rows, "vector query returned nothing — API drift, not a clean store"
    assert rows[0].get("score") is not None


def test_qdrant_delete_by_source_removes_and_verifies(qdrant_store: Any) -> None:
    assert qdrant_store.count_for_source("s1") == 2
    removed = qdrant_store.delete_by_source("s1")
    assert removed == 2
    assert qdrant_store.count_for_source("s1") == 0
    assert qdrant_store.count_for_source("s2") == 1


def test_qdrant_isolation_check_end_to_end(qdrant_store: Any) -> None:
    from ferryte.oracle.isolation import run_isolation_check

    report = run_isolation_check(
        qdrant_store, queries=["renewal discount terms"], backend="qdrant:test"
    )
    assert report.filtered_leaks == []
    assert report.tenants_checked and len(report.tenants_checked) == 2
    assert report.queries_run > 0
