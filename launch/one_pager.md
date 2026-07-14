# Ferryte — one-pager

**Ferryte is the verification layer for agent forgetting.**
We prove whether a deleted, revoked, or cross-tenant source can still influence your AI agent — and we give you the exact memory artifact responsible.

## The problem (in one quote)

> "Deleting an event doesn't remove the structured information derived out of it from the long term memory."
> — AWS Bedrock AgentCore docs

Every major agent-memory backend has the same shape: the row goes away, the derived summary/embedding/fact stays. Teams ship multi-tenant agents to production and discover the leak from a customer. There is no Sentry for this.

## What we built (and what's shipping today)

| Capability                          | v1                                                            |
| ----------------------------------- | ------------------------------------------------------------- |
| One-line auto-instrumentation       | `ferryte.instrument()`                                         |
| Memory adapters                     | Mem0 + self-contained vector store (Zep/AgentCore next)       |
| Forgetting oracle                   | source-revocation, cross-tenant-isolation, stale-fact, poisoning |
| Source-to-derived lineage           | SQLite, blast-radius API                                      |
| Honest blind-spot map               | both runtime and structural gaps                              |
| Coverage report                     | JSON + HTML + rich terminal                                   |
| CI gate                             | non-zero exit on revoked-marker re-entry                      |
| Dashboard                           | Next.js, dark, ships with sample report                       |

## Why we win on this wedge

| Incumbent                         | Why they aren't the answer                                                                                                          |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Promptfoo (`agentic:memory-poisoning`) | Generic red-team plugin. No lineage. No backend delete. No blind-spot map.                                                       |
| Zep / Graphiti                    | Provenance is in-substrate only. Shared summaries still absorb deleted episodes.                                                    |
| Atlan / Ethyca / Transcend        | Top-down privacy/PII. Slow legal sale. Don't model derived agent memory.                                                            |
| OWASP Agent Memory Guard          | Single-store middleware. Free OSS, no product, no audit evidence.                                                                   |

The defensible wedge is **cross-system source-to-descendant verification** — exactly what the vendors document as broken and exactly what nobody else verifies.

## Distribution

Source-available (BSL 1.1). `pip install ferryte`. Hosted dashboard and team features are the expansion.

## Land / expand

- **Land:** developer-team budget. CI gate + coverage report. Bottoms-up.
- **Expand:** runtime retrieval filter, audit receipts, compliance attestation. Security/CISO budget. (Deferred from v1 on purpose — we ship after design partners ask.)

## ICP

B2B SaaS shipping multi-tenant AI agents with persistent memory to enterprise customers, where a security review or a real incident has created urgency.

## Ask

Five design partners. Eight weeks each. We'll publish what we learn.
Paired with the founding engineer for the Core integration; six months of
Cloud free when Cloud ships.
**pranav@ferryte.dev** · github.com/getferryte/ferryte
