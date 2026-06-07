"""SQLite-backed persistence for the lineage graph and retrieval traces.

We use the stdlib ``sqlite3`` module so the OSS install has zero binary deps.
DuckDB can be swapped in later for the hosted product; the schema stays the same.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
import threading
import time
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    source_id   TEXT PRIMARY KEY,
    tenant_id   TEXT,
    revoked_at  REAL,
    metadata    TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id  TEXT PRIMARY KEY,
    backend      TEXT NOT NULL,
    kind         TEXT NOT NULL,
    tenant_id    TEXT,
    content      TEXT,
    created_at   REAL NOT NULL,
    deleted_at   REAL,
    metadata     TEXT
);

CREATE TABLE IF NOT EXISTS derivations (
    artifact_id  TEXT NOT NULL,
    source_id    TEXT NOT NULL,
    confidence   REAL NOT NULL DEFAULT 1.0,
    PRIMARY KEY (artifact_id, source_id),
    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id),
    FOREIGN KEY (source_id)   REFERENCES sources(source_id)
);
CREATE INDEX IF NOT EXISTS idx_derivations_source ON derivations(source_id);

CREATE TABLE IF NOT EXISTS retrievals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    backend      TEXT NOT NULL,
    query        TEXT NOT NULL,
    artifact_id  TEXT,
    content      TEXT,
    score        REAL,
    tenant_id    TEXT,
    occurred_at  REAL NOT NULL,
    metadata     TEXT
);
CREATE INDEX IF NOT EXISTS idx_retrievals_artifact ON retrievals(artifact_id);
CREATE INDEX IF NOT EXISTS idx_retrievals_query    ON retrievals(query);

CREATE TABLE IF NOT EXISTS blindspots (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    backend      TEXT NOT NULL,
    kind         TEXT NOT NULL,
    detail       TEXT NOT NULL,
    observed_at  REAL NOT NULL
);

-- J2: actions the agent took using retrieved memory. A leak that drove an action
-- (sent an email, signed a contract) is *propagated* — deleting the source can't
-- undo it. This is a second kind of blast radius beyond the recallable store.
CREATE TABLE IF NOT EXISTS actions (
    action_id    TEXT PRIMARY KEY,
    kind         TEXT NOT NULL,
    tenant_id    TEXT,
    detail       TEXT,
    occurred_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS action_inputs (
    action_id    TEXT NOT NULL,
    artifact_id  TEXT NOT NULL,
    PRIMARY KEY (action_id, artifact_id)
);
CREATE INDEX IF NOT EXISTS idx_action_inputs_artifact ON action_inputs(artifact_id);
"""


def _now() -> float:
    return time.time()


def _dumps(value: dict[str, Any] | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value, sort_keys=True, default=str)


def _loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


