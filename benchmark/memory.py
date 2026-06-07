"""`SummaryMemory` — a realistic multi-tenant agent-memory layer.

This is the system-under-test. It mirrors the common production pattern: raw
writes go into a vector store, AND a per-tenant rolling **summary** (derived
memory) is maintained by an LLM. The leak the report measures: when an app
deletes a source's raw rows, the derived summary that absorbed it survives —
exactly the behaviour AWS AgentCore and Zep document. `leak_summaries=False`
models the "good" app that also clears derived memory, for an A/B contrast.
"""

from __future__ import annotations

from typing import Any, Protocol

from .stores import Embedder, StoredItem, VectorStore, new_item


class Summarizer(Protocol):
    def update(self, existing: str | None, new_content: str, *, tenant_id: str) -> str: ...


class ConcatSummarizer:
    """Dependency-free stand-in for tests. Real runs use `OpenAISummarizer`."""

    def update(self, existing: str | None, new_content: str, *, tenant_id: str) -> str:
        return new_content if not existing else f"{existing} | {new_content}"


class OpenAISummarizer:
    """Maintains a rolling per-tenant summary with a real LLM.

    Lazy-imports `openai` so the core stays dependency-free. Used only for
    real benchmark runs (needs OPENAI_API_KEY).
    """

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        from openai import OpenAI  # noqa: PLC0415 - intentional lazy import

        self._client = OpenAI()

    def update(self, existing: str | None, new_content: str, *, tenant_id: str) -> str:
        prompt = (
            "You maintain a concise running memory summary for one tenant. "
            "Merge the new note into the existing summary, preserving any "
            "specific identifiers, codes, names, and facts verbatim.\n\n"
            f"Existing summary:\n{existing or '(none)'}\n\n"
            f"New note:\n{new_content}\n\nUpdated summary:"
        )
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return (resp.choices[0].message.content or "").strip()


class SummaryMemory:
    """Vector store + per-tenant LLM summary. Ferryte instruments this."""

    def __init__(
        self,
        *,
        store: VectorStore,
        embedder: Embedder,
        summarizer: Summarizer | None = None,
        leak_summaries: bool = True,
    ) -> None:
        self.store = store
        self.embedder = embedder
        self.summarizer: Summarizer = summarizer or ConcatSummarizer()
        self.leak_summaries = leak_summaries
        # tenant -> {"artifact_id", "text", "absorbed": [source_id, ...]}
        self._summaries: dict[str, dict[str, Any]] = {}

    def add(
        self,
        *,
        content: str,
        source_id: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        item = new_item(
            content=content,
            embedding=self.embedder.embed(content),
            tenant_id=tenant_id,
            source_id=source_id,
            kind="raw",
            metadata=metadata,
        )
        self.store.upsert(item)
        if tenant_id:
            self._update_summary(tenant_id, content, source_id)
        return item.artifact_id

    def _update_summary(self, tenant_id: str, content: str, source_id: str | None) -> None:
        s = self._summaries.get(tenant_id)
        if s is None:
            text = self.summarizer.update(None, content, tenant_id=tenant_id)
            s = {
                "artifact_id": new_item(
                    content=text, embedding=[], tenant_id=tenant_id, source_id=None
                ).artifact_id,
                "text": text,
                "absorbed": [source_id] if source_id else [],
            }
            self._summaries[tenant_id] = s
        else:
            s["text"] = self.summarizer.update(s["text"], content, tenant_id=tenant_id)
            if source_id and source_id not in s["absorbed"]:
                s["absorbed"].append(source_id)
        self.store.upsert(
            new_item(
                content=s["text"],
                embedding=self.embedder.embed(s["text"]),
                tenant_id=tenant_id,
                source_id=None,
                kind="summary",
                metadata={"kind": "summary", "absorbed_sources": list(s["absorbed"])},
                artifact_id=s["artifact_id"],
            )
        )

    def search(
        self, *, query: str, tenant_id: str | None = None, limit: int = 5
    ) -> list[tuple[StoredItem, float]]:
        return self.store.query(self.embedder.embed(query), tenant_id=tenant_id, limit=limit)

    def delete_by_source(self, source_id: str, *, tenant_id: str | None = None) -> int:
        n = self.store.delete_by_source(source_id, tenant_id=tenant_id)
        if not self.leak_summaries:
            for _tid, s in self._summaries.items():
                if source_id in s["absorbed"]:
                    self.store.delete_artifact(s["artifact_id"])
        return n

    def raw_items_containing(self, needle: str) -> list[StoredItem]:
        return self.store.items_containing(needle)
