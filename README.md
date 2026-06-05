# Ferryte

**Verification for agent forgetting.**
**Source-available (BSL 1.1 → Apache 2.0) · commercial Cloud + Enterprise tiers.**

[Marketing site](https://ferryte.dev) · [Live dashboard demo](https://ferryte.dev/app) · [LICENSING](LICENSING.md) · [COMMERCIAL](COMMERCIAL.md)

> "Deleting an event doesn't remove the structured information derived out of it from the long term memory."
> — [AWS Bedrock AgentCore docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/short-term-delete-event.html)

When you delete a record, revoke a permission, or quarantine a source, your agent's *derived* memories (summaries, embeddings, extracted facts) often keep behaving as if the data is still there. The platform vendors document this. Almost nobody verifies it.

**Ferryte is the forgetting oracle.** It seeds canary memories, calls the real delete API, replays your agent, inspects both the store contents and the retrieval traces, and tells you exactly which derived artifacts still leak — including an honest map of what it cannot see.

It is built for one thing: catching the leak before your customer does.

## Why this exists

Agent memory is production state, but teams don't test it like production state. Sentry observes errors that already happened. Ferryte detects **counterfactual failures**: information that should no longer be allowed to influence behavior, but still does.

The crux:
- AWS Bedrock AgentCore: deleting a short-term event does not remove derived long-term memory records.
- Zep: deleting an episode does not regenerate the shared node summaries that already absorbed it.
- Mem0 / generic vector stores: deletes the row, but embeddings already in retrieval caches keep returning.

Ferryte is the layer that proves whether forgetting actually happened.

## What it does (v1)

1. **Seed** deterministic canary memories tagged by `source_id` and `tenant_id`.
2. **Revoke** via the backend's own delete / permissions API.
3. **Replay** agent probes AND directly inspect store contents + retrieval traces — not just final answers. (Final-answer-only verification gives false confidence.)
4. **Trace** the lineage from each source to every derived artifact it influenced; compute blast radius on revocation.
5. **Report** coverage + the blind-spot map (where we *cannot* prove forgetting — un-instrumented stores, laundered LLM-paraphrased derivations, external caches).
6. **Gate** CI: fail the build when a revoked marker re-enters retrieval or prompt.

Scenarios shipped:

- `source-revocation` — flagship: delete a source, prove no derivative still surfaces it.
- `cross-tenant-isolation` — Tenant A's data never reaches Tenant B's agent.
- `stale-fact` — agent refuses or flags facts past their valid window.
- `memory-poisoning` — planted malicious write is detected and quarantined.

## Install

```bash
pip install ferryte
```

## Quickstart (under 10 minutes)

```python
import ferryte
from mem0 import Memory

ferryte.instrument()              # one line; auto-patches detected memory clients
mem = Memory()                    # your existing code, unchanged
# ... your agent runs ...
```

Then in CI:

```bash
ferryte init                      # zero-config: discovers the agent + memory backend
ferryte test --scenario source-revocation
ferryte coverage                  # prints what was verified + the blind-spot map
```

A non-zero exit code on `ferryte test` means a revoked marker re-entered the agent's prompt. That's the build break.

## Architecture

```
your agent  ─┐
             │  one-line auto-patch
             ▼
      ferryte.instrument()
             │
   ┌─────────┼──────────────┐
   │         │              │
   ▼         ▼              ▼
backends    lineage      retrieval
adapters    graph         traces
   │         │              │
   └─────────┴──────┬───────┘
                    ▼
            forgetting oracle
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
    coverage    CI gate       dashboard
    + blind-    (fail on      (Next.js)
    spot map    leak)
```

Backends in v1: **Mem0** + a generic **vector store** (pgvector / Chroma / in-memory).
Architected for fast-follow: Zep / Graphiti and AWS Bedrock AgentCore.

## Explicitly deferred (fast-follow, NOT in v1)

- Runtime retrieval enforcement filter (latency-sensitive; ship after design partners ask).
- Zep + AgentCore adapters (architected for, built next).
- Audit receipts / compliance attestation layer (expansion path).

## Project layout

```
ferryte/
├── src/ferryte/            # Python core + CLI (pip install ferryte)
│   ├── instrument.py       # one-line auto-patching
│   ├── adapters/           # memory-backend adapters (Mem0, vector store, ...)
│   ├── lineage/            # source → derived-artifact graph + blast radius
│   ├── oracle/             # canary + scenario runner
│   ├── reports/            # coverage + blind-spot map
│   └── api/                # local HTTP server feeding the dashboard
├── dashboard/              # Next.js + Tailwind UI (Glyff design system, dark)
├── demo/                   # self-contained multi-tenant memory leak demo (the 30s X clip)
├── launch/                 # X thread copy, design-partner signup
└── tests/
```

## Source-available

Ferryte is **source-available** under the Business Source License 1.1.

- **Core (BSL 1.1, free to read / run / self-host)** — the library, CLI, four scenarios, lineage graph, Mem0 + vector adapters, local Next.js dashboard. Everything you need to verify forgetting in your own CI, in production, for free. Each version converts to Apache 2.0 three years after release.
- **Cloud (private beta)** — hosted continuous verification, regression alerts, multi-environment, Slack/PagerDuty integrations. Design partners only through 2026.
- **Enterprise (annual contract)** — self-hosted with SSO/RBAC/audit logs, premium adapters (AgentCore, Zep, GovCloud), signed compliance attestations (GDPR / CCPA), runtime retrieval enforcement (v2), support SLA.

The one thing BSL does not permit: reselling Ferryte as a hosted/embedded service that competes with Ferryte Cloud. Everything else — read, run, modify, self-host in production — is free. The exact boundary, contributor license, and trademark policy are in [LICENSING.md](LICENSING.md). The commercial-tier scope and how to apply are in [COMMERCIAL.md](COMMERCIAL.md).

Same model as Sentry, CockroachDB, HashiCorp, and MariaDB.

## Status

Pre-launch. The source-available engine ships now; Cloud and Enterprise gate behind design partners. Looking for B2B SaaS companies running multi-tenant AI agents in production with persistent memory.

If that is you: open an issue, email `hello@ferryte.dev`, or sign up via the marketing site.

## License

**v0.2.0 and later:** Business Source License 1.1, converting to Apache 2.0 three years after each release — see [LICENSE](LICENSE).
**v0.1.0 and earlier:** MIT (a published release cannot be relicensed) — see [LICENSE-MIT.txt](LICENSE-MIT.txt).
Commercial Cloud / Enterprise tiers are closed-source — see [LICENSING.md](LICENSING.md) for the precise boundary.
