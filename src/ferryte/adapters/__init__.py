"""Adapters for memory backends.

Each adapter knows how to:
  - patch a backend client to capture writes and reads (provenance + retrieval traces)
  - call the backend's real delete / revoke API (the oracle's hand on the wheel)
  - enumerate the artifacts derived from a given source (best-effort; surfaces blind spots)
"""

from .base import Adapter, AdapterCapability, BackendKind, RetrievalRecord, WriteRecord

__all__ = [
    "Adapter",
    "AdapterCapability",
    "BackendKind",
    "RetrievalRecord",
    "WriteRecord",
]
