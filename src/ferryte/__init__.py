"""Ferryte — verification for agent forgetting.

Public API:

    import ferryte
    ferryte.instrument()                  # one-line auto-patch of detected memory clients

    ferryte.tag(source_id=..., tenant_id=...)   # context manager: tag writes happening inside
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from .config import FerryteConfig, get_config
from .context import current_context, tag
from .instrument import instrument, uninstrument
from .lineage import LineageGraph, get_lineage
from .registry import register_adapter


def record_action(
    *,
    action_id: str,
    kind: str,
    artifact_ids,  # type: ignore[no-untyped-def]
    tenant_id: str | None = None,
    detail: dict | None = None,
) -> None:
    """Record that the agent took an action (sent an email, signed a contract,
    made a decision) using the given retrieved artifacts. This builds the
    retrieval→action edge so a later revocation can distinguish a *recallable*
    leak (still in the store, deletable) from a *propagated* one that already
    drove a consequence deletion cannot undo. (J2 — action/consequence lineage.)
    """
    get_lineage().record_action(
        action_id=action_id,
        kind=kind,
        artifact_ids=artifact_ids,
        tenant_id=tenant_id,
        detail=detail,
    )


__all__ = [
    "instrument",
    "uninstrument",
    "tag",
    "current_context",
    "get_lineage",
    "LineageGraph",
    "FerryteConfig",
    "get_config",
    "register_adapter",
    "record_action",
]

# Single source of truth is the installed package metadata (pyproject `version`),
# so the CLI/API can never drift from the published version again.
try:
    __version__ = _pkg_version("ferryte")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.0.0+local"
