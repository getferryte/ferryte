"""Pluggable vector-store backends + embedders for the benchmark.

Every store implements the same tiny surface so `SummaryMemory` can run on
in-memory (tests), Chroma, Qdrant, or pgvector without changing the harness.
A row delete on a raw store is clean — the leak lives in the summary layer
(see memory.py), which is the honest thing the report measures.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _WORD_RE.findall(text or "")]


# --------------------------------------------------------------- embedders


@runtime_checkable
class Embedder(Protocol):
    dim: int

    def embed(self, text: str) -> list[float]: ...


class HashEmbedder:
    """Deterministic, dependency-free embedding for tests and CI.

    Real benchmark runs use `OpenAIEmbedder`; this keeps the pipeline testable
    with no network or API key.
    """

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _tokenize(text):
            h = int(hashlib.sha1(tok.encode("utf-8")).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        norm = sum(v * v for v in vec) ** 0.5
        return [v / norm for v in vec] if norm > 0 else vec


class OpenAIEmbedder:
    """Real embeddings for benchmark runs. Lazy-imports `openai`."""

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self.model = model
        self.dim = 1536 if model.endswith("3-small") else 3072
        from openai import OpenAI  # noqa: PLC0415 - intentional lazy import

        self._client = OpenAI()

    def embed(self, text: str) -> list[float]:
        resp = self._client.embeddings.create(model=self.model, input=text or " ")
        return resp.data[0].embedding


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# --------------------------------------------------------------- items + store


@dataclass
class StoredItem:
    artifact_id: str
    content: str
    embedding: list[float]
    tenant_id: str | None
    source_id: str | None
    kind: str = "raw"  # "raw" | "summary"
    metadata: dict[str, Any] = field(default_factory=dict)
    deleted: bool = False


@runtime_checkable
class VectorStore(Protocol):
    name: str

    def upsert(self, item: StoredItem) -> None: ...
    def query(
        self,
        embedding: list[float],
        *,
        tenant_id: str | None = None,
        limit: int = 5,
        include_deleted: bool = False,
    ) -> list[tuple[StoredItem, float]]: ...
    def delete_by_source(self, source_id: str, *, tenant_id: str | None = None) -> int: ...
    def delete_artifact(self, artifact_id: str) -> None: ...
    def items(self) -> Iterable[StoredItem]: ...
    def items_containing(self, needle: str) -> list[StoredItem]: ...


class InMemoryVS:
    """Reference store. Soft-deletes raw rows so store-inspection can still see
    what survived (matching Ferryte's vector adapter contract)."""

    name = "inmemory"

    def __init__(self) -> None:
        self._items: dict[str, StoredItem] = {}

    def upsert(self, item: StoredItem) -> None:
        self._items[item.artifact_id] = item

    def query(
        self,
        embedding: list[float],
        *,
        tenant_id: str | None = None,
        limit: int = 5,
        include_deleted: bool = False,
    ) -> list[tuple[StoredItem, float]]:
        scored: list[tuple[StoredItem, float]] = []
        for it in self._items.values():
            if it.deleted and not include_deleted:
                continue
            if tenant_id is not None and it.tenant_id not in (None, tenant_id):
                continue
            scored.append((it, cosine(embedding, it.embedding)))
        scored.sort(key=lambda kv: kv[1], reverse=True)
        return scored[:limit]

    def delete_by_source(self, source_id: str, *, tenant_id: str | None = None) -> int:
        n = 0
        for it in self._items.values():
            if it.source_id == source_id and it.kind == "raw" and not it.deleted:
                it.deleted = True
                n += 1
        return n

    def delete_artifact(self, artifact_id: str) -> None:
        it = self._items.get(artifact_id)
        if it is not None:
            it.deleted = True

    def items(self) -> Iterable[StoredItem]:
        return list(self._items.values())

    def items_containing(self, needle: str) -> list[StoredItem]:
        n = (needle or "").lower()
        return [it for it in self._items.values() if n in (it.content or "").lower()]


def new_item(
    *,
    content: str,
    embedding: list[float],
    tenant_id: str | None,
    source_id: str | None,
    kind: str = "raw",
    metadata: dict[str, Any] | None = None,
    artifact_id: str | None = None,
) -> StoredItem:
    return StoredItem(
        artifact_id=artifact_id or str(uuid.uuid4()),
        content=content,
        embedding=embedding,
        tenant_id=tenant_id,
        source_id=source_id,
        kind=kind,
        metadata=dict(metadata or {}),
    )
