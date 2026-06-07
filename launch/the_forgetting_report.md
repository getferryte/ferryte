# The Forgetting Report

**We deleted the data from popular AI-memory stacks. Most of them kept it. Then
we turned on Ferryte and most of the leaks disappeared.**

A reproducible benchmark of *delete-after-revoke* behaviour in agent memory.
Everything here runs on our own deployments of public / open-source tools, with
pinned versions and a one-command repro. Don't trust us — run it:
`github.com/getferryte/ferryte/tree/main/benchmark`.

---

## TL;DR

- We plant a unique canary fact for one tenant, let the memory stack do its normal
  thing (including its own LLM summarization / fact-extraction), then call the
  stack's **real delete API** to revoke the source. Then we ask the agent again.
- Deleting the **raw row** is clean everywhere. The data that survives lives in the
  **derived layer** — the LLM summary or knowledge-graph node that absorbed the
  fact. That layer is what every serious agent-memory framework adds, and it's
  where forgetting quietly fails.
- **The same harness, with `--with-ferryte`, runs the lineage-driven cascade
  delete on top of the native API.** Most leaks go away.

| Stack | Before (naive delete) | After (with Ferryte cascade) | Δ |
|---|---:|---:|---:|
| **AWS Bedrock AgentCore** | 50% (LEAK / PASS / LEAK / PASS) | **75%** (PASS / PASS / WARN / PASS) | **+25pp** |
| **Vector store + app summary** (pgvector · Chroma · Qdrant) | 25% (LEAK / PASS / WARN / LEAK) | **50%** (PASS / PASS / WARN / LEAK) | **+25pp** |
| **Mem0** (native) | 25% (LEAK / PASS / LEAK / LEAK) | 25% (no change — see §4) | — |
| **Zep** | — | — | *run pending* |

> Scenarios in order: source-revocation · cross-tenant · stale-fact · poisoning.
> Forgetting Score = % of scenarios the stack passes cleanly. AgentCore tested
> live on AWS `us-west-2`. The Mem0 row is the honest part: Ferryte's lineage
> graph doesn't yet see Mem0's internal extracted facts. That's a known gap, not
> a hidden one.

---

## 1. Why this benchmark exists

"Delete my data" is a legal obligation (GDPR Art. 17, CCPA) and a security
boundary (multi-tenant isolation). But agent memory isn't a database row — it's a
pipeline. A fact written once gets **embedded, summarized, extracted into a graph,
and folded into per-tenant rolling memory.** When an app later deletes "the
source," it usually deletes the row it knows about. The derived copies it never
tracked stay behind, and the agent keeps answering from them.

The vendors say so themselves:

- **AWS Bedrock AgentCore:** *"Deleting an event doesn't remove the structured
  information derived out of it from the long term memory."*
- **Zep:** *"Deleting an episode does not regenerate the names or summaries of
  nodes shared with other episodes."*

This report turns those admissions into a measurement anyone can reproduce.

## 2. What we tested

**Backends (launch set):** Mem0, pgvector, Chroma, Qdrant (the three raw stores run
under a realistic multi-tenant *summary memory* layer), plus AWS Bedrock AgentCore
and Zep tested through their own native delete APIs.

