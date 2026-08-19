# Changelog

All notable changes to Ferryte will be documented in this file.

## [Unreleased]

### Added — real vector-store backends

- **pgvector adapter** (`ferryte[pgvector]`). Schema-configurable handle over an
  existing Postgres table — you name the table and the content / embedding /
  tenant / source columns, and Ferryte speaks SQL against them. Works read-only
  against a production table it has never seen. Identifiers are validated
  against a strict pattern and quoted before they reach SQL.
- **Chroma adapter** (`ferryte[chroma]`). Wraps a collection; tenant scoping via
  the metadata `where` filter. Chroma embeds queries itself, so semantic
  probing is meaningful out of the box.
- **Qdrant adapter** (`ferryte[qdrant]`). Payload-filter tenant scoping, scroll
  based enumeration.
- `ferryte.connect.open_store()` — resolve any backend from a URI
  (`postgres://`, `chroma://`, `chroma+http://`, `qdrant://`, `memory://`) so the
  CLI, Cloud and notebooks share one code path.
- `documents_for_tenant()` on every store, which is what makes the
  semantic-neighbour probe possible.

> On embeddings, stated plainly: pgvector and Qdrant hold vectors from *your*
> model, which Ferryte cannot reproduce. Pass an `embedder` for true vector
> similarity; omit it and probes fall back to a lexical scan that still catches
> exact-token leaks but can miss paraphrased ones — and records a blind spot
> saying so. Previous releases listed these three stores as supported when only
> an in-memory reference store shipped; that claim is now true.

### Added — isolation and attestation

- **`ferryte isolation-check <uri>`** — three probes against a live store:
  *filtered* (a foreign document with the tenant filter applied is a hard fail),
  *unfiltered blast radius* (what one forgotten predicate would expose, reported
  as exposure rather than a defect), and *semantic neighbours* (queries derived
  from one tenant's own documents run as another tenant — reach through
  similarity, which produces no error in any log). Exits non-zero on a real
  leak. JSON and Markdown output.
- **`ferryte attest-deletion <uri> --source ... --sign`** — deletes, re-probes to
  verify, and emits a dated, hash-chained, Ed25519-signed record covering what
  was deleted, what was probed, and what could not be verified. `--dry-run`
  verifies without deleting.
- **`ferryte verify-attestation <file>`** — recomputes the canonical hash and
  checks the signature; detects post-hoc edits.
- Every attestation carries a named scope-limitations section (backups,
  replicas, downstream exports, model weights, point-in-time validity) and
  states that it is **not** a certificate of regulatory compliance.
- `ferryte[attest]` extra for Ed25519 signing. Without it, records still carry a
  SHA-256 content hash and say plainly that they are unsigned.

### Added — CI and Cloud

- **GitHub Action** (`action.yml`): runs the isolation check and, optionally, the
  forgetting battery on every PR; writes a job summary and uploads reports.
  `fail-on-blind-spots` is off by default, because a blind spot is an honest gap
  in coverage rather than evidence of a defect.
- **Cloud `POST /v1/scan` + `GET /v1/scan/{id}`** — hosted, read-only isolation
  scan. Credentials are never persisted, results are excerpt-bounded and expire
  after an hour, jobs are scoped to the requesting org/project, and loopback and
  private addresses are refused by default so the endpoint cannot be used as an
  SSRF primitive.

### Added — prior release

- **`ferryte audit`** — one command that runs the full scenario battery,
  attributes up to five wrong answers (`--answer`, optionally paired with
  `--answer-query`), and writes a client-facing deliverable: `audit.json`
  plus a print-ready `audit.html` (executive summary, prioritized fix list,
  evidence chains, honest blind-spot map). Powers the paid Agent Memory
  Audit at ferryte.dev/audit.
- `write_audit_report()` / `AuditMeta` in `ferryte.reports` for programmatic
  audit-report generation.
- Marketing site: `/audit` page (fixed-price Agent Memory Audit offer) with
  a servable sample report at `/sample-audit.html`; nav + sitemap entries.
- Dashboard toolchain upgraded to Next.js 16 / React 19 with committed ESLint
  configuration and CI coverage for linting and production builds.
- Technical SEO for ferryte.dev: unique route metadata and canonicals,
  structured product/service/benchmark data, crawl-safe dashboard no-indexing,
  a deterministic sitemap, and a machine-readable benchmark feed.

### Fixed

- CLI demo bootstrap now retains the temporary vector client long enough for
  `ferryte test` and `ferryte audit` to run their scenario batteries.

## [0.2.3] — 2026-07-08

### Changed

- **License: BSL 1.1 grant updated.** The "competing offering" definition now
  matches what Ferryte actually is (memory debugging, observability,
  attribution, and verification for AI agents — not just deletion
  verification), and the Change Date moves to the BSL maximum of four years
  per version. v0.2.0–v0.2.2 keep their original 3-year terms (see
  `LICENSE-BSL.txt`); v0.1.0 remains MIT.
- Package metadata, README, and site updated to the memory-debugging
  positioning ("trace a wrong answer back to the exact memory that caused it")
  language.

## [0.2.2] — 2026-07-07

### Added

- **Answer lineage** — `ferryte.record_answer()` records the exact memories in
  context when an answer was produced, making `ferryte why` attribution exact
  instead of inferential.
- **Supersession edges** — `ferryte.record_supersession()` marks a fact as
  replaced, making stale-belief diagnosis structurally provable.
- **Counterfactual replay** — `ferryte why --replay` ablates the top suspect
  from live retrieval and shows what would have entered the context instead.
- **Attribution v2** — IDF-weighted content overlap, quote-level shared-span
  evidence, zombie-memory and hub-memory (poisoning-pattern) diagnoses.
- **FTS5 candidate prefiltering** — attribution stays fast on large memory
  corpora (20k memories: ~178ms → ~0.5ms candidate selection).
- `--since` time-window filter on `ferryte why`; `/api/why` endpoint for the
  dashboard.

## [0.2.1] — 2026-06-05

### Fixed

- `ferryte --version` (and the FastAPI server version) reported `0.1.0` because
  the version string was hardcoded. The version is now derived from installed
  package metadata, so the CLI/API can never drift from the published release
  again.

## [0.2.0] — 2026-06-05

### Changed

- **License: MIT → Business Source License 1.1.** Ferryte v0.2.0 and later are
  source-available under BSL 1.1 and convert to the Apache License 2.0 three
  years after each release. You may read, modify, self-host, and run Ferryte
  in production for free; the only restriction is reselling it as a hosted or
  embedded service that competes with Ferryte Cloud. v0.1.0 remains MIT in
  perpetuity (a published release cannot be retroactively relicensed). See
  `LICENSE`, `LICENSE-MIT.txt`, and `LICENSING.md`.
- Marketing site, README, and docs updated from "open-core / MIT" to
  "source-available / BSL 1.1" language throughout.

## [0.1.0] — 2026-06-04

Initial public release (published to PyPI under the MIT License).

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
