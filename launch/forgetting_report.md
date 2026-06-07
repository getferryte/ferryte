# The Forgetting Report — plan & spec

A public, reproducible benchmark of "delete-after-revoke" behaviour across popular
agent-memory stacks. It doubles as Ferryte's launch and its traction story:
it empirically confirms the leak the platform vendors already admit in their own docs.

---

## 1. Goal

Publish a credible, reproducible study: *"We deleted the data from N popular
AI-memory stacks. Here's how many still remembered it."* Plus an open benchmark
anyone can run, so we own the way "agent forgetting" gets measured.

## 2. Strategic frame

- Attack the **category problem**, never any company's private systems. Everything
  runs on **our own deployments** of public / open-source tools. Legal, defensible,
  reproducible.
- Become the **referee** of agent forgetting — own the measurement standard.
- Demand is downstream of **GDPR Art. 17 / CCPA**. Position the benchmark as the
  evidence standard regulators and auditors point to.

## 3. Credibility is the whole game (non-negotiables)

The report dies the moment the methodology looks rigged. So:

1. Test **real backends in their default / recommended configs** — not strawmen.
2. Use realistic **multi-tenant agent-memory** setups, including derived memory
   (summaries / graph nodes) where the framework provides it — because that's where
   the leak actually lives. Raw CRUD on a vector store may legitimately PASS; the
   summary/graph layer is the story.
3. **Fully reproducible**: pinned versions, docker-compose, one command, public repo.
4. Keep the illustrative **in-memory baseline** (which we built to demonstrate the
   leak) clearly separate from real-backend results. Never blend them.
5. Offer vendors **right-of-reply** before publishing (notify 5–7 days ahead). Frame
   constructively ("here's the fix"), never cruelly. We confirm their own docs.

## 4. Benchmark design