class LineageStore:
    """Thread-safe SQLite wrapper around the lineage schema."""

    def __init__(
        self,
        path: Path | str,
        *,
        fingerprint_mode: bool = False,
        fingerprint_salt: str | None = None,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fingerprint_mode = fingerprint_mode
        # a per-store salt makes fingerprints non-reversible (no rainbow tables)
        # and uncorrelatable across deployments; explicit salt enables reproducibility.
        self._salt = (fingerprint_salt or secrets.token_hex(16)).encode("utf-8")
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_SCHEMA)

    def _fp(self, text: str | None) -> str | None:
        """In fingerprint mode, replace raw text with a salted HMAC-SHA256 digest
        so the local DB never persists the sensitive content itself."""
        if not self.fingerprint_mode or text is None:
            return text
        digest = hmac.new(self._salt, text.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
        return f"fp:sha256:{digest}"

    @contextmanager
    def _cursor(self) -> Iterator[sqlite3.Cursor]:
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
            finally:
                cur.close()

    # ----- writes ------------------------------------------------------------

    def upsert_source(
        self,
        *,
        source_id: str,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO sources (source_id, tenant_id, metadata)
                VALUES (?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    tenant_id = COALESCE(excluded.tenant_id, sources.tenant_id),
                    metadata  = COALESCE(excluded.metadata,  sources.metadata);
                """,
                (source_id, tenant_id, _dumps(metadata)),
            )

    def mark_source_revoked(self, source_id: str, *, at: float | None = None) -> None:
        ts = at if at is not None else _now()
        with self._cursor() as cur:
            cur.execute(
                "UPDATE sources SET revoked_at = ? WHERE source_id = ?",
                (ts, source_id),
            )

    def record_artifact(
        self,
        *,
        artifact_id: str,
        backend: str,
        kind: str,
        content: str | None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO artifacts (artifact_id, backend, kind, tenant_id, content, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(artifact_id) DO UPDATE SET
                    tenant_id = COALESCE(excluded.tenant_id, artifacts.tenant_id),
                    content   = COALESCE(excluded.content,   artifacts.content),
                    metadata  = COALESCE(excluded.metadata,  artifacts.metadata);
                """,
                (artifact_id, backend, kind, tenant_id, self._fp(content), _now(), _dumps(metadata)),
            )

    def record_derivation(
        self,
        *,
        artifact_id: str,
        source_id: str,
        confidence: float = 1.0,
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO derivations (artifact_id, source_id, confidence)
                VALUES (?, ?, ?)
                ON CONFLICT(artifact_id, source_id) DO UPDATE SET
                    confidence = MAX(derivations.confidence, excluded.confidence);
                """,
                (artifact_id, source_id, confidence),
            )

    def mark_artifact_deleted(self, artifact_id: str, *, at: float | None = None) -> None:
        ts = at if at is not None else _now()
        with self._cursor() as cur:
            cur.execute(
                "UPDATE artifacts SET deleted_at = ? WHERE artifact_id = ?",
                (ts, artifact_id),
            )

    def record_retrieval(
        self,
        *,
        backend: str,
        query: str,
        artifact_id: str | None,
        content: str | None,
        score: float | None,
        tenant_id: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO retrievals (backend, query, artifact_id, content, score, tenant_id, occurred_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    backend,
                    self._fp(query),
                    artifact_id,
                    self._fp(content),
                    score,
                    tenant_id,
                    _now(),
                    _dumps(metadata),
                ),
            )

    def record_action(
        self,
        *,
        action_id: str,
        kind: str,
        artifact_ids: Iterable[str],
        tenant_id: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO actions (action_id, kind, tenant_id, detail, occurred_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(action_id) DO UPDATE SET
                    kind = excluded.kind, detail = excluded.detail;
                """,
                (action_id, kind, tenant_id, _dumps(detail), _now()),
            )
            for aid in dict.fromkeys(artifact_ids):
                cur.execute(
                    "INSERT OR IGNORE INTO action_inputs (action_id, artifact_id) VALUES (?, ?);",
                    (action_id, aid),
                )

    def actions_consuming_source(self, source_id: str) -> list[dict[str, Any]]:
        """Actions that consumed *any* artifact derived from this source — i.e.
        propagated consequences that deleting the source cannot undo."""
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ac.action_id, ac.kind, ac.tenant_id, ac.detail, ac.occurred_at
                FROM actions ac
                JOIN action_inputs ai ON ai.action_id = ac.action_id
                JOIN derivations d    ON d.artifact_id = ai.artifact_id
                WHERE d.source_id = ?
                ORDER BY ac.occurred_at;
                """,
                (source_id,),
            )
            return [
                {
                    "action_id": r["action_id"],
                    "kind": r["kind"],
                    "tenant_id": r["tenant_id"],
                    "detail": _loads(r["detail"]),
                    "occurred_at": r["occurred_at"],
                }
                for r in cur.fetchall()
            ]

    def record_blindspot(self, *, backend: str, kind: str, detail: str) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO blindspots (backend, kind, detail, observed_at)
                VALUES (?, ?, ?, ?);
                """,
                (backend, kind, detail, _now()),
            )

    # ----- reads -------------------------------------------------------------

    def artifacts_for_source(self, source_id: str) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT a.*, d.confidence
                FROM artifacts a
                JOIN derivations d ON d.artifact_id = a.artifact_id
                WHERE d.source_id = ?;
                """,
                (source_id,),
            )
            return [self._artifact_row(r) for r in cur.fetchall()]

    def sources(self, *, tenant_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM sources"
        args: tuple[Any, ...] = ()
        if tenant_id is not None:
            sql += " WHERE tenant_id = ?"
            args = (tenant_id,)
        with self._cursor() as cur:
            cur.execute(sql, args)
            return [
                {
                    "source_id": r["source_id"],
                    "tenant_id": r["tenant_id"],
                    "revoked_at": r["revoked_at"],
                    "metadata": _loads(r["metadata"]),
                }
                for r in cur.fetchall()
            ]

    def retrievals_for_artifact(
        self, artifact_id: str, *, since: float | None = None
    ) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            if since is None:
                cur.execute(
                    "SELECT * FROM retrievals WHERE artifact_id = ? ORDER BY occurred_at",
                    (artifact_id,),
                )
            else:
                cur.execute(
                    "SELECT * FROM retrievals WHERE artifact_id = ? AND occurred_at >= ? ORDER BY occurred_at",
                    (artifact_id, since),
                )
            return [self._retrieval_row(r) for r in cur.fetchall()]

    def retrievals_matching(
        self,
        *,
        query_substring: str | None = None,
        tenant_id: str | None = None,
        since: float | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        args: list[Any] = []
        if query_substring is not None:
            clauses.append("query LIKE ?")
            args.append(f"%{query_substring}%")
        if tenant_id is not None:
            clauses.append("tenant_id = ?")
            args.append(tenant_id)
        if since is not None:
            clauses.append("occurred_at >= ?")
            args.append(since)
        sql = "SELECT * FROM retrievals"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY occurred_at"
        with self._cursor() as cur:
            cur.execute(sql, tuple(args))
            return [self._retrieval_row(r) for r in cur.fetchall()]

    def all_artifacts(self) -> Iterable[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM artifacts;")
            for r in cur.fetchall():
                yield self._artifact_row(r)

    def blindspots(self) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM blindspots ORDER BY observed_at;")
            return [
                {
                    "backend": r["backend"],
                    "kind": r["kind"],
                    "detail": r["detail"],
                    "observed_at": r["observed_at"],
                }
                for r in cur.fetchall()
            ]

    def counts(self) -> dict[str, int]:
        with self._cursor() as cur:
            out: dict[str, int] = {}
            for table in (
                "sources",
                "artifacts",
                "derivations",
                "retrievals",
                "blindspots",
                "actions",
                "action_inputs",
            ):
                cur.execute(f"SELECT COUNT(*) AS n FROM {table};")
                out[table] = int(cur.fetchone()["n"])
            return out

    def clear(self) -> None:
        with self._cursor() as cur:
            for table in (
                "action_inputs",
                "actions",
                "retrievals",
                "blindspots",
                "derivations",
                "artifacts",
                "sources",
            ):
                cur.execute(f"DELETE FROM {table};")

    # ----- helpers -----------------------------------------------------------

    @staticmethod
    def _artifact_row(r: sqlite3.Row) -> dict[str, Any]:
        return {
            "artifact_id": r["artifact_id"],
            "backend": r["backend"],
            "kind": r["kind"],
            "tenant_id": r["tenant_id"],
            "content": r["content"],
            "created_at": r["created_at"],
            "deleted_at": r["deleted_at"],
            "metadata": _loads(r["metadata"]),
            "confidence": r["confidence"] if "confidence" in r.keys() else 1.0,  # noqa: SIM118
        }

    @staticmethod
    def _retrieval_row(r: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": r["id"],
            "backend": r["backend"],
            "query": r["query"],
            "artifact_id": r["artifact_id"],
            "content": r["content"],
            "score": r["score"],
            "tenant_id": r["tenant_id"],
            "occurred_at": r["occurred_at"],
            "metadata": _loads(r["metadata"]),
        }

    def close(self) -> None:
        with self._lock:
            self._conn.close()
