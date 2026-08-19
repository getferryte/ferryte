"""Adapter for pgvector (PostgreSQL + the ``vector`` extension).

Two objects live here, and the split matters:

* :class:`PgVectorStore` — a thin, *schema-configurable* handle over an existing
  ``psycopg`` connection. It does not own your schema and does not migrate
  anything. You tell it which table and which columns hold content / embedding /
  tenant / source, and it speaks SQL against them. This is what lets Ferryte
  point at a **production table it has never seen before** and probe it.
* :class:`PgVectorAdapter` — the five-hook :class:`~ferryte.adapters.base.Adapter`
  implementation that instruments a ``PgVectorStore``.

Design notes, stated plainly because they bound what the tool can honestly claim:

* **Embeddings are yours, not ours.** A real pgvector table stores vectors from
  whatever model you embed with. Ferryte cannot reproduce those vectors, so
  ``probe()`` takes an optional ``embedder``. Supply one and we run true vector
  similarity (``<=>``). Omit it and we fall back to a lexical ``ILIKE`` scan and
  record a **blind spot** saying semantic-neighbour leaks may be missed. The
  fallback is genuinely sufficient for canary detection (markers are
  high-entropy tokens) and genuinely insufficient for paraphrase detection. We
  say so rather than papering over it.
* **Deletes are real.** ``delete_source`` issues an actual ``DELETE`` against
  your table and then **re-probes** to verify the rows are gone. The
  verification is the product; the delete is the easy part.
* **Identifiers are validated, not interpolated blindly.** Table and column
  names are checked against a strict identifier pattern and quoted, because they
  arrive from config and end up in SQL.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from ..context import current_context
from ..lineage import get_lineage
from .base import AdapterCapability, BackendKind, RetrievalRecord, WriteRecord

# Postgres identifiers we are willing to place into SQL. Deliberately strict:
# unquoted-safe characters only, so a hostile config value cannot break out.
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")

Embedder = Callable[[str], Sequence[float]]


def _ident(name: str, *, what: str) -> str:
    """Validate and double-quote a Postgres identifier."""
    if not _IDENT_RE.match(name or ""):
        raise ValueError(
            f"Unsafe or empty {what}: {name!r}. "
            "Ferryte only accepts plain identifiers ([A-Za-z_][A-Za-z0-9_$]*)."
        )
    return f'"{name}"'


def _qualified(schema: str | None, table: str) -> str:
    if schema:
        return f"{_ident(schema, what='schema')}.{_ident(table, what='table')}"
    return _ident(table, what="table")


def _vector_literal(vec: Sequence[float]) -> str:
    """pgvector accepts a bracketed float list as text, e.g. '[0.1,0.2]'."""
    return "[" + ",".join(f"{float(v):.9g}" for v in vec) + "]"


@dataclass
class PgVectorSchema:
    """Where the interesting columns live in the user's own table."""

    table: str = "memories"
    schema: str | None = None
    id_column: str = "id"
    content_column: str = "content"
    embedding_column: str | None = "embedding"
    tenant_column: str | None = "tenant_id"
    source_column: str | None = "source_id"
    metadata_column: str | None = None

    def qualified(self) -> str:
        return _qualified(self.schema, self.table)


