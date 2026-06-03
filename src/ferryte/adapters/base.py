"""Base classes for memory-backend adapters.

The adapter interface is deliberately narrow: anyone writing a Zep or AgentCore
adapter implements the same five hooks and gets the full Ferryte pipeline for free.
"""

from __future__ import annotations

import enum
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol


class BackendKind(str, enum.Enum):
    MEM0 = "mem0"
    VECTOR = "vector"
    ZEP = "zep"
    AGENTCORE = "agentcore"
    CUSTOM = "custom"


class AdapterCapability(str, enum.Enum):
    WRITE_CAPTURE = "write_capture"
    READ_CAPTURE = "read_capture"
    SOURCE_DELETE = "source_delete"
    TENANT_SCOPING = "tenant_scoping"
    DERIVED_ENUMERATION = "derived_enumeration"


@dataclass
class WriteRecord:
    """A captured memory write."""

    backend: BackendKind
    artifact_id: str
    content: str
    source_id: str | None = None
    tenant_id: str | None = None
    kind: str = "raw"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalRecord:
    """A captured memory read."""

    backend: BackendKind
    query: str
    artifact_id: str
    content: str
    score: float | None = None
    tenant_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Adapter(Protocol):
    """The minimum surface a backend adapter must implement."""

    name: str
    backend: BackendKind
    capabilities: frozenset[AdapterCapability]

    def patch(self, client: Any) -> Any:
        """Wrap or monkey-patch ``client`` so subsequent calls are captured.

        Returns the (possibly same) instrumented client.
        """
        ...

    def unpatch(self, client: Any) -> None:
        """Reverse ``patch``."""
        ...

    def delete_source(self, client: Any, *, source_id: str, tenant_id: str | None = None) -> int:
        """Call the backend's real delete API for everything tagged with ``source_id``.

        Returns the number of underlying records the adapter believes it deleted.
        """
        ...

    def list_artifacts_for_source(
        self,
        client: Any,
        *,
        source_id: str,
        tenant_id: str | None = None,
    ) -> Iterable[WriteRecord]:
        """Best-effort enumeration of artifacts derived from ``source_id``.

        If the backend cannot answer this (e.g. an LLM paraphrased five sources into one
        summary and lost the ids), the adapter should return what it can and the lineage
        layer surfaces the rest as a blind spot.
        """
        ...

    def probe(
        self,
        client: Any,
        *,
        query: str,
        tenant_id: str | None = None,
        limit: int = 5,
    ) -> list[RetrievalRecord]:
        """Run a retrieval query and return what the backend would surface."""
        ...
