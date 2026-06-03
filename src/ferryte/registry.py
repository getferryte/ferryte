"""Adapter registry.

Adapters self-register at import time. ``ferryte.instrument()`` then asks the
registry for everything it knows about and tries to detect each one in the
running process.
"""

from __future__ import annotations

from .adapters.base import Adapter, BackendKind

_REGISTRY: dict[str, type[Adapter]] = {}


def register_adapter(cls: type[Adapter]) -> type[Adapter]:
    """Decorator: register an adapter class by ``cls.name``."""
    name = getattr(cls, "name", cls.__name__)
    _REGISTRY[name] = cls
    return cls


def get_registered() -> list[type[Adapter]]:
    return list(_REGISTRY.values())


def find_by_backend(backend: BackendKind) -> list[type[Adapter]]:
    return [cls for cls in _REGISTRY.values() if getattr(cls, "backend", None) == backend]


def clear_for_tests() -> None:
    _REGISTRY.clear()
