# Changelog

All notable changes to Ferryte will be documented in this file.

## [0.1.0] — unreleased

Initial public release.

### Added

- `ferryte.instrument()` — one-line auto-instrumentation that auto-patches detected memory clients, with a constructor hook so clients built after the call are picked up too.
- `ferryte.tag(source_id=..., tenant_id=...)` — context manager for attaching provenance to writes with zero call-site changes.
- Adapter interface (`Adapter`, `WriteRecord`, `RetrievalRecord`, `AdapterCapability`) designed so Zep/Graphiti and AWS Bedrock AgentCore are drop-in fast-follows.
- First-party adapters: Mem0 + a self-contained `InMemoryVectorStore` (the latter deliberately reproduces the "derived summary survives delete" failure mode documented by both AWS AgentCore and Zep).
- Source-to-derived-artifact lineage graph backed by SQLite, plus blast-radius computation for revocation.
- Forgetting oracle with four built-in scenarios: `source-revocation`, `cross-tenant-isolation`, `stale-fact`, `memory-poisoning`.
- Inspection of BOTH retrieval results and raw store contents — kills the "canary passed but tainted context still stored" false-confidence trap.
- Coverage + blind-spot reports (JSON, HTML, rich terminal); explicit structural-gap surfacing.
- `ferryte` CLI: `init`, `test`, `coverage`, `list-scenarios`, `serve`.
- CI gate: non-zero exit when a revoked marker re-enters retrieval or prompt.
- Optional FastAPI HTTP server (`ferryte serve`) consumed by the Next.js dashboard.
- Next.js + Tailwind dashboard with overview, lineage / blast-radius, and blind-spots pages; ships with a baked-in sample report so screenshots work without the API running.
- Self-contained 30-second demo (`demo/multi_tenant_leak.py`) reproducing the leak with zero external services.
- Launch kit: X thread copy, screencast script, one-pager, design-partner program.
