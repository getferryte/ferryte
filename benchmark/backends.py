"""Real vector-store backends for the benchmark.

Each implements the same `VectorStore` surface as `InMemoryVS`, so the same
`SummaryMemory` + Ferryte adapter run unchanged on every store. Both Chroma and
Qdrant run locally with NO Docker (Chroma embedded, Qdrant `:memory:`), so the
harness is testable in CI; the same classes also point at Docker/remote servers
for the real benchmark by passing connection args.

A row delete here is a real hard delete (that's what production does); the leak
lives in the summary the app keeps — see memory.py.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import time
import uuid
from collections.abc import Iterable

from .stores import StoredItem


def _absorbed(meta_value: str | list | None) -> list:
    if isinstance(meta_value, list):
        return meta_value
    if isinstance(meta_value, str) and meta_value:
        try:
            return json.loads(meta_value)
        except json.JSONDecodeError:
            return []
    return []


class ChromaVS:
    """Chroma backend. Embedded (no Docker) by default.

    Pass `host`/`port` to target a running Chroma server (docker-compose).
    Embeddings are supplied by the caller, so Chroma's default model never loads.
    """

    name = "chroma"

    def __init__(
        self,
        collection: str = "ferryte_bench",
        *,
        host: str | None = None,
        port: int | None = None,
    ) -> None:
        import chromadb  # noqa: PLC0415 - lazy optional dep

        self._client = (
            chromadb.HttpClient(host=host, port=port)
            if host
            else chromadb.EphemeralClient()
        )
        with contextlib.suppress(Exception):  # fresh collection per run
            self._client.delete_collection(collection)
        self._col = self._client.create_collection(
            collection, metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, item: StoredItem) -> None:
        md = {
            "tenant_id": item.tenant_id or "",
            "source_id": item.source_id or "",
            "kind": item.kind,
            "absorbed_sources": json.dumps(item.metadata.get("absorbed_sources", [])),
        }
        self._col.upsert(
            ids=[item.artifact_id],
            embeddings=[item.embedding],
            documents=[item.content],
            metadatas=[md],
        )

    def query(
        self,
        embedding: list[float],
        *,
        tenant_id: str | None = None,
        limit: int = 5,
        include_deleted: bool = False,
    ) -> list[tuple[StoredItem, float]]:
        where = {"tenant_id": tenant_id} if tenant_id is not None else None
        res = self._col.query(
            query_embeddings=[embedding],
            n_results=limit,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        out: list[tuple[StoredItem, float]] = []
        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        for aid, doc, md, dist in zip(ids, docs, metas, dists):
            out.append((self._to_item(aid, doc, md), 1.0 - float(dist)))
        return out

    def delete_by_source(self, source_id: str, *, tenant_id: str | None = None) -> int:
        got = self._col.get(
            where={"$and": [{"source_id": source_id}, {"kind": "raw"}]},
            include=[],
        )
        ids = got.get("ids") or []
        if ids:
            self._col.delete(ids=ids)
        return len(ids)

    def delete_artifact(self, artifact_id: str) -> None:
        self._col.delete(ids=[artifact_id])

    def items(self) -> Iterable[StoredItem]:
        res = self._col.get(include=["documents", "metadatas"])
        ids = res.get("ids") or []
        docs = res.get("documents") or []
        metas = res.get("metadatas") or []
        return [self._to_item(a, d, m) for a, d, m in zip(ids, docs, metas)]

    def items_containing(self, needle: str) -> list[StoredItem]:
        n = (needle or "").lower()
        return [it for it in self.items() if n in (it.content or "").lower()]

    @staticmethod
    def _to_item(aid: str, doc: str, md: dict) -> StoredItem:
        return StoredItem(
            artifact_id=aid,
            content=doc or "",
            embedding=[],
            tenant_id=(md.get("tenant_id") or None),
            source_id=(md.get("source_id") or None),
            kind=md.get("kind", "raw"),
            metadata={
                "kind": md.get("kind", "raw"),
                "absorbed_sources": _absorbed(md.get("absorbed_sources")),
            },
        )


class QdrantVS:
    """Qdrant backend. In-memory (`:memory:`, no Docker) by default.

    Pass `url` to target a running Qdrant server (docker-compose). The vector
    dimension is inferred from the first upserted embedding.
    """

    name = "qdrant"

    def __init__(self, collection: str = "ferryte_bench", *, url: str | None = None) -> None:
        from qdrant_client import QdrantClient  # noqa: PLC0415 - lazy optional dep

        self._client = QdrantClient(url=url) if url else QdrantClient(location=":memory:")
        self._collection = collection
        self._ready = False

    def _ensure(self, dim: int) -> None:
        if self._ready:
            return
        from qdrant_client import models  # noqa: PLC0415

        if self._client.collection_exists(self._collection):
            self._client.delete_collection(self._collection)
        self._client.create_collection(
            self._collection,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )
        self._ready = True

    def upsert(self, item: StoredItem) -> None:
        from qdrant_client import models  # noqa: PLC0415

        self._ensure(len(item.embedding))
        self._client.upsert(
            self._collection,
            points=[
                models.PointStruct(
                    id=item.artifact_id,
                    vector=item.embedding,
                    payload={
                        "content": item.content,
                        "tenant_id": item.tenant_id,
                        "source_id": item.source_id,
                        "kind": item.kind,
                        "absorbed_sources": item.metadata.get("absorbed_sources", []),
                    },
                )
            ],
        )

    def _tenant_filter(self, tenant_id: str | None, *, extra: list | None = None):
        from qdrant_client import models  # noqa: PLC0415

        must = list(extra or [])
        if tenant_id is not None:
            must.append(
                models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id))
            )
        return models.Filter(must=must) if must else None

    def query(
        self,
        embedding: list[float],
        *,
        tenant_id: str | None = None,
        limit: int = 5,
        include_deleted: bool = False,
    ) -> list[tuple[StoredItem, float]]:
        if not self._ready:
            return []
        resp = self._client.query_points(
            self._collection,
            query=embedding,
            limit=limit,
            query_filter=self._tenant_filter(tenant_id),
            with_payload=True,
        )
        return [(self._to_item(h.id, h.payload or {}), float(h.score)) for h in resp.points]

    def delete_by_source(self, source_id: str, *, tenant_id: str | None = None) -> int:
        from qdrant_client import models  # noqa: PLC0415

        if not self._ready:
            return 0
        flt = models.Filter(
            must=[
                models.FieldCondition(key="source_id", match=models.MatchValue(value=source_id)),
                models.FieldCondition(key="kind", match=models.MatchValue(value="raw")),
            ]
        )
        n = self._client.count(self._collection, count_filter=flt, exact=True).count
        self._client.delete(self._collection, points_selector=models.FilterSelector(filter=flt))
        return n

    def delete_artifact(self, artifact_id: str) -> None:
        from qdrant_client import models  # noqa: PLC0415

        if not self._ready:
            return
        self._client.delete(
            self._collection, points_selector=models.PointIdsList(points=[artifact_id])
        )

    def items(self) -> Iterable[StoredItem]:
        if not self._ready:
            return []
        points, _ = self._client.scroll(
            self._collection, limit=10000, with_payload=True, with_vectors=False
        )
        return [self._to_item(p.id, p.payload or {}) for p in points]

    def items_containing(self, needle: str) -> list[StoredItem]:
        n = (needle or "").lower()
        return [it for it in self.items() if n in (it.content or "").lower()]

    @staticmethod
    def _to_item(pid, payload: dict) -> StoredItem:
        return StoredItem(
            artifact_id=str(pid),
            content=payload.get("content", "") or "",
            embedding=[],
            tenant_id=payload.get("tenant_id"),
            source_id=payload.get("source_id"),
            kind=payload.get("kind", "raw"),
            metadata={
                "kind": payload.get("kind", "raw"),
                "absorbed_sources": payload.get("absorbed_sources", []),
            },
        )


class LanceDBVS:
    """LanceDB backend — the embedded, file-based vector store used in
    enterprise/Harvey-tier production stacks. Runs fully embedded (no server,
    no Docker, no key): we connect to a temp directory by default. Pass ``uri``
    to point at a persistent dataset / object-store path for a real run.

    A row delete is a real hard delete (``DELETE WHERE`` predicate); the leak
    lives in the summary layer the app keeps — same contract as the other stores.
    """

    name = "lancedb"

    def __init__(self, *, uri: str | None = None, table: str = "ferryte_bench") -> None:
        import lancedb  # noqa: PLC0415 - lazy optional dep

        self._db = lancedb.connect(uri or tempfile.mkdtemp(prefix="ferryte_lancedb_"))
        self._table_name = table
        self._tbl = None

    def _ensure(self, dim: int) -> None:
        if self._tbl is not None:
            return
        import pyarrow as pa  # noqa: PLC0415

        schema = pa.schema(
            [
                pa.field("artifact_id", pa.string()),
                pa.field("content", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), dim)),
                pa.field("tenant_id", pa.string()),
                pa.field("source_id", pa.string()),
                pa.field("kind", pa.string()),
                pa.field("absorbed_sources", pa.string()),
            ]
        )
        self._tbl = self._db.create_table(self._table_name, schema=schema, mode="overwrite")

    def upsert(self, item: StoredItem) -> None:
        self._ensure(len(item.embedding))
        # LanceDB has no native upsert-by-pk here; delete-then-add is idempotent.
        self._tbl.delete(f"artifact_id = '{item.artifact_id}'")
        self._tbl.add(
            [
                {
                    "artifact_id": item.artifact_id,
                    "content": item.content,
                    "vector": [float(x) for x in item.embedding],
                    "tenant_id": item.tenant_id or "",
                    "source_id": item.source_id or "",
                    "kind": item.kind,
                    "absorbed_sources": json.dumps(item.metadata.get("absorbed_sources", [])),
                }
            ]
        )

    def query(
        self,
        embedding: list[float],
        *,
        tenant_id: str | None = None,
        limit: int = 5,
        include_deleted: bool = False,
    ) -> list[tuple[StoredItem, float]]:
        if self._tbl is None:
            return []
        q = self._tbl.search(embedding).metric("cosine").limit(limit)
        if tenant_id is not None:
            q = q.where(f"tenant_id = '{tenant_id}'", prefilter=True)
        rows = q.to_list()
        # cosine distance in [0,2]; turn into a similarity score.
        return [(self._to_item(r), 1.0 - float(r.get("_distance", 1.0))) for r in rows]

    def delete_by_source(self, source_id: str, *, tenant_id: str | None = None) -> int:
        if self._tbl is None:
            return 0
        n = sum(1 for it in self.items() if it.source_id == source_id and it.kind == "raw")
        self._tbl.delete(f"source_id = '{source_id}' AND kind = 'raw'")
        return n

    def delete_artifact(self, artifact_id: str) -> None:
        if self._tbl is None:
            return
        self._tbl.delete(f"artifact_id = '{artifact_id}'")

    def items(self) -> Iterable[StoredItem]:
        if self._tbl is None:
            return []
        return [self._to_item(r) for r in self._tbl.to_arrow().to_pylist()]

    def items_containing(self, needle: str) -> list[StoredItem]:
        n = (needle or "").lower()
        return [it for it in self.items() if n in (it.content or "").lower()]

    @staticmethod
    def _to_item(r: dict) -> StoredItem:
        return StoredItem(
            artifact_id=r.get("artifact_id", ""),
            content=r.get("content", "") or "",
            embedding=[],
            tenant_id=(r.get("tenant_id") or None),
            source_id=(r.get("source_id") or None),
            kind=r.get("kind", "raw"),
            metadata={
                "kind": r.get("kind", "raw"),
                "absorbed_sources": _absorbed(r.get("absorbed_sources")),
            },
        )


class PineconeVS:
    """Pinecone backend — the category-defining managed vector DB at scale.

    Managed/serverless: needs ``PINECONE_API_KEY`` (no embedded mode). Each run
    uses a fresh **namespace** inside a per-dimension index, so runs are isolated
    without paying serverless index-creation latency every time.

    Serverless Pinecone cannot delete by metadata filter, so we keep an exact
    local source->ids map (we own every write) and delete by id — that's also how
    a real integration tracks what it wrote. Deletes are eventually consistent, so
    we settle briefly before returning.

    NOTE: pending live validation against a Pinecone account; gated on the key.
    """

    name = "pinecone"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        index_prefix: str = "ferryte-bench",
        cloud: str | None = None,
        region: str | None = None,
        settle_s: float = 6.0,
    ) -> None:
        key = api_key or os.environ.get("PINECONE_API_KEY")
        if not key:
            raise RuntimeError(
                "PINECONE_API_KEY not set — the Pinecone benchmark needs a managed "
                "Pinecone key (no embedded mode). Get one at app.pinecone.io."
            )
        from pinecone import Pinecone  # noqa: PLC0415 - lazy optional dep

        self._pc = Pinecone(api_key=key)
        self._index_prefix = index_prefix
        self._cloud = cloud or os.environ.get("PINECONE_CLOUD", "aws")
        self._region = region or os.environ.get("PINECONE_REGION", "us-east-1")
        self._settle_s = settle_s
        self._namespace = uuid.uuid4().hex[:12]
        self._index = None
        # Local mirror of what we wrote (exact; the store owns all writes).
        self._items: dict[str, StoredItem] = {}
        self._by_source: dict[str, list[str]] = {}

    def _ensure(self, dim: int) -> None:
        if self._index is not None:
            return
        from pinecone import ServerlessSpec  # noqa: PLC0415

        name = f"{self._index_prefix}-{dim}"
        existing = {ix["name"] for ix in self._pc.list_indexes()}
        if name not in existing:
            self._pc.create_index(
                name=name,
                dimension=dim,
                metric="cosine",
                spec=ServerlessSpec(cloud=self._cloud, region=self._region),
            )
        deadline = time.time() + 120
        while time.time() < deadline:
            if self._pc.describe_index(name).status.get("ready"):
                break
            time.sleep(2)
        self._index = self._pc.Index(name)

    def upsert(self, item: StoredItem) -> None:
        self._ensure(len(item.embedding))
        self._index.upsert(
            namespace=self._namespace,
            vectors=[
                {
                    "id": item.artifact_id,
                    "values": [float(x) for x in item.embedding],
                    "metadata": {
                        "content": item.content,
                        "tenant_id": item.tenant_id or "",
                        "source_id": item.source_id or "",
                        "kind": item.kind,
                        "absorbed_sources": json.dumps(
                            item.metadata.get("absorbed_sources", [])
                        ),
                    },
                }
            ],
        )
        self._items[item.artifact_id] = item
        if item.source_id and item.kind == "raw":
            self._by_source.setdefault(item.source_id, []).append(item.artifact_id)

    def query(
        self,
        embedding: list[float],
        *,
        tenant_id: str | None = None,
        limit: int = 5,
        include_deleted: bool = False,
    ) -> list[tuple[StoredItem, float]]:
        if self._index is None:
            return []
        flt = {"tenant_id": {"$eq": tenant_id}} if tenant_id is not None else None
        res = self._index.query(
            namespace=self._namespace,
            vector=[float(x) for x in embedding],
            top_k=limit,
            include_metadata=True,
            filter=flt,
        )
        out: list[tuple[StoredItem, float]] = []
        for m in res.get("matches", []):
            out.append((self._to_item(m.get("id", ""), m.get("metadata") or {}), float(m.get("score", 0.0))))
        return out

    def delete_by_source(self, source_id: str, *, tenant_id: str | None = None) -> int:
        if self._index is None:
            return 0
        ids = [
            aid
            for aid in self._by_source.get(source_id, [])
            if aid in self._items and not self._items[aid].deleted
        ]
        if ids:
            self._index.delete(ids=ids, namespace=self._namespace)
            for aid in ids:
                self._items[aid].deleted = True
            time.sleep(self._settle_s)  # serverless delete is eventually consistent
        return len(ids)

    def delete_artifact(self, artifact_id: str) -> None:
        if self._index is None:
            return
        self._index.delete(ids=[artifact_id], namespace=self._namespace)
        if artifact_id in self._items:
            self._items[artifact_id].deleted = True
        time.sleep(self._settle_s)

    def items(self) -> Iterable[StoredItem]:
        return [it for it in self._items.values() if not it.deleted]

    def items_containing(self, needle: str) -> list[StoredItem]:
        n = (needle or "").lower()
        return [it for it in self.items() if n in (it.content or "").lower()]

    @staticmethod
    def _to_item(aid: str, md: dict) -> StoredItem:
        return StoredItem(
            artifact_id=aid,
            content=md.get("content", "") or "",
            embedding=[],
            tenant_id=(md.get("tenant_id") or None),
            source_id=(md.get("source_id") or None),
            kind=md.get("kind", "raw"),
            metadata={
                "kind": md.get("kind", "raw"),
                "absorbed_sources": _absorbed(md.get("absorbed_sources")),
            },
        )


def _vec_literal(vec: list[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in vec) + "]"


class PgvectorVS:
    """pgvector backend over Postgres. Needs the `vector` extension (the
    `pgvector/pgvector` image ships it). Cosine distance via the `<=>` operator.

    The table is recreated per run so the dimension matches the active embedder.
    """

    name = "pgvector"

    def __init__(
        self,
        *,
        dsn: str = "postgresql://ferryte:ferryte@localhost:5432/ferryte",
        table: str = "ferryte_bench",
    ) -> None:
        import psycopg  # noqa: PLC0415 - lazy optional dep

        self._conn = psycopg.connect(dsn, autocommit=True)
        self._table = table
        self._ready = False
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

    def _ensure(self, dim: int) -> None:
        if self._ready:
            return
        with self._conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {self._table}")
            cur.execute(
                f"CREATE TABLE {self._table} ("
                "artifact_id text PRIMARY KEY, content text, embedding vector(%s), "
                "tenant_id text, source_id text, kind text, absorbed_sources jsonb)" % dim
            )
        self._ready = True

    def upsert(self, item: StoredItem) -> None:
        self._ensure(len(item.embedding))
        with self._conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {self._table} "
                "(artifact_id, content, embedding, tenant_id, source_id, kind, absorbed_sources) "
                "VALUES (%s, %s, %s::vector, %s, %s, %s, %s) "
                "ON CONFLICT (artifact_id) DO UPDATE SET content=EXCLUDED.content, "
                "embedding=EXCLUDED.embedding, kind=EXCLUDED.kind, "
                "absorbed_sources=EXCLUDED.absorbed_sources",
                (
                    item.artifact_id,
                    item.content,
                    _vec_literal(item.embedding),
                    item.tenant_id,
                    item.source_id,
                    item.kind,
                    json.dumps(item.metadata.get("absorbed_sources", [])),
                ),
            )

    def query(
        self,
        embedding: list[float],
        *,
        tenant_id: str | None = None,
        limit: int = 5,
        include_deleted: bool = False,
    ) -> list[tuple[StoredItem, float]]:
        if not self._ready:
            return []
        where = ""
        params: list = [_vec_literal(embedding)]
        if tenant_id is not None:
            where = "WHERE tenant_id = %s"
            params.append(tenant_id)
        params.append(limit)
        sql = (
            "SELECT artifact_id, content, tenant_id, source_id, kind, absorbed_sources, "
            f"1 - (embedding <=> %s::vector) AS score FROM {self._table} {where} "
            "ORDER BY score DESC LIMIT %s"
        )
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return [(self._row_to_item(r), float(r[6])) for r in cur.fetchall()]

    def delete_by_source(self, source_id: str, *, tenant_id: str | None = None) -> int:
        if not self._ready:
            return 0
        with self._conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self._table} WHERE source_id = %s AND kind = 'raw'", (source_id,)
            )
            return cur.rowcount

    def delete_artifact(self, artifact_id: str) -> None:
        if not self._ready:
            return
        with self._conn.cursor() as cur:
            cur.execute(f"DELETE FROM {self._table} WHERE artifact_id = %s", (artifact_id,))

    def items(self) -> Iterable[StoredItem]:
        if not self._ready:
            return []
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT artifact_id, content, tenant_id, source_id, kind, absorbed_sources "
                f"FROM {self._table}"
            )
            return [self._row_to_item(r) for r in cur.fetchall()]

    def items_containing(self, needle: str) -> list[StoredItem]:
        if not self._ready:
            return []
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT artifact_id, content, tenant_id, source_id, kind, absorbed_sources "
                f"FROM {self._table} WHERE content ILIKE %s",
                (f"%{needle}%",),
            )
            return [self._row_to_item(r) for r in cur.fetchall()]

    @staticmethod
    def _row_to_item(r) -> StoredItem:
        absorbed = r[5] if isinstance(r[5], list) else _absorbed(r[5])
        return StoredItem(
            artifact_id=r[0],
            content=r[1] or "",
            embedding=[],
            tenant_id=r[2],
            source_id=r[3],
            kind=r[4] or "raw",
            metadata={"kind": r[4] or "raw", "absorbed_sources": absorbed},
        )
