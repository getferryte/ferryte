# Design partner program

## What it is

Five paid pilots in 2026. First six months of Ferryte Cloud free. A named
Ferryte engineer paired with your team for the first integration. Direct
input on the roadmap. Public credit if you want it; quiet pilot if you don't.

## ICP — who we are looking for

- **Stage:** Series A–B AI-native B2B SaaS.
- **Engineering size:** 30–500.
- **Memory layer:** persistent + multi-tenant. Mem0, Zep, pgvector, Pinecone,
  Chroma, AgentCore — we cover them in that order.
- **Pain shape:** last security review took weeks, AppSec asked "how do you
  prove deletion across your memory layer," and you had no good answer.
- **Decision-maker reachable in one email.** We do not chase procurement at
  this stage.

## Disqualifiers (politely say no)

- Solo / hobby projects. The problem exists at multi-tenant scale.
- Pure RAG-over-public-docs apps. No persistent memory, no real problem.
- Enterprises whose memory is fully in their VPC, fully single-tenant. We
  serve them via Enterprise (self-hosted), not Cloud.
- Teams "exploring AI" but not shipping multi-tenant memory in 2026.

## Outreach email template

**Subject:** Memory leak verification for ${COMPANY}

**Body:**

> Hi ${FIRST_NAME},
>
> I'm ${YOUR_NAME}, building Ferryte — an open-core forgetting oracle for AI
> agents.
>
> AWS's own AgentCore docs admit it: *"deleting an event doesn't remove the
> structured information derived out of it from the long term memory."*
> Zep says the same about shared node summaries. OWASP added memory
> poisoning (ASI06) to the Agentic Top 10 last December. Almost nobody is
> testing for the leak in CI yet.
>
> ${COMPANY} caught my attention because ${SPECIFIC_REASON — multi-tenant
> memory in production / Series-A funding announcement / a tweet about
> RAG failures / a job posting for an AppSec lead}. The exact failure shape
> Ferryte catches: a user's revoked data still surfacing through a derived
> summary or embedding after the official delete API has been called.
>
> The ask is small. Fifteen minutes on a call where I demo the leak against
> a Mem0 / pgvector stack like yours, and you tell me whether the bottom-up
> "drop into CI" framing maps to how ${COMPANY} thinks about memory testing.
> If we both want to continue, the design-partner offer is: first six months
> of Ferryte Cloud free, a named Ferryte engineer paired with your team for
> the first integration, and you shape the roadmap.
>
> Worst case for you: fifteen minutes and a tool you can `pip install`
> for free.
>
> Calendly: ${LINK}. Or reply with three windows that work this week.
>
> Best,
> ${YOUR_NAME}
>
> ferryte.dev · github.com/getferryte/ferryte

## Follow-up cadence

- **Day 0:** initial email.
- **Day 4:** soft bump — "just want to make sure this didn't land in spam."
- **Day 11:** final bump — a one-line update with a specific new piece of
  social proof (a star count, a leaked-find from another design partner, a
  link to the X thread). Then drop it.

## Target list — who to send this to

The first 30. Build the list before the X thread goes live so you can DM
the post to these people in the launch hour.

| Tier | Why | How to reach |
|---|---|---|
| **A — warm intros only.** Founders / heads-of-eng at AI-native SaaS you can be introduced to via a mutual. | Highest conversion. | Ask the warm node. |
| **B — public signal.** Founders who have tweeted about RAG leaks, agent memory bugs, AppSec friction. | Mid conversion; they have the problem language. | Reply to the relevant tweet, then DM. Do not cold-email straight away. |
| **C — cold but ICP-matched.** Series A–B AI startups on YC / Crunchbase / Sequoia portfolio whose product description includes "memory" or "personalisation" with multi-tenant. | Low conversion; volume play. | Cold email via the template above. |

Aim for 10 × A, 10 × B, 10 × C. The A tier converts; the B+C tiers fund
the social-proof tweet at week 2 ("five design partners signed up").

## Tracking

A flat markdown file at `launch/design_partners.tracker.md` (gitignored — not
in this repo). Columns: company, contact, role, tier, source, sent date,
reply date, status, next-action date.

Do not over-engineer this. A tab in Linear is better than a CRM at this
stage.
