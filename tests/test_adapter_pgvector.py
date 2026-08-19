"""pgvector adapter tests against a recording fake DBAPI connection.

There is no Postgres in CI, so these do not prove the adapter works against a
live server — they prove the thing that actually broke during development: the
**SQL text and the parameter ordering**. A vector query interleaves placeholders
across SELECT, WHERE and ORDER BY, and getting that order wrong produces a query
that either errors or, worse, silently ranks by the wrong vector.

What is verified here:
  * identifiers are validated and quoted (injection attempt is rejected)
  * the vector path emits placeholders in the order [vec, tenant?, vec, limit]
  * the lexical fallback path emits [pattern, tenant?, limit]
  * delete-by-source issues a real DELETE and then re-counts to verify

What is NOT verified here, and is stated plainly rather than implied:
  * that a real Postgres accepts this SQL
  * that `<=>` returns what we assume on the buyer's pgvector version
Those need a live instance. See `docker-compose.yml` in benchmark/ for one.
"""

from __future__ import annotations

from typing import Any

import pytest

from ferryte.adapters.pgvector import (
    PgVectorAdapter,
    PgVectorSchema,
    PgVectorStore,
    _ident,
)


class FakeCursor:
    def __init__(self, conn: FakeConnection) -> None:
        self.conn = conn
        self.rowcount = 0
        self._rows: list[tuple] = []

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    def execute(self, sql: str, params: Any = None) -> None:
        self.conn.calls.append((" ".join(sql.split()), list(params or [])))
        self._rows = self.conn.next_rows
        self.rowcount = self.conn.next_rowcount

    def fetchone(self) -> tuple | None:
        return self._rows[0] if self._rows else None

    def fetchall(self) -> list[tuple]:
        return list(self._rows)


class FakeConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list]] = []
        self.next_rows: list[tuple] = []
        self.next_rowcount = 0
        self.commits = 0

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1


def embed(text: str) -> list[float]:
    return [float(len(text) % 7), 1.0, 0.5]


@pytest.fixture()
def conn() -> FakeConnection:
    return FakeConnection()


@pytest.fixture()
def store(conn: FakeConnection) -> PgVectorStore:
    return PgVectorStore(
        connection=conn,
        schema=PgVectorSchema(table="memories", schema="public"),
        embedder=embed,
    )


# --------------------------------------------------------------- identifiers


@pytest.mark.parametrize(
    "bad",
    ['memories; DROP TABLE users', 'a"b', "", "1abc", "tbl name", "x'y"],
)
def test_unsafe_identifiers_are_rejected(bad: str) -> None:
    with pytest.raises(ValueError, match="Unsafe or empty"):
        _ident(bad, what="table")


def test_valid_identifiers_are_quoted() -> None:
    assert _ident("memories", what="table") == '"memories"'
    assert _ident("tenant_id", what="column") == '"tenant_id"'


def test_injection_via_schema_config_is_blocked(conn: FakeConnection) -> None:
    evil = PgVectorStore(
        connection=conn,
        schema=PgVectorSchema(table="memories; DROP TABLE users"),
        embedder=embed,
    )
    with pytest.raises(ValueError):
        evil.search(query="anything", tenant_id="acme")
    assert conn.calls == [], "no SQL should reach the connection"


# ------------------------------------------------------------- vector search


def test_vector_search_parameter_order(store: PgVectorStore, conn: FakeConnection) -> None:
    conn.next_rows = [("id1", "some content", "acme", "s1", 0.25)]
    store.search(query="renewal terms", tenant_id="acme", limit=7)

    sql, params = conn.calls[-1]
    assert "<=> %s::vector AS _ferryte_distance" in sql
    assert 'WHERE "tenant_id" = %s' in sql
    assert "ORDER BY" in sql and "LIMIT %s" in sql

    vec = "[" + ",".join(f"{v:.9g}" for v in embed("renewal terms")) + "]"
    # The exact ordering that was wrong in the first draft of this adapter.
    assert params == [vec, "acme", vec, 7]


def test_vector_search_without_tenant_omits_where(
    store: PgVectorStore, conn: FakeConnection
) -> None:
    conn.next_rows = []
    store.search(query="q", limit=3)
    sql, params = conn.calls[-1]
    assert "WHERE" not in sql
    vec = "[" + ",".join(f"{v:.9g}" for v in embed("q")) + "]"
    assert params == [vec, vec, 3]