**Scenarios** (each plants canaries a stack can't have invented on its own):

1. **Source revocation** — write a fact tied to a source, delete the source via the
   real API, then probe. LEAK if the marker still surfaces.
2. **Cross-tenant isolation** — write for tenant B, query as tenant A. LEAK if A
   sees B's marker.
3. **Stale fact** — overwrite an old value with a new one. WARN/LEAK if the stale
   value still outranks the fresh one.
4. **Memory poisoning** (OWASP ASI06) — inject low-trust content, then probe. LEAK
   if it survives into retrieved answers.

**Verdicts:** PASS (gone everywhere) · LEAK (resurfaced) · WARN (partial / stale
outranks fresh) · BLIND (we honestly couldn't verify — never a silent pass).

## 3. Methodology (the credibility is the whole point)

1. **Real backends, default/recommended configs**, on our own deployments. No
   strawmen, never anyone's private systems.
2. **A canary the data can't invent.** Each marker (e.g. `ORION-DELTA-77`) is
   unique, so any later appearance is provably a leak, not a coincidence.
3. **The real delete path.** We call each stack's own delete/revoke API — the same
   call an application would make for a GDPR request.
4. **Derived memory is the system under test.** Raw stores get a realistic
   multi-tenant LLM summary layer on top (because that's how real agents use them);
   native frameworks are tested through their built-in extraction + delete.
5. **Fully reproducible.** Pinned versions, docker-compose, one command, public
   repo. Embedder `text-embedding-3-small`, summarizer `gpt-4o-mini`.
6. **The illustrative in-memory baseline is kept separate** from real-backend
   results and never blended in.

## 4. Findings

### Raw vector stores (pgvector / Chroma / Qdrant) — identical, and that's the point

All three score the same. A row delete cleanly removes the embedding — so on their
own they'd PASS. They LEAK only because the **app-side LLM summary** absorbed the
fact and the delete didn't reach it. **Takeaway: don't blame your vector DB.** The
forgetting bug is in the derived layer you (or your framework) built on top.

- Source revocation → **LEAK**: the per-tenant summary still surfaces the marker.
- Cross-tenant → **PASS**: tenant scoping on retrieval holds.
- Stale fact → **WARN**: the stale value lingers alongside the fresh one.
- Poisoning → **LEAK**: injected content has no trust boundary and is retrieved.

### Mem0 (native framework) — the honest gap

Mem0 runs its own LLM fact-extraction on every write. In our run it preserved the
canary **verbatim** in an extracted memory. Deleting the tracked memory still left
the fact retrievable — extraction had produced a copy the source-delete didn't
reach.

- Source revocation → **LEAK**, Cross-tenant → **PASS**, Stale fact → **LEAK**,
  Poisoning → **LEAK**. **Forgetting Score 25%.**

**Why `--with-ferryte` does not move the Mem0 row** (the honest part you should
know about):

Ferryte's lineage graph records every artifact ID returned from `add()`. Mem0's
internal fact-extractor, however, can create derived facts whose IDs aren't
surfaced to the caller — so the lineage graph can't yet enumerate them for a
cascade. Mem0 needs deeper instrumentation than monkey-patching `add` to reach
that layer. We're flagging this rather than hiding it; it's on the roadmap.

### AWS Bedrock AgentCore (native framework) — the headline result

Tested live on AWS `us-west-2` with the semantic memory strategy. After every
`CreateEvent`, AgentCore extracts a structured long-term `MemoryRecord` — a
short, fluent fact synthesised by Claude.

**Before (naive `DeleteEvent` only) — Forgetting Score 50%:**
When we revoked the source by calling `DeleteEvent` on every raw event, the
events disappeared (verified via `ListEvents` returning 0), **but the extracted
record survived** with the canary marker (`KILO-BETELGEUSE-58DCBE`) preserved
verbatim. `RetrieveMemoryRecords` continued to return it for natural queries
(`launch code`, `secret`) with scores in the 0.40–0.45 range — exactly what
[AWS's own documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/short-term-delete-event.html)
warns about. *Measured*, not asserted.

- Source revocation → **LEAK**, Cross-tenant → **PASS**, Stale fact → **LEAK**,
  Poisoning → **PASS**.

**After (`--with-ferryte` cascade) — Forgetting Score 75% (+25pp):**
With Ferryte's lineage cascade enabled, the same `DeleteEvent` is followed by an
automatic `ListMemoryRecords` → `DeleteMemoryRecord` sweep against the affected
namespace, with a brief settling loop to handle AgentCore's eventually-consistent
re-extraction. The canary stops surfacing.

- Source revocation → **PASS**, Cross-tenant → **PASS**, Stale fact → **WARN**,
  Poisoning → **PASS**.
- The remaining WARN is a different bug class (stale-fact is about overwrite
  ordering, not delete) — the cascade alone doesn't fix that, by design.
- This is exactly the fix AWS recommends in their own docs. The win is that
  Ferryte does it *automatically* via lineage, without you having to discover
  every derived-memory surface by hand for every backend you run.

### Zep (run pending)

Zep's self-hostable Community Edition has been deprecated; the current
`zep-cloud` SDK is cloud-only. We'll publish a measured row if/when we run it
against a hosted Zep Cloud account, rather than assert numbers we haven't
produced.

## 5. Why it happens

Agent memory is a *fan-out*. One write becomes many artifacts:

```
write ──► raw embedding (vector row)
      └─► per-tenant rolling summary  (LLM)
      └─► knowledge-graph nodes/edges (LLM)
      └─► extracted "facts" / preferences (LLM)
```

App-level deletes target the artifact the app created (the row). The LLM-derived
artifacts were created by the *framework*, are keyed differently, and are often
shared across multiple sources — so a naive delete can't safely remove them, and
usually doesn't try. The fact lives on in the summary.

## 6. How to fix it (per category)

- **If you run a raw store + your own summaries:** track lineage from each derived
  artifact back to its sources, and on delete, regenerate or purge any summary that
  absorbed the revoked source. (This is exactly what Ferryte's lineage graph is
  for.)
- **Mem0:** after deleting source memories, also delete derived/extracted memories
  that reference the same content; don't assume one delete cascades.
- **AgentCore:** deleting events is not enough — also delete the derived
  long-term `MemoryRecords` (BatchDeleteMemoryRecords) for that actor/source.
- **Zep:** deleting an episode won't regenerate shared node summaries — you must
  reprocess or prune affected graph nodes.

## 7. What we did NOT test (blind spots)

- Proprietary managed memory we can't self-host or didn't pay for.
- Latency / cost / quality — this is strictly a *forgetting* benchmark.
- Every possible config. We used defaults/recommended; a hardened config may do
  better, and we'd happily measure it.
- Where we couldn't verify, the cell is **BLIND**, not PASS.

## 8. The obvious objection

**"You sell the fix, so of course you found leaks."** Fair. Our defense is
falsifiability, not trust:

- The whole harness is open; versions and configs are pinned.
- We publish what **passes** (cross-tenant isolation held everywhere).
- We tell you exactly what we didn't test.
- Run it against your own stack and check our work. If we're wrong about a cell,
  open an issue — we'll correct it in public.

## 9. Reproduce it

```bash
git clone https://github.com/getferryte/ferryte
cd ferryte/benchmark
cp .env.example .env            # add your OpenAI key
docker compose up -d            # pgvector · qdrant · chroma
pip install -r requirements.txt
python -m benchmark.run \
  --backends mem0,qdrant,chroma,pgvector \
  --scenarios all --embedder openai --summarizer openai
```

## 10. What to do about it

Put a forgetting test in CI. Ferryte plants the canaries, calls your real delete
path, and breaks the build when a revoked fact survives — including through the
summary/graph layer:

```bash
pip install ferryte
ferryte test --scenario source-revocation
```

Free audit for teams running multi-tenant agents in production:
**hello@ferryte.dev**.

---

*Appendix — environment: embedder `text-embedding-3-small`, summarizer
`gpt-4o-mini`, stores via `benchmark/docker-compose.yml`. Exact image digests and
package versions are pinned in the repo before each published run.*
