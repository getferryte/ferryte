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

# Single source of truth is the installed package metadata (pyproject `version`),
# so the CLI/API can never drift from the published version again.
try:
    __version__ = _pkg_version("ferryte")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.0.0+local"
