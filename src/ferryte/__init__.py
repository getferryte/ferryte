"""Ferryte — verification for agent forgetting.

Public API:

    import ferryte
    ferryte.instrument()                  # one-line auto-patch of detected memory clients

    ferryte.tag(source_id=..., tenant_id=...)   # context manager: tag writes happening inside
"""

from __future__ import annotations

from .config import FerryteConfig, get_config
from .context import current_context, tag
from .instrument import instrument, uninstrument
from .lineage import LineageGraph, get_lineage
from .registry import register_adapter

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
]

__version__ = "0.1.0"