@dataclass
class PgVectorStore:
    """A minimal, schema-agnostic handle over a pgvector table.

    ``connection`` is any DBAPI-ish connection exposing ``cursor()`` — in
    practice ``psycopg.connect(...)`` (psycopg 3) or ``psycopg2.connect(...)``.
    Ferryte never opens the connection for you unless you call :meth:`connect`.
    """

    connection: Any
    schema: PgVectorSchema = field(default_factory=PgVectorSchema)
    embedder: Embedder | None = None
    autocommit: bool = True

    # populated by the adapter when instrumented
    _ferryte_patched: bool = False

    # ------------------------------------------------------------------ setup

    @classmethod
    def connect(
        cls,
        dsn: str,
        *,
        schema: PgVectorSchema | None = None,
        embedder: Embedder | None = None,
    ) -> PgVectorStore:
        """Open a connection from a DSN. Requires ``psycopg`` (or ``psycopg2``).

        Raises a clear ImportError rather than a confusing NameError if the
        driver is missing, because "install the extra" is an actionable message
        and ``ModuleNotFoundError: psycopg`` from inside a library is not.
        """
        conn = _connect_dsn(dsn)
        return cls(connection=conn, schema=schema or PgVectorSchema(), embedder=embedder)

    def close(self) -> None:
        with _suppress():
            self.connection.close()

    # ------------------------------------------------------------------ writes

    def add(
        self,
        *,
        content: str,
        source_id: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Insert one row. Returns the new row's id as a string.

        Only used for seeding canaries into a scratch/staging table — Ferryte
        never writes to a table it is only auditing.
        """
        s = self.schema
        cols = [s.content_column]
        vals: list[Any] = [content]
        if s.embedding_column and self.embedder is not None:
            cols.append(s.embedding_column)
            vals.append(_vector_literal(self.embedder(content)))
        if s.tenant_column and tenant_id is not None:
            cols.append(s.tenant_column)
            vals.append(tenant_id)
        if s.source_column and source_id is not None:
            cols.append(s.source_column)
            vals.append(source_id)
        if s.metadata_column and metadata:
            import json as _json

            cols.append(s.metadata_column)
            vals.append(_json.dumps(metadata))

        col_sql = ", ".join(_ident(c, what="column") for c in cols)
        ph = ", ".join(["%s"] * len(vals))
        sql = (
            f"INSERT INTO {s.qualified()} ({col_sql}) VALUES ({ph}) "
            f"RETURNING {_ident(s.id_column, what='id column')}"
        )
        with self.connection.cursor() as cur:
            cur.execute(sql, vals)
            row = cur.fetchone()
        self._maybe_commit()
        return str(row[0]) if row else ""

    # --------------------------------------------------------------- retrieval

    def search(
        self,
        *,
        query: str,
        tenant_id: str | None = None,
        limit: int = 5,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        """Return up to ``limit`` rows most relevant to ``query``.

        Uses real vector similarity when an embedder is available and the table
        has an embedding column; otherwise falls back to a lexical scan.
        """
        _ = include_deleted  # pgvector has no soft-delete convention; rows are gone or not
        s = self.schema
        select_cols = [s.id_column, s.content_column]
        if s.tenant_column:
            select_cols.append(s.tenant_column)
        if s.source_column:
            select_cols.append(s.source_column)
        col_sql = ", ".join(_ident(c, what="column") for c in select_cols)

        tenant_clause: str | None = None
        if tenant_id is not None and s.tenant_column:
            tenant_clause = f"{_ident(s.tenant_column, what='tenant column')} = %s"

        use_vector = bool(s.embedding_column) and self.embedder is not None
        params: list[Any] = []
        if use_vector:
            emb_col = _ident(s.embedding_column, what="embedding column")  # type: ignore[arg-type]
            vec = _vector_literal(self.embedder(query))  # type: ignore[misc]
            # Placeholder order must mirror the SQL exactly:
            #   1) SELECT ... <=> %s   2) WHERE tenant = %s   3) ORDER BY <=> %s   4) LIMIT %s
            sql = (
                f"SELECT {col_sql}, {emb_col} <=> %s::vector AS _ferryte_distance "
                f"FROM {s.qualified()}"
            )
            params.append(vec)
            if tenant_clause:
                sql += f" WHERE {tenant_clause}"
                params.append(tenant_id)
            sql += f" ORDER BY {emb_col} <=> %s::vector LIMIT %s"
            params.extend([vec, limit])
        else:
            where = [f"{_ident(s.content_column, what='content column')} ILIKE %s"]
            params.append(f"%{query}%")
            if tenant_clause:
                where.append(tenant_clause)
                params.append(tenant_id)
            sql = f"SELECT {col_sql} FROM {s.qualified()} WHERE " + " AND ".join(where)
            sql += " LIMIT %s"
            params.append(limit)
            get_lineage().record_blindspot(
                backend=BackendKind.VECTOR.value,
                kind="lexical_fallback",
                detail=(
                    "pgvector probe ran without an embedder, so retrieval used a lexical "
                    "ILIKE scan. Exact-token (canary) leaks are still detected; "
                    "paraphrased or semantic-neighbour leaks may be missed."
                ),
            )

        with self.connection.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        out: list[dict[str, Any]] = []
        for row in rows:
            rec: dict[str, Any] = {}
            for i, c in enumerate(select_cols):
                rec[c] = row[i]
            if use_vector and len(row) > len(select_cols):
                distance = float(row[len(select_cols)])
                rec["score"] = 1.0 - distance  # cosine distance -> similarity
            out.append(rec)
        return out

    def raw_rows_containing(self, needle: str, *, limit: int = 200) -> list[dict[str, Any]]:
        """Scan the *store itself*, bypassing retrieval ranking.

        This is the check that catches leaks a well-behaved query would never
        surface: the row is present and reachable, it simply did not rank.
        """
        s = self.schema
        select_cols = [s.id_column, s.content_column]
        if s.tenant_column:
            select_cols.append(s.tenant_column)
        if s.source_column:
            select_cols.append(s.source_column)
        col_sql = ", ".join(_ident(c, what="column") for c in select_cols)
        sql = (
            f"SELECT {col_sql} FROM {s.qualified()} "
            f"WHERE {_ident(s.content_column, what='content column')} ILIKE %s LIMIT %s"
        )
        with self.connection.cursor() as cur:
            cur.execute(sql, [f"%{needle}%", limit])
            rows = cur.fetchall()
        return [{c: row[i] for i, c in enumerate(select_cols)} for row in rows]

    # ----------------------------------------------------------------- deletes

    def delete_by_source(self, source_id: str) -> int:
        """Issue the real DELETE. Returns rows affected."""
        s = self.schema
        if not s.source_column:
            get_lineage().record_blindspot(
                backend=BackendKind.VECTOR.value,
                kind="no_source_column",
                detail=(
                    "Table has no source column configured, so Ferryte cannot delete "
                    "by source. Deletion verification is not possible for this schema."
                ),
            )
            return 0
        sql = (
            f"DELETE FROM {s.qualified()} "
            f"WHERE {_ident(s.source_column, what='source column')} = %s"
        )
        with self.connection.cursor() as cur:
            cur.execute(sql, [source_id])
            n = cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
        self._maybe_commit()
        return int(n)

    def count_for_source(self, source_id: str) -> int:
        s = self.schema
        if not s.source_column:
            return -1
        sql = (
            f"SELECT COUNT(*) FROM {s.qualified()} "
            f"WHERE {_ident(s.source_column, what='source column')} = %s"
        )
        with self.connection.cursor() as cur:
            cur.execute(sql, [source_id])
            row = cur.fetchone()
        return int(row[0]) if row else 0

    def documents_for_tenant(self, tenant_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        """Enumerate one tenant's rows — powers the semantic-neighbour probe."""
        s = self.schema
        if not s.tenant_column:
            return []
        select_cols = [s.id_column, s.content_column, s.tenant_column]
        col_sql = ", ".join(_ident(c, what="column") for c in select_cols)
        sql = (
            f"SELECT {col_sql} FROM {s.qualified()} "
            f"WHERE {_ident(s.tenant_column, what='tenant column')} = %s LIMIT %s"
        )
        with self.connection.cursor() as cur:
            cur.execute(sql, [tenant_id, limit])
            rows = cur.fetchall()
        return [
            {"id": r[0], "content": r[1], "tenant_id": r[2]}
            for r in rows
        ]

    def tenants(self, *, limit: int = 100) -> list[str]:
        """Distinct tenant values — used to auto-discover tenants for isolation checks."""
        s = self.schema
        if not s.tenant_column:
            return []
        sql = (
            f"SELECT DISTINCT {_ident(s.tenant_column, what='tenant column')} "
            f"FROM {s.qualified()} "
            f"WHERE {_ident(s.tenant_column, what='tenant column')} IS NOT NULL LIMIT %s"
        )
        with self.connection.cursor() as cur:
            cur.execute(sql, [limit])
            rows = cur.fetchall()
        return [str(r[0]) for r in rows]

    # ---------------------------------------------------------------- internal

    def _maybe_commit(self) -> None:
        if not self.autocommit:
            return
        with _suppress():
            self.connection.commit()


class PgVectorAdapter:
    """Five-hook adapter over :class:`PgVectorStore`."""

    name: str = "pgvector"
    backend: BackendKind = BackendKind.VECTOR
    capabilities: frozenset[AdapterCapability] = frozenset(
        {
            AdapterCapability.WRITE_CAPTURE,
            AdapterCapability.READ_CAPTURE,
            AdapterCapability.SOURCE_DELETE,
            AdapterCapability.TENANT_SCOPING,
            AdapterCapability.DERIVED_ENUMERATION,
        }
    )

    def patch(self, client: PgVectorStore) -> PgVectorStore:
        if getattr(client, "_ferryte_patched", False):
            return client
        lineage = get_lineage()
        original_add = client.add
        original_search = client.search
        original_delete = client.delete_by_source

        def add(
            *,
            content: str,
            source_id: str | None = None,
            tenant_id: str | None = None,
            metadata: dict[str, Any] | None = None,
        ) -> str:
            ctx = current_context()
            sid = source_id or ctx.source_id
            tid = tenant_id or ctx.tenant_id
            artifact_id = original_add(
                content=content, source_id=sid, tenant_id=tid, metadata=metadata
            )
            lineage.record_write(
                WriteRecord(
                    backend=BackendKind.VECTOR,
                    artifact_id=artifact_id,
                    content=content,
                    source_id=sid,
                    tenant_id=tid,
                    kind="raw",
                    metadata=dict(metadata or {}),
                )
            )
            return artifact_id

        def search(
            *,
            query: str,
            tenant_id: str | None = None,
            limit: int = 5,
            include_deleted: bool = False,
        ) -> list[dict[str, Any]]:
            ctx = current_context()
            tid = tenant_id or ctx.tenant_id
            rows = original_search(
                query=query, tenant_id=tid, limit=limit, include_deleted=include_deleted
            )
            s = client.schema
            for row in rows:
                lineage.record_retrieval(
                    RetrievalRecord(
                        backend=BackendKind.VECTOR,
                        query=query,
                        artifact_id=str(row.get(s.id_column, "")),
                        content=str(row.get(s.content_column, "")),
                        score=row.get("score"),
                        tenant_id=str(row.get(s.tenant_column)) if s.tenant_column else tid,
                        metadata={"backend": "pgvector"},
                    )
                )
            return rows

        def delete_by_source(source_id: str) -> int:
            n = original_delete(source_id)
            lineage.mark_source_revoked(source_id)
            # Verification is the product: confirm the rows are actually gone.
            remaining = client.count_for_source(source_id)
            if remaining > 0:
                lineage.record_blindspot(
                    backend=BackendKind.VECTOR.value,
                    kind="incomplete_delete",
                    detail=(
                        f"DELETE for source {source_id} reported {n} rows but "
                        f"{remaining} rows still match. The delete did not fully apply."
                    ),
                )
            return n

        client.add = add  # type: ignore[assignment]
        client.search = search  # type: ignore[assignment]
        client.delete_by_source = delete_by_source  # type: ignore[assignment]
        client._ferryte_patched = True
        client._ferryte_originals = {  # type: ignore[attr-defined]
            "add": original_add,
            "search": original_search,
            "delete_by_source": original_delete,
        }
        return client

    def unpatch(self, client: PgVectorStore) -> None:
        if not getattr(client, "_ferryte_patched", False):
            return
        originals = client._ferryte_originals  # type: ignore[attr-defined]
        client.add = originals["add"]  # type: ignore[assignment]
        client.search = originals["search"]  # type: ignore[assignment]
        client.delete_by_source = originals["delete_by_source"]  # type: ignore[assignment]
        client._ferryte_patched = False

    def delete_source(
        self, client: PgVectorStore, *, source_id: str, tenant_id: str | None = None
    ) -> int:
        _ = tenant_id
        return client.delete_by_source(source_id)

    def list_artifacts_for_source(
        self,
        client: PgVectorStore,
        *,
        source_id: str,
        tenant_id: str | None = None,
    ) -> Iterable[WriteRecord]:
        s = client.schema
        if not s.source_column:
            return []
        sql = (
            f"SELECT {_ident(s.id_column, what='id column')}, "
            f"{_ident(s.content_column, what='content column')} "
            f"FROM {s.qualified()} "
            f"WHERE {_ident(s.source_column, what='source column')} = %s"
        )
        with client.connection.cursor() as cur:
            cur.execute(sql, [source_id])
            rows = cur.fetchall()
        return [
            WriteRecord(
                backend=BackendKind.VECTOR,
                artifact_id=str(r[0]),
                content=str(r[1]),
                source_id=source_id,
                tenant_id=tenant_id,
                kind="raw",
            )
            for r in rows
        ]

    def probe(
        self,
        client: PgVectorStore,
        *,
        query: str,
        tenant_id: str | None = None,
        limit: int = 5,
    ) -> list[RetrievalRecord]:
        rows = client.search(query=query, tenant_id=tenant_id, limit=limit)
        s = client.schema
        return [
            RetrievalRecord(
                backend=BackendKind.VECTOR,
                query=query,
                artifact_id=str(r.get(s.id_column, "")),
                content=str(r.get(s.content_column, "")),
                score=r.get("score"),
                tenant_id=str(r.get(s.tenant_column)) if s.tenant_column else tenant_id,
                metadata={"backend": "pgvector"},
            )
            for r in rows
        ]


# ---------------------------------------------------------------------- utils


def _connect_dsn(dsn: str) -> Any:
    """Open a Postgres connection with whichever driver is installed."""
    try:
        import psycopg  # type: ignore

        return psycopg.connect(dsn, autocommit=True)
    except ImportError:
        pass
    try:
        import psycopg2  # type: ignore

        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        return conn
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "pgvector support needs a Postgres driver. Install one:\n"
            "    pip install 'ferryte[pgvector]'\n"
            "or\n"
            "    pip install psycopg[binary]"
        ) from exc


class _suppress:
    """Tiny context manager: ignore errors from best-effort cleanup calls."""

    def __enter__(self) -> None:
        return None

    def __exit__(self, *exc: Any) -> bool:
        return True
