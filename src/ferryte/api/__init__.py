"""Local HTTP API consumed by the Next.js dashboard."""

from .server import build_app, serve

__all__ = ["build_app", "serve"]
