"""Configuration for Ferryte.

Single global config object; defaults are chosen so `ferryte.instrument()` works
with zero arguments. Environment variables can override.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_state_dir() -> Path:
    explicit = os.environ.get("FERRYTE_STATE_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return Path.cwd() / ".ferryte"


@dataclass
class FerryteConfig:
    """Runtime configuration for Ferryte.

    Attributes:
        state_dir: where the lineage DB and reports live. Defaults to ``./.ferryte``.
        db_path: explicit override for the SQLite lineage DB path.
        capture_retrieval: whether to log every retrieval read into the trace log.
        capture_writes: whether to log every memory write into the lineage graph.
        auto_discover: if True, the CLI tries to import the user's project to detect
            instrumented memory clients.
        strict: if True, raises on adapter errors instead of swallowing them.
    """

    state_dir: Path = field(default_factory=_default_state_dir)
    db_path: Path | None = None
    capture_retrieval: bool = True
    capture_writes: bool = True
    auto_discover: bool = True
    strict: bool = False
    # J3 privacy-preserving lineage: when True, the local lineage DB stores only
    # salted fingerprints of artifact/retrieval content + queries, never the raw
    # text — so Ferryte itself never becomes a second copy of the sensitive data.
    # (Same principle as the Cloud PII boundary, applied locally.)
    fingerprint_mode: bool = field(
        default_factory=lambda: os.environ.get("FERRYTE_FINGERPRINT_MODE", "").lower()
        in ("1", "true", "yes", "on")
    )
    fingerprint_salt: str | None = field(
        default_factory=lambda: os.environ.get("FERRYTE_FINGERPRINT_SALT") or None
    )

    def resolved_db_path(self) -> Path:
        if self.db_path is not None:
            return self.db_path
        return self.state_dir / "lineage.db"

    def ensure_dirs(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / "reports").mkdir(parents=True, exist_ok=True)


_config: FerryteConfig | None = None


def get_config() -> FerryteConfig:
    """Return the process-wide singleton config, creating it if needed."""
    global _config
    if _config is None:
        _config = FerryteConfig()
    return _config


def set_config(cfg: FerryteConfig) -> None:
    """Replace the global config (used by tests and the CLI)."""
    global _config
    _config = cfg
