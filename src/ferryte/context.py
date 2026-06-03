"""Thread- and async-local provenance context.

Anything inside ``with ferryte.tag(source_id=..., tenant_id=...)`` gets that
provenance attached to every adapter-captured write. Adapters that can also
read provenance from explicit kwargs / metadata should prefer those; the
context is the fallback so users get useful lineage with zero call-site changes.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProvenanceContext:
    source_id: str | None = None
    tenant_id: str | None = None
    actor: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)


_EMPTY = ProvenanceContext()

_context_var: ContextVar[ProvenanceContext] = ContextVar("ferryte_context", default=_EMPTY)


def current_context() -> ProvenanceContext:
    """Return the active provenance context (or an empty one)."""
    return _context_var.get()


@contextmanager
def tag(
    *,
    source_id: str | None = None,
    tenant_id: str | None = None,
    actor: str | None = None,
    tags: list[str] | None = None,
) -> Iterator[ProvenanceContext]:
    """Attach provenance to every memory write that happens inside this block.

    Example::

        with ferryte.tag(source_id="doc-42", tenant_id="acme"):
            mem.add(messages=[...])
    """
    parent = current_context()
    merged = ProvenanceContext(
        source_id=source_id or parent.source_id,
        tenant_id=tenant_id or parent.tenant_id,
        actor=actor or parent.actor,
        tags=tuple(tags) if tags is not None else parent.tags,
    )
    token = _context_var.set(merged)
    try:
        yield merged
    finally:
        _context_var.reset(token)
