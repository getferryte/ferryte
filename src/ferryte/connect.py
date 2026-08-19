"""Connect to a memory backend from a connection string.

One function, ``open_store``, so the CLI, the Cloud service and a notebook all
resolve a backend the same way. Everything here is optional-dependency-safe: if
a driver is missing you get an actionable install message, never a bare
``ModuleNotFoundError`` from three frames deep.

Supported forms::

    postgres://user:pass@host/db          -> pgvector (needs [pgvector])
    postgresql://...                       -> same
    chroma://./path/to/db#collection       -> local persistent Chroma
    chroma+http://host:8000#collection     -> remote Chroma
    qdrant://host:6333#collection          -> Qdrant
    qdrant+https://host#collection         -> Qdrant over TLS
    memory://                              -> the built-in in-memory store (demos/tests)
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from .adapters.base import BackendKind


@dataclass
class OpenedStore:
    """A connected store plus the metadata callers need to report honestly."""

    store: Any
    backend: BackendKind
    label: str
    notes: list[str]

    def close(self) -> None:
        closer = getattr(self.store, "close", None)
        if callable(closer):
            with contextlib.suppress(Exception):  # best-effort cleanup
                closer()


def open_store(
    uri: str,
    *,
    table: str | None = None,
    schema: str | None = None,
    tenant_column: str = "tenant_id",
    source_column: str = "source_id",
    content_column: str = "content",
    id_column: str = "id",
    embedding_column: str | None = "embedding",
    embedder: Any | None = None,
) -> OpenedStore:
    """Open ``uri`` and return a store implementing the isolation-check surface."""
    parsed = urlparse(uri)
    scheme = (parsed.scheme or "").lower()
    notes: list[str] = []

    if scheme in {"postgres", "postgresql", "pgvector"}:
        from .adapters.pgvector import PgVectorSchema, PgVectorStore

        dsn = uri
        if scheme == "pgvector":  # normalise to something psycopg accepts
            dsn = "postgresql://" + uri.split("://", 1)[1]
        pg_schema = PgVectorSchema(
            table=table or "memories",
            schema=schema,
            id_column=id_column,
            content_column=content_column,
            embedding_column=embedding_column,
            tenant_column=tenant_column,
            source_column=source_column,
        )
        store = PgVectorStore.connect(dsn, schema=pg_schema, embedder=embedder)
        if embedder is None:
            notes.append(
                "No embedder supplied for pgvector: retrieval probes use a lexical scan. "
                "Exact-token leaks are detected; paraphrase-level leaks may be missed."
            )
        return OpenedStore(
            store=store,
            backend=BackendKind.VECTOR,
            label=f"pgvector:{pg_schema.qualified()}",
            notes=notes,
        )

    if scheme in {"chroma", "chroma+http", "chroma+https"}:
        from .adapters.chroma import ChromaStore

        collection = parsed.fragment or table or "memories"
        if scheme == "chroma":
            path = (parsed.netloc or "") + (parsed.path or "")
            chroma_store = ChromaStore.connect(
                collection=collection,
                path=path or None,
                tenant_key=tenant_column,
                source_key=source_column,
            )
            label = f"chroma:{path or 'ephemeral'}#{collection}"
        else:
            chroma_store = ChromaStore.connect(
                collection=collection,
                host=parsed.hostname or "localhost",
                port=parsed.port or 8000,
                tenant_key=tenant_column,
                source_key=source_column,
            )
            label = f"chroma:{parsed.hostname}:{parsed.port or 8000}#{collection}"
        notes.append(
            "Chroma embeds queries with its own embedding function, so semantic-neighbour "
            "probing is meaningful here."
        )
        return OpenedStore(
            store=chroma_store, backend=BackendKind.VECTOR, label=label, notes=notes
        )

    if scheme in {"qdrant", "qdrant+http", "qdrant+https"}:
        from .adapters.qdrant import QdrantStore

        collection = parsed.fragment or table or "memories"
        url = None
        if scheme == "qdrant+https":
            url = f"https://{parsed.hostname}" + (f":{parsed.port}" if parsed.port else "")
        qdrant_store = QdrantStore.connect(
            collection=collection,
            url=url,
            host=parsed.hostname or "localhost",
            port=parsed.port or 6333,
            embedder=embedder,
        )
        qdrant_store.tenant_key = tenant_column
        qdrant_store.source_key = source_column
        qdrant_store.content_key = content_column
        if embedder is None:
            notes.append(
                "No embedder supplied for Qdrant: probes scroll payloads and match "
                "substrings instead of running vector search. Paraphrase-level leaks "
                "may be missed."
            )
        return OpenedStore(
            store=qdrant_store,
            backend=BackendKind.VECTOR,
            label=f"qdrant:{parsed.hostname}#{collection}",
            notes=notes,
        )

    if scheme in {"memory", "inmemory", ""}:
        from .adapters.vector import InMemoryVectorStore

        notes.append(
            "Using the built-in in-memory store. This is a reference implementation for "
            "demos and tests, not a production backend."
        )
        return OpenedStore(
            store=_InMemoryIsolationShim(InMemoryVectorStore()),
            backend=BackendKind.VECTOR,
            label="memory://",
            notes=notes,
        )

    raise ValueError(
        f"Unrecognised backend URI scheme: {scheme!r}.\n"
        "Supported: postgres://, chroma://, chroma+http://, qdrant://, memory://"
    )


class _InMemoryIsolationShim:
    """Adapt ``InMemoryVectorStore`` to the isolation-check surface.

    The in-memory store returns ``(item, score)`` tuples; the isolation checker
    wants dicts. Rather than change the store (which the demo and several tests
    depend on), translate here.
    """

    def __init__(self, inner: Any) -> None:
        self.inner = inner

    def add(self, **kwargs: Any) -> str:
        return self.inner.add(**kwargs)

    def search(
        self, *, query: str, tenant_id: str | None = None, limit: int = 5
    ) -> list[dict[str, Any]]:
        return [
            self._row(item, score)
            for item, score in self.inner.search(query=query, tenant_id=tenant_id, limit=limit)
        ]

    def search_unfiltered(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return [
            self._row(item, score)
            for item, score in self.inner.search(query=query, tenant_id=None, limit=limit)
        ]

    def raw_rows_containing(self, needle: str, *, limit: int = 200) -> list[dict[str, Any]]:
        out = [self._row(it, None) for it in self.inner.raw_items_containing(needle)]
        return out[:limit]

    def documents_for_tenant(self, tenant_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in self.inner.raw_items():
            if getattr(item, "deleted", False):
                continue
            if str(getattr(item, "tenant_id", "")) != tenant_id:
                continue
            out.append(self._row(item, None))
            if len(out) >= limit:
                break
        return out

    def tenants(self, *, limit: int = 100) -> list[str]:
        seen: list[str] = []
        for item in self.inner.raw_items():
            tid = getattr(item, "tenant_id", None)
            if tid and str(tid) not in seen:
                seen.append(str(tid))
            if len(seen) >= limit:
                break
        return seen

    def delete_by_source(self, source_id: str) -> int:
        return self.inner.delete_by_source(source_id)

    def count_for_source(self, source_id: str) -> int:
        return sum(
            1
            for it in self.inner.raw_items()
            if not getattr(it, "deleted", False)
            and source_id in str(getattr(it, "metadata", {}).get("absorbed_sources", []))
        )

    @staticmethod
    def _row(item: Any, score: float | None) -> dict[str, Any]:
        return {
            "id": getattr(item, "artifact_id", ""),
            "content": getattr(item, "content", ""),
            "tenant_id": getattr(item, "tenant_id", None),
            "score": score,
            "metadata": dict(getattr(item, "metadata", {}) or {}),
        }