- **Matrix:** backend × scenario.
- **Backends (launch set, LOCKED):** Mem0, pgvector, Chroma, Qdrant, Zep (self-hosted
  CE), **AWS Bedrock AgentCore**. AgentCore is in at launch (it's the headline name) —
  but it must **not block the launch**: if AWS setup slips, we ship the other five and
  add AgentCore in a fast-follow.
- **Scenarios (already built):** source-revocation, cross-tenant isolation,
  stale-fact overwrite, memory-poisoning.
- **Cell result:** PASS (forgot) / FAIL (leaked) / BLIND (couldn't verify).
- **Forgetting Score** per backend = % of scenarios cleanly passed → leaderboard rank.
- Document each backend's exact config + the delete path exercised.

## 5. Build scope

**Already exists:** Mem0 adapter, generic vector base, 4 scenarios, JSON/HTML reports,
lineage graph, CLI.

**Architecture finding (from reading `adapters/vector.py`):** the current `VectorAdapter`
is tightly coupled to the in-memory store's internals — "just subclass it" understates
the work. And raw vector DBs don't leak on their own (a row delete is clean); the leak
requires an **LLM summarization / derived-memory layer** on top. So the real net-new
work is a **shared multi-tenant "summary memory" layer** (using the OpenAI key) that we
run over each raw store, plus per-store CRUD adapters. Frameworks with built-in derived
memory (Mem0, Zep, AgentCore) are tested through their own delete APIs. This is the
honest, defensible design — and the reason the LLM key is central.

**To build:**

| Item | Notes | Est. |
|---|---|---|
| pgvector / Chroma / Qdrant subclasses | Configure client + delete path on the vector base | ~0.5–1 day each |
| Zep adapter | Implement the 5-method `Adapter` protocol against Zep CE / Graphiti; key surface = graph node summaries | ~3–5 days |
| Realistic agent configs | Multi-tenant, with summarization where supported, per stack | ~2–3 days |
| Benchmark harness | Orchestrate matrix runs, emit `results.json` + scorecards + leaderboard data | ~2–3 days |
| Reproducibility | docker-compose, pinned deps, `make benchmark` | ~1 day |
| (Stretch) AgentCore adapter | Needs AWS account + Bedrock cost | ~1 wk |

The adapter contract is 5 methods: `patch`, `unpatch`, `delete_source`,
`list_artifacts_for_source`, `probe` (see `src/ferryte/adapters/base.py`).

## 6. Public artifacts

1. **Open benchmark** — code + compose + one-command run (in-repo `benchmark/` or a
   dedicated repo).
2. **Leaderboard page** at `ferryte.dev/benchmark` — the matrix, scores, methodology,
   and a prominent "reproduce it yourself."
3. **The Report** (long-form): problem → method → results → per-backend findings →
   how to fix → blind spots & limits → FAQ pre-empting "you rigged it."
4. **Launch assets:** X thread, Show HN, Product Hunt (adapt the existing launch kit).

## 7. Narrative / thread skeleton

1. Hook: *"We deleted the data from N popular AI-memory stacks. Most still remembered it."*
2. The proof: the results matrix image.
3. Why it happens: derived memory / summaries / graph nodes (+ vendor quotes).
4. Why it matters: GDPR Art. 17, cross-tenant exposure, security.
5. The honest part: blind spots, what we did **not** test, exact configs used.
6. Reproduce it yourself: repo link.
7. What to do: Ferryte in CI; opt-in free audit offer.

## 8. Timeline (full-time, ~3.5–4 weeks with AgentCore)

- **Week 1:** vector subclasses (pgvector/Chroma/Qdrant) + docker-compose + harness;
  realistic multi-tenant configs with summarization.
- **Week 2:** Zep adapter (graph summaries) + AgentCore adapter (AWS Bedrock).
- **Week 3:** run the full matrix, build the `/benchmark` leaderboard page, write the report.
- **Week 4:** methodology hardening, polish, launch everywhere at once.

AgentCore (AWS) is the schedule risk — if it slips, launch with the other five and
fast-follow.

## 9. Risks & mitigations

| Risk | Mitigation |
|---|---|
| "You rigged it" | Default configs, reproducible, transparent; baseline kept separate |
| **Conflict of interest — "they sell the fix, of course they find leaks"** | This is the sharpest attack since we publish cold. Mitigate with (a) airtight repro, (b) a fair "how to configure safely / how to fix" section per tool, (c) publish exact configs + versions so anyone can falsify us |
| Vendor backlash | Constructive framing, confirm their own docs; consider a 48h pre-brief courtesy |
| AgentCore cost/complexity | Must not block launch; fast-follow if AWS slips |
| Methodology critique on summaries | Use each framework's own summarization features; document exactly |
| Scope creep | Ship with the 6 locked backends; no new ones mid-build |

## 10. YC tie-in

- **Demonstrated, quantified pain** = the report.
- **Distribution + community** = the open benchmark everyone can run.
- **Traction** = inbound design partners / audit requests from the launch.

## 11. Locked decisions

1. **Backend set:** Mem0 + pgvector + Chroma + Qdrant + Zep + AWS Bedrock AgentCore.
2. **AgentCore:** included at launch (must not block; fast-follow if AWS slips).
3. **Home:** `/benchmark` route on `ferryte.dev` + code in the main repo.
4. **Right-of-reply:** publish cold (no advance notice). → Lean extra hard on
   reproducibility + a fair "how to fix" section to blunt the conflict-of-interest attack.
5. **Name:** TBD — "The Forgetting Report" (working title).

## 12. Prerequisites the founder must provide

These gate the actual benchmark runs (I can write all the code; these need your accounts/keys):

- **LLM + embedding API key** (e.g., OpenAI) — required for the summarization layer that
  *creates* the derived-memory leak. This is the heart of the test.
- **Docker** locally (or a cheap VM) for pgvector / Chroma / Qdrant / Zep CE.
- **AWS account with Bedrock + AgentCore access** + budget for the AgentCore run.
- Decide the final **report name** and confirm the `/benchmark` page goes live on the
  production site.
