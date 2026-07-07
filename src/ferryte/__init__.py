"""Ferryte — memory debugging for AI agents.

Public API:

    import ferryte
    ferryte.instrument()                  # one-line auto-patch of detected memory clients

    ferryte.tag(source_id=..., tenant_id=...)   # context manager: tag writes happening inside

    ferryte.record_answer(...)            # optional: answer→memory edge for exact `ferryte why`
    ferryte.record_supersession(...)      # optional: mark a fact replaced (structural staleness)
    ferryte.record_action(...)            # optional: retrieval→action edge (propagated blast radius)
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


def record_answer(
    *,
    answer_id: str,
    content: str,
    artifact_ids,  # type: ignore[no-untyped-def]
    query: str | None = None,
    tenant_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    """Record an answer the agent produced and the memories that were in its
    context. This builds the retrieval→answer edge: with it, ``ferryte why``
    anchors attribution on the exact recorded input set instead of inferring
    causation from content overlap. Call it once per agent turn::

        results = mem.search(query=q, tenant_id=tid)
        answer = llm(q, context=results)
        ferryte.record_answer(
            answer_id=turn_id, content=answer, query=q, tenant_id=tid,
            artifact_ids=[r.artifact_id for r in results],
        )
    """
    get_lineage().record_answer(
        answer_id=answer_id,
        content=content,
        query=query,
        tenant_id=tenant_id,
        artifact_ids=artifact_ids,
        metadata=metadata,
    )


def record_supersession(
    *,
    old_artifact_id: str,
    new_artifact_id: str,
    reason: str | None = None,
) -> None:
    """Record that one memory supersedes another (the newer fact replaces the
    older belief). Bi-temporal invalidation in the Zep/Graphiti sense: the old
    memory isn't deleted, but if it still wins retrieval afterwards, ``ferryte
    why`` reports a structurally provable stale belief instead of a guess.
    """
    get_lineage().record_supersession(
        old_artifact_id=old_artifact_id,
        new_artifact_id=new_artifact_id,
        reason=reason,
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
    "record_answer",
    "record_supersession",
]

# Single source of truth is the installed package metadata (pyproject `version`),
# so the CLI/API can never drift from the published version again.
try:
    __version__ = _pkg_version("ferryte")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.0.0+local"
