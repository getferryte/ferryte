"""``ferryte.instrument()`` — the one-line entry point.

The user calls this once at process start. It:

  1. Imports every adapter shipped with Ferryte and registers it.
  2. Installs an import hook so that subsequently-constructed clients of known
     backends (e.g. ``mem0.Memory()``, ``InMemoryVectorStore()``) are wrapped
     in their adapter automatically.
  3. Returns a small ``Instrumentation`` handle you can pass to ``ferryte.test``
     so the oracle knows which clients to talk to.

The design constraint from the plan: this MUST work with zero arguments and
zero call-site changes. Everything else is opt-in.
"""

from __future__ import annotations

import contextlib
import importlib
import threading
import weakref
from dataclasses import dataclass, field
from typing import Any

from .adapters.base import Adapter, BackendKind
from .config import FerryteConfig, get_config, set_config
from .lineage import get_lineage
from .registry import get_registered, register_adapter

_BUILTIN_ADAPTERS: list[str] = [
    "ferryte.adapters.vector:VectorAdapter",
    "ferryte.adapters.mem0:Mem0Adapter",
]

_lock = threading.RLock()
_installed: bool = False
_handle: Instrumentation | None = None


@dataclass
class TrackedClient:
    """One memory client we are watching."""

    adapter: Adapter
    client: Any
    backend: BackendKind

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"TrackedClient(backend={self.backend.value}, client={type(self.client).__name__})"


@dataclass
class Instrumentation:
    """Process-wide handle returned by ``ferryte.instrument()``."""

    config: FerryteConfig
    adapters: list[Adapter] = field(default_factory=list)
    _clients: weakref.WeakValueDictionary[int, Any] = field(
        default_factory=weakref.WeakValueDictionary
    )
    _adapter_by_client_id: dict[int, Adapter] = field(default_factory=dict)

    def track(self, client: Any, adapter: Adapter) -> Any:
        adapter.patch(client)
        self._clients[id(client)] = client
        self._adapter_by_client_id[id(client)] = adapter
        return client

    def list_clients(self) -> list[TrackedClient]:
        out: list[TrackedClient] = []
        for cid, client in list(self._clients.items()):
            adapter = self._adapter_by_client_id.get(cid)
            if adapter is None:
                continue
            out.append(TrackedClient(adapter=adapter, client=client, backend=adapter.backend))
        return out

    def adapter_for(self, client: Any) -> Adapter | None:
        return self._adapter_by_client_id.get(id(client))


def _load_builtin_adapters() -> list[type[Adapter]]:
    loaded: list[type[Adapter]] = []
    for spec in _BUILTIN_ADAPTERS:
        module_name, attr = spec.split(":", 1)
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        cls = getattr(module, attr, None)
        if cls is None:
            continue
        register_adapter(cls)
        loaded.append(cls)
    return loaded


def _install_constructor_hooks(handle: Instrumentation) -> None:
    """Auto-patch new instances of known backends as they are constructed.

    Wrappers are installed once per class and look up the current handle at
    call time, so re-instrumenting the process (e.g. in tests) still works.
    """
    _wrap_constructor(
        module_path="mem0",
        class_names=("Memory", "MemoryClient", "AsyncMemory"),
        adapter_name="mem0",
    )
    _wrap_constructor(
        module_path="ferryte.adapters.vector",
        class_names=("InMemoryVectorStore",),
        adapter_name="vector",
    )


def _wrap_constructor(
    *,
    module_path: str,
    class_names: tuple[str, ...],
    adapter_name: str,
) -> None:
    try:
        module = importlib.import_module(module_path)
    except Exception:
        return
    for name in class_names:
        cls = getattr(module, name, None)
        if cls is None or getattr(cls, "_ferryte_constructor_wrapped", False):
            continue
        original_init = cls.__init__

        def make_wrapper(orig: Any, target_adapter_name: str) -> Any:
            def wrapper(self: Any, *args: Any, **kwargs: Any) -> None:
                orig(self, *args, **kwargs)
                live = current_instrumentation()
                if live is None:
                    return
                adapter = next(
                    (a for a in live.adapters if a.name == target_adapter_name), None
                )
                if adapter is None:
                    return
                try:
                    live.track(self, adapter)
                except Exception:
                    if get_config().strict:
                        raise

            return wrapper

        cls.__init__ = make_wrapper(original_init, adapter_name)  # type: ignore[method-assign]
        cls._ferryte_constructor_wrapped = True
        cls._ferryte_original_init = original_init


def instrument(
    *,
    config: FerryteConfig | None = None,
    adapters: list[Adapter] | None = None,
    clients: list[Any] | None = None,
) -> Instrumentation:
    """Activate Ferryte.

    Args:
        config: optional ``FerryteConfig`` override; otherwise the global default.
        adapters: explicit adapters to use; defaults to all built-ins.
        clients: pre-existing client instances to patch immediately. New ones
            created later are picked up automatically by the constructor hook.
    """
    global _installed, _handle
    with _lock:
        if config is not None:
            set_config(config)
        cfg = get_config()
        cfg.ensure_dirs()
        get_lineage()  # initialise SQLite eagerly so first write is fast

        if adapters is None:
            _load_builtin_adapters()
            adapters = [cls() for cls in get_registered()]  # type: ignore[call-arg]
        handle = Instrumentation(config=cfg, adapters=list(adapters))
        _install_constructor_hooks(handle)

        if clients:
            for client in clients:
                adapter = _pick_adapter(client, handle.adapters)
                if adapter is not None:
                    handle.track(client, adapter)

        _installed = True
        _handle = handle
        return handle


def _pick_adapter(client: Any, adapters: list[Adapter]) -> Adapter | None:
    """Heuristic: match by module path of the client's class."""
    module = type(client).__module__
    if module.startswith("mem0"):
        return next((a for a in adapters if a.name == "mem0"), None)
    if module.startswith("ferryte.adapters.vector") or type(client).__name__ == "InMemoryVectorStore":
        return next((a for a in adapters if a.name == "vector"), None)
    return None


def uninstrument() -> None:
    """Remove all patches and forget tracked clients (mostly for tests)."""
    global _installed, _handle
    with _lock:
        if _handle is None:
            return
        for tc in _handle.list_clients():
            with contextlib.suppress(Exception):
                tc.adapter.unpatch(tc.client)
        _handle = None
        _installed = False


def current_instrumentation() -> Instrumentation | None:
    return _handle
