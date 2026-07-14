# X launch thread

**Goal:** convert AI engineers and AppSec leads into GitHub stars, `pip
install ferryte` runs, and one or two design-partner replies.

**Posting time:** Tuesday or Wednesday, 9–10am Pacific. Highest dev-Twitter
engagement window.

**Pre-flight checks (do all of these before posting):**

- [ ] ferryte.dev resolves and the marketing site renders.
- [ ] `pip install ferryte` works in a fresh venv on a clean machine.
- [ ] `python demo/multi_tenant_leak.py` runs and shows the FAIL output.
- [ ] github.com/getferryte/ferryte is **public**.
- [ ] The screencast .mp4 is exported (1080p, 90 sec, ≤ 8 MB).
- [ ] Pin tweet 1 to the @ferryte profile after posting.
- [ ] DM the post to 5–10 friendly accounts within the first hour.

Tweets are numbered. Character counts in `[brackets]` at the end of each.

---

## 1 · The hook (with video)

> AWS, in their own AgentCore docs:
>
> "Deleting an event doesn't remove the structured information derived out of it from the long term memory."
>
> Your AI deleted the data. The derived memories didn't.
>
> Today we're open-sourcing the test that catches it. 🧵

**Media:** the 90-second screencast (autoplay loop on X).
**Alt text:** "Terminal output showing a leaked secret being deleted via the official API; a follow-up query still returns the secret; then `ferryte test` runs and fails CI with the exact memory path responsible."

`[≈ 275 chars]`

---

## 2 · The problem, plain

> Every major memory vendor admits delete is fire-and-forget at the source layer:
>
> — AWS Bedrock AgentCore (above)
> — Zep: deleting an episode does not regenerate the names or summaries of nodes shared with other episodes
> — OWASP added "Memory & Context Poisoning" (ASI06:2026) to the Agentic AI Top 10 on Dec 9, 2025
>
> Almost nobody tests for the leak in CI.

`[≈ 295 chars]`

---

## 3 · The product

> Ferryte is the source-available forgetting oracle.
>
> One line: `ferryte.instrument()`. Auto-patches Mem0 and the generic vector base (subclass for pgvector / Chroma / Qdrant). Zep + AgentCore adapters land with the design-partner cohort.
>
> One command: `ferryte test`. Plants canary memories, calls your delete API, inspects both store contents AND retrieval traces. Fails CI on leak.

`[≈ 305 chars]`

---

## 4 · What it actually does (4-step)

> The pipeline:
>
> 1. Instrument — auto-patch at construction time. Your agent code does not change.
> 2. Probe — plant deterministic canary memories tagged by source + tenant.
> 3. Delete — call your backend's REAL delete API. Not a mock.
> 4. Verify — inspect store + retrieval traces. Exit 1 on any surviving marker.

`[≈ 310 chars]`

---

## 5 · Why "verify" matters (the false-confidence trap)

> Naïve memory tests ask the agent a question and trust the answer.
>
> Agents are stochastic. Retrieval is not.
>
> Ferryte inspects the actual store contents and retrieval scores — not just final answers. A passing test means something. A failing one ships an artifact ID.

`[≈ 285 chars]`

---

## 6 · The honest part (the blind-spot map)

> Every Ferryte report has two sections: what we PROVED, and what we COULDN'T see.
>
> Un-instrumented stores, laundered LLM paraphrases, external caches — those become explicit blind spots.
>
> A forgetting oracle that hides its limits is dangerous. We say no.

`[≈ 290 chars]`

---

## 7 · Source-available (the model)

> Engine is source-available under BSL 1.1 — read it, self-host it, run it in production free. Every version converts to Apache 2.0 after three years.
>
> Cloud (hosted, alerts, history) ships *with* the first five design partners, not before. Enterprise (SSO, signed compliance receipts, premium adapters, runtime enforcement) is on the roadmap once Cloud is mature.
>
> Same playbook as Sentry, CockroachDB, HashiCorp.

`[≈ 270 chars]`

---

## 8 · Demo (no setup, no keys)

> Run the 30-second leak demo yourself, no API keys, no accounts:
>
> ```
> pip install ferryte
> python -m ferryte.demo
> ```
>
> Two tenants. One agent. Acme writes a secret, deletes it. The summary absorbs it. Agent leaks it. Ferryte catches it. Build breaks.

`[≈ 290 chars]`

**Note:** if `python -m ferryte.demo` isn't wired yet at launch, replace
with `python demo/multi_tenant_leak.py` after `git clone`. Keep one path
that works in the tweet.

---

## 9 · Who this is for

> If you ship multi-tenant memory in an AI product and your last security review took six weeks, this is for you.
>
> If you are an AppSec lead asked to prove deletion across summaries + embeddings, this is for you.
>
> If you are a compliance team writing GDPR Article 17 reports, this is for you.

`[≈ 320 chars]`

---

## 10 · CTA

> Star: github.com/getferryte/ferryte
> Read: ferryte.dev
> Design partners (first 5, six months of Cloud free when it ships, paired with the founder): pranav@ferryte.dev
>
> If you find a real leak with Ferryte in the next two weeks, I'll add you to the launch board and ship the next adapter you ask for. Reply or DM.

`[≈ 320 chars]`

---

## Posting checklist (do in order)

1. Compose tweet 1 in the X composer.
2. Attach the screencast .mp4. Add alt text.
3. Hit "Add another tweet" 9 times.
4. Paste tweets 2–10 in order.
5. **Double-check tweet 10** has the ferryte.dev link and `pranav@ferryte.dev`.
6. Post.
7. Pin tweet 1 to the profile.
8. Cross-post link to relevant Discords (r/AI_Agents, LangChain Slack, Mem0
   community). Don't blast — pick communities you're actually in.
9. Submit to HN with the title `Show HN: Ferryte – Verify your AI agent
   actually forgot deleted data` linking to ferryte.dev. (Time it for
   ~7am Pacific.)
10. Post to ProductHunt with the [pre-written copy](./producthunt.md).
11. Monitor mentions for the next 4 hours. Reply to every substantive comment
    in the first 90 minutes — that's the algo window.

## DM list (people to ping post-launch, within an hour)

Build this list before posting. Target 10–20 names. Each DM is one sentence
plus the link to tweet 1. Examples of who to ping:

- Founders of memory companies (Mem0, Zep — frame it as collaboration, not competition)
- AppSec / AI-security influencers
- AI-agent infra founders you've talked to before
- 2–3 well-known YC W25/S25 alum founders
- Anyone who has publicly tweeted about agent memory leaks or RAG hallucinations

The first hour determines the day. Treat it like a launch, not a hope.
