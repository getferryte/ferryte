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

-- Answers the agent actually produced, and which memories were in context when
-- it produced them. This is the retrieval→answer edge that makes `ferryte why`
-- exact instead of inferential: when an app opts in via ferryte.record_answer(),
-- attribution can anchor on the recorded input set rather than reconstructing
-- causation from content overlap alone.
CREATE TABLE IF NOT EXISTS answers (
    answer_id    TEXT PRIMARY KEY,
    content      TEXT,
    query        TEXT,
    tenant_id    TEXT,
    occurred_at  REAL NOT NULL,
    metadata     TEXT
);
CREATE INDEX IF NOT EXISTS idx_answers_occurred ON answers(occurred_at);

CREATE TABLE IF NOT EXISTS answer_inputs (
    answer_id    TEXT NOT NULL,
    artifact_id  TEXT NOT NULL,
    PRIMARY KEY (answer_id, artifact_id)
);
CREATE INDEX IF NOT EXISTS idx_answer_inputs_artifact ON answer_inputs(artifact_id);

-- Fact supersession (bi-temporal lineage, after Zep/Graphiti's edge-invalidation
-- model): when a newer memory replaces an older belief, we record the edge
-- instead of guessing later. An artifact with a supersession edge that still
-- wins retrieval is a *structurally provable* stale belief.
CREATE TABLE IF NOT EXISTS supersessions (
    old_artifact_id  TEXT NOT NULL,
    new_artifact_id  TEXT NOT NULL,
    reason           TEXT,
    occurred_at      REAL NOT NULL,
    PRIMARY KEY (old_artifact_id, new_artifact_id)
);
CREATE INDEX IF NOT EXISTS idx_supersessions_old ON supersessions(old_artifact_id);
"""

# Full-text index over artifact content, used to prefilter attribution candidates
# on large memory corpora. FTS5 ships with virtually every CPython build; if this
# particular SQLite lacks it we degrade to full scans transparently.
_FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
    artifact_id UNINDEXED,
    content
);
CREATE TRIGGER IF NOT EXISTS artifacts_fts_ai AFTER INSERT ON artifacts BEGIN
    INSERT INTO artifacts_fts (artifact_id, content)
    VALUES (new.artifact_id, COALESCE(new.content, ''));
END;
CREATE TRIGGER IF NOT EXISTS artifacts_fts_au AFTER UPDATE OF content ON artifacts BEGIN
    DELETE FROM artifacts_fts WHERE artifact_id = old.artifact_id;
    INSERT INTO artifacts_fts (artifact_id, content)
    VALUES (new.artifact_id, COALESCE(new.content, ''));
END;
CREATE TRIGGER IF NOT EXISTS artifacts_fts_ad AFTER DELETE ON artifacts BEGIN
    DELETE FROM artifacts_fts WHERE artifact_id = old.artifact_id;
END;
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
            self._fts_enabled = self._init_fts()

    def _init_fts(self) -> bool:
        """Create the FTS index (and backfill it for DBs created before it existed)."""
        try:
            self._conn.executescript(_FTS_SCHEMA)
            cur = self._conn.execute(
                "SELECT (SELECT COUNT(*) FROM artifacts) AS a, "
                "(SELECT COUNT(*) FROM artifacts_fts) AS f;"
            )
            row = cur.fetchone()
            if int(row["a"]) != int(row["f"]):
                self._conn.execute("DELETE FROM artifacts_fts;")
                self._conn.execute(
                    "INSERT INTO artifacts_fts (artifact_id, content) "
                    "SELECT artifact_id, COALESCE(content, '') FROM artifacts;"
                )
            return True
        except sqlite3.OperationalError:
            return False

    def _fp(self, text: str | None) -> str | None:
        """In fingerprint mode, replace raw text with a salted HMAC-SHA256 digest
        so the local DB never persists the sensitive content itself."""
        if not self.fingerprint_mode or text is None:
            return text
        digest = hmac.new(self._salt, text.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
        return f"fp:sha256:{digest}"

    def fingerprint(self, text: str | None) -> str | None:
        """The stored form of ``text`` (identity unless fingerprint mode is on).

        Lets callers compare externally-held text against persisted rows without
        knowing whether this store fingerprints content.
        """
        return self._fp(text)

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

    def record_answer(
        self,
        *,
        answer_id: str,
        content: str | None,
        query: str | None = None,
        tenant_id: str | None = None,
        artifact_ids: Iterable[str] = (),
        metadata: dict[str, Any] | None = None,
        at: float | None = None,
    ) -> None:
        """Record an answer the agent produced and the memories in its context.

        This is the retrieval→answer edge. Apps that call this after each agent
        turn get *exact* attribution from ``ferryte why`` (the recorded input set
        anchors the ranking) instead of content-overlap inference.
        """
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO answers (answer_id, content, query, tenant_id, occurred_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(answer_id) DO UPDATE SET
                    content  = COALESCE(excluded.content,  answers.content),
                    query    = COALESCE(excluded.query,    answers.query),
                    metadata = COALESCE(excluded.metadata, answers.metadata);
                """,
                (
                    answer_id,
                    self._fp(content),
                    self._fp(query),
                    tenant_id,
                    at if at is not None else _now(),
                    _dumps(metadata),
                ),
            )
            for aid in dict.fromkeys(artifact_ids):
                cur.execute(
                    "INSERT OR IGNORE INTO answer_inputs (answer_id, artifact_id) VALUES (?, ?);",
                    (answer_id, aid),
                )

    def record_supersession(
        self,
        *,
        old_artifact_id: str,
        new_artifact_id: str,
        reason: str | None = None,
        at: float | None = None,
    ) -> None:
        """Record that ``new_artifact_id`` supersedes ``old_artifact_id``.

        Bi-temporal edge in the Zep/Graphiti sense: the old belief is invalidated,
        not deleted. If the old artifact still wins retrieval afterwards, that is
        a structurally provable stale belief — no inference needed.
        """
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO supersessions (old_artifact_id, new_artifact_id, reason, occurred_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(old_artifact_id, new_artifact_id) DO UPDATE SET
                    reason = COALESCE(excluded.reason, supersessions.reason);
                """,
                (old_artifact_id, new_artifact_id, reason, at if at is not None else _now()),
            )

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

    def sources_for_artifact(self, artifact_id: str) -> list[dict[str, Any]]:
        """The source(s) a given artifact was derived from, with revocation state.

        The inverse of :meth:`artifacts_for_source` — used by attribution to trace
        a suspected memory back to where it came from and flag revoked origins.
        """
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT s.source_id, s.tenant_id, s.revoked_at, s.metadata, d.confidence
                FROM derivations d
                JOIN sources s ON s.source_id = d.source_id
                WHERE d.artifact_id = ?;
                """,
                (artifact_id,),
            )
            return [
                {
                    "source_id": r["source_id"],
                    "tenant_id": r["tenant_id"],
                    "revoked_at": r["revoked_at"],
                    "metadata": _loads(r["metadata"]),
                    "confidence": r["confidence"],
                }
                for r in cur.fetchall()
            ]

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

    def artifacts_by_ids(self, artifact_ids: Iterable[str]) -> list[dict[str, Any]]:
        ids = list(dict.fromkeys(artifact_ids))
        if not ids:
            return []
        out: list[dict[str, Any]] = []
        # chunk to stay under SQLite's default 999-parameter limit
        with self._cursor() as cur:
            for i in range(0, len(ids), 500):
                chunk = ids[i : i + 500]
                marks = ",".join("?" * len(chunk))
                cur.execute(f"SELECT * FROM artifacts WHERE artifact_id IN ({marks});", chunk)
                out.extend(self._artifact_row(r) for r in cur.fetchall())
        return out

    def candidate_artifact_ids(self, tokens: Iterable[str], *, limit: int = 2000) -> list[str] | None:
        """FTS-prefiltered artifact ids whose content mentions any of ``tokens``.

        Returns ``None`` when FTS is unavailable (caller should full-scan).
        Tokens are alphanumeric (they come from our tokenizer), so quoting each
        one keeps the MATCH expression safe from FTS query syntax.
        """
        if not getattr(self, "_fts_enabled", False):
            return None
        toks = [t for t in dict.fromkeys(tokens) if t][:48]
        if not toks:
            return []
        match = " OR ".join(f'"{t}"' for t in toks)
        try:
            with self._cursor() as cur:
                # BM25 rank ordering so the cap keeps the most lexically relevant
                # memories when the answer's tokens match a huge slice of the corpus.
                cur.execute(
                    "SELECT artifact_id FROM artifacts_fts WHERE artifacts_fts MATCH ? "
                    "ORDER BY rank LIMIT ?;",
                    (match, limit),
                )
                return list(dict.fromkeys(r["artifact_id"] for r in cur.fetchall()))
        except sqlite3.OperationalError:
            return None

    def answers_matching(
        self,
        *,
        tenant_id: str | None = None,
        since: float | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        args: list[Any] = []
        if tenant_id is not None:
            clauses.append("tenant_id = ?")
            args.append(tenant_id)
        if since is not None:
            clauses.append("occurred_at >= ?")
            args.append(since)
        sql = "SELECT * FROM answers"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY occurred_at DESC LIMIT ?"
        args.append(limit)
        with self._cursor() as cur:
            cur.execute(sql, tuple(args))
            return [
                {
                    "answer_id": r["answer_id"],
                    "content": r["content"],
                    "query": r["query"],
                    "tenant_id": r["tenant_id"],
                    "occurred_at": r["occurred_at"],
                    "metadata": _loads(r["metadata"]),
                }
                for r in cur.fetchall()
            ]

    def artifact_ids_for_answer(self, answer_id: str) -> list[str]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT artifact_id FROM answer_inputs WHERE answer_id = ?;",
                (answer_id,),
            )
            return [r["artifact_id"] for r in cur.fetchall()]

    def supersessions_for(self, artifact_id: str) -> list[dict[str, Any]]:
        """Edges where ``artifact_id`` was superseded by a newer artifact."""
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT new_artifact_id, reason, occurred_at
                FROM supersessions WHERE old_artifact_id = ?
                ORDER BY occurred_at;
                """,
                (artifact_id,),
            )
            return [
                {
                    "new_artifact_id": r["new_artifact_id"],
                    "reason": r["reason"],
                    "occurred_at": r["occurred_at"],
                }
                for r in cur.fetchall()
            ]

    def retrieval_query_counts(self) -> dict[str, int]:
        """Distinct-query retrieval fan-out per artifact, in one aggregate pass.

        A memory retrieved across an outlier number of *distinct* queries has the
        access signature of an injected/poisoned record (MINJA-style attacks are
        engineered to be retrieved for many victim queries) — or of an over-broad
        summary polluting every context. Either way it deserves a flag.
        """
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT artifact_id, COUNT(DISTINCT query) AS n
                FROM retrievals
                WHERE artifact_id IS NOT NULL
                GROUP BY artifact_id;
                """
            )
            return {r["artifact_id"]: int(r["n"]) for r in cur.fetchall()}

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
                "answers",
                "answer_inputs",
                "supersessions",
            ):
                cur.execute(f"SELECT COUNT(*) AS n FROM {table};")
                out[table] = int(cur.fetchone()["n"])
            return out

    def clear(self) -> None:
        with self._cursor() as cur:
            for table in (
                "answer_inputs",
                "answers",
                "supersessions",
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
