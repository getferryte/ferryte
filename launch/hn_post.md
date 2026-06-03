# Hacker News — Show HN post

**Title** (≤ 80 chars, must start with `Show HN:`):

> Show HN: Ferryte – Verify your AI agent actually forgot deleted data

**Link:** https://ferryte.dev

**Text (the comment HN attaches to the post):**

Hi HN — we're open-sourcing Ferryte, a forgetting oracle for AI agents.

The premise, in one quote from AWS Bedrock AgentCore's own documentation:
*"Deleting an event doesn't remove the structured information derived out of
it from the long term memory."* Zep says the same about shared node summaries.
OWASP added memory poisoning (ASI06) to the Agentic Top 10 in December 2025.

The leak shape: an AI agent with persistent memory stores a fact, derives
summaries / embeddings / rollups from it, then the source gets deleted by the
official API. The primary record is gone; the derivations still surface the
fact. Multi-tenant agents leak across customers. Right-to-be-forgotten
requests don't actually forget. You find out from a customer.

What Ferryte does:

1. `ferryte.instrument()` — one line. Auto-patches detected memory clients
   (Mem0, generic vector stores; AgentCore/Zep adapters next).
2. `ferryte test` — plants deterministic canary memories tagged by source +
   tenant, calls your backend's real delete API, then inspects both store
   contents AND retrieval traces. Final-answer-only verification gives false
   confidence; agents are stochastic, retrieval is not.
3. Emits a coverage report with two sections: what was PROVED and an
   explicit BLIND-SPOT map (un-instrumented stores, laundered LLM
   paraphrases, external caches). A forgetting oracle that hides its limits
   is dangerous.
4. Non-zero exit on leak. Drop into CI.

It's MIT, in Python. Engine + CLI + lineage graph + four scenarios
(source-revocation, cross-tenant-isolation, stale-fact, memory-poisoning) +
a local Next.js dashboard. Cloud and Enterprise tiers (hosted, signed
compliance attestations, runtime enforcement) come later — same open-core
shape as Sentry/PostHog/Supabase.

Try the leak demo, no API keys:

    pip install ferryte
    python demo/multi_tenant_leak.py

It runs against a self-contained leaky in-memory vector store and exits 1
when the seeded canary survives delete. Real Mem0 / pgvector behave the same
way — swap the adapter, the demo is identical.

We're looking for five design partners running multi-tenant AI memory in
production. First six months free, named engineer on call, you shape the
roadmap. hello@ferryte.dev.

I'd love feedback on:

- The blind-spot framing — is it credible, or does it read like a cop-out?
- The scenarios you'd actually want next (we've got an internal list; would
  rather hear yours first).
- Whether the cross-system source-to-descendant verification framing maps to
  any leak you've personally hit.

Code: https://github.com/getferryte/ferryte
Marketing: https://ferryte.dev
Open-core boundary: https://github.com/getferryte/ferryte/blob/main/LICENSING.md

---

## Timing

- Submit around **07:00 Pacific Tuesday/Wednesday**. Front-page candidates
  in that window get the longest peak window.
- Have 5–10 friendly accounts ready to engage in the first 30 minutes
  (genuine comments, not upvotes — HN penalises vote rings).
- Reply to **every** substantive comment in the first two hours. The HN
  algorithm rewards engagement velocity.

## What to do if it doesn't take off

Don't resubmit the same link within 24 hours — flagged. Wait a week and try
a different framing (e.g. "Ask HN" or a technical-deep-dive blog post linked
from the homepage).