def test_distance_is_converted_to_similarity(
    store: PgVectorStore, conn: FakeConnection
) -> None:
    conn.next_rows = [("id1", "content", "acme", "s1", 0.25)]
    rows = store.search(query="q", tenant_id="acme")
    assert rows[0]["score"] == pytest.approx(0.75)
    assert rows[0]["id"] == "id1"
    assert rows[0]["tenant_id"] == "acme"


# ----------------------------------------------------------- lexical fallback


def test_lexical_fallback_when_no_embedder(conn: FakeConnection) -> None:
    store = PgVectorStore(connection=conn, schema=PgVectorSchema(), embedder=None)
    conn.next_rows = []
    store.search(query="secret", tenant_id="acme", limit=5)
    sql, params = conn.calls[-1]
    assert "ILIKE" in sql and "<=>" not in sql
    assert params == ["%secret%", "acme", 5]


def test_lexical_fallback_records_a_blind_spot(conn: FakeConnection, tmp_path: Any) -> None:
    """The fallback must never be silent — it changes what the report can claim."""
    from ferryte.config import get_config, set_config
    from ferryte.lineage import get_lineage

    cfg = get_config()
    cfg.state_dir = tmp_path
    set_config(cfg)

    store = PgVectorStore(connection=conn, schema=PgVectorSchema(), embedder=None)
    conn.next_rows = []
    store.search(query="secret", tenant_id="acme")

    blind = get_lineage().blindspots()
    assert any(b.get("kind") == "lexical_fallback" for b in blind)


# ------------------------------------------------------------------- deletes


def test_delete_by_source_issues_real_delete(
    store: PgVectorStore, conn: FakeConnection
) -> None:
    conn.next_rowcount = 3
    n = store.delete_by_source("user_8813")
    sql, params = conn.calls[-1]
    assert sql.startswith('DELETE FROM "public"."memories"')
    assert '"source_id" = %s' in sql
    assert params == ["user_8813"]
    assert n == 3
    assert conn.commits >= 1


def test_delete_without_source_column_is_a_blind_spot_not_a_lie(
    conn: FakeConnection, tmp_path: Any
) -> None:
    from ferryte.config import get_config, set_config

    cfg = get_config()
    cfg.state_dir = tmp_path
    set_config(cfg)

    store = PgVectorStore(
        connection=conn, schema=PgVectorSchema(source_column=None), embedder=embed
    )
    assert store.delete_by_source("x") == 0
    assert conn.calls == [], "must not issue a DELETE it cannot scope"


def test_adapter_flags_incomplete_delete(conn: FakeConnection, tmp_path: Any) -> None:
    """If rows survive the DELETE, that must surface — silence here would be the
    single most damaging failure mode for an attestation."""
    from ferryte.config import get_config, set_config
    from ferryte.lineage import get_lineage

    cfg = get_config()
    cfg.state_dir = tmp_path
    set_config(cfg)

    store = PgVectorStore(connection=conn, schema=PgVectorSchema(), embedder=embed)
    PgVectorAdapter().patch(store)

    conn.next_rowcount = 2
    conn.next_rows = [(5,)]  # count_for_source still returns 5 -> incomplete
    store.delete_by_source("user_1")

    blind = get_lineage().blindspots()
    assert any(b.get("kind") == "incomplete_delete" for b in blind)


# ------------------------------------------------------------- enumeration


def test_documents_for_tenant_shape(store: PgVectorStore, conn: FakeConnection) -> None:
    conn.next_rows = [("id1", "content one", "acme"), ("id2", "content two", "acme")]
    rows = store.documents_for_tenant("acme", limit=10)
    sql, params = conn.calls[-1]
    assert '"tenant_id" = %s' in sql
    assert params == ["acme", 10]
    assert rows[0] == {"id": "id1", "content": "content one", "tenant_id": "acme"}


def test_tenants_discovery(store: PgVectorStore, conn: FakeConnection) -> None:
    conn.next_rows = [("acme",), ("globex",)]
    assert store.tenants() == ["acme", "globex"]
    sql, _ = conn.calls[-1]
    assert "DISTINCT" in sql and "IS NOT NULL" in sql
