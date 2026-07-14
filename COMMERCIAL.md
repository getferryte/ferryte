# Commercial tiers

Ferryte is source-available under the Business Source License 1.1. The
engine in this repository is enough to trace, attribute,
and verify your agents' memory in CI and production, forever, for free.

This document describes the commercial products built on top of that engine,
and how to get access to them.

For the precise licensing boundary, see [LICENSING.md](LICENSING.md).

---

## Core (BSL 1.1) — available today

The library, the CLI (`ferryte why`, `ferryte test`), the attribution engine,
counterfactual replay, the lineage graph, and the local dashboard.

- **Price:** free, forever.
- **License:** Business Source License 1.1 — read, run, modify, and
  self-host in production for free. Converts to Apache 2.0 four years after
  each release. The only restriction: you can't resell Ferryte itself as a
  competing hosted or embedded service. (v0.1.0 remains MIT; v0.2.0–v0.2.2
  carry the earlier 3-year BSL terms.)
- **Install:** `pip install ferryte`
- **Run:** `ferryte why "the wrong answer" --tenant acme`
- **Support:** community via GitHub issues and discussions.
- **Best for:** individual developers and small teams debugging their own
  agents' memory without involving procurement.

## Cloud — pre-release

Hosted, continuous memory observability. **Not built yet.** We are building
Cloud with the first five design partners, not before. When it ships, your
instrumented agents will stream lineage to Ferryte Cloud; we will run
continuous verification, retain memory history, alert on regressions, and
integrate with the rest of your incident-response stack.

- **Price:** TBD at GA. Free for design partners through 2026.
- **License:** commercial SaaS.
- **Status:** pre-release — five design-partner seats, building together.
- **Best for:** teams running agent memory in production who want continuous
  attribution and verification rather than one-off local runs, and who need
  alerts when memory quality regresses across deploys.

**What it will include beyond Core (once built):**

- Continuous, scheduled verification runs across environments
  (dev, staging, prod).
- Historical retention of every attribution, replay, and blast-radius report
  — searchable, diff-able across runs.
- Regression alerts: a memory turning stale, a deleted source resurfacing,
  a hub-memory pattern emerging.
- Slack, PagerDuty, Linear, and generic webhook destinations.
- Per-tenant memory dashboards for incident triage.
- Org-level RBAC, projects, and environments.

**How to get in:** email `pranav@ferryte.dev` with:

1. Your stack (memory backends, agent framework, hosting).
2. Roughly how many tenants you serve and how sensitive their data is.
3. The specific memory failure you're fighting (wrong answers, stale facts,
   leaks — whatever it is).

We reply within 24 hours. We say no to most candidates. The ones we say yes
to get the first six months of Cloud free **when Cloud ships**, the founding
engineer paired with their team for the first Core integration, and a direct
line to the roadmap.

## Enterprise — roadmap

The self-hosted, hardened distribution. This is where the trust plane lives:
the things AppSec, CISO, and Compliance teams sign off on.

- **Price:** annual contract; tier based on number of agent products and
  ingested write volume. Contact sales for a quote.
- **License:** commercial enterprise agreement.
- **Status:** roadmap. Not in development yet. First contracts ship after
  Cloud has been in design-partner hands for at least two quarters.
- **Best for:** enterprises that cannot put a third party between their agent
  and their memory layer, that need attestation evidence for regulators, or
  that need premium adapters for regulated environments.

**What's included beyond Cloud:**

- Self-hosted deployment (Docker / Kubernetes / Helm).
- SSO via SAML or OIDC; SCIM provisioning; full RBAC.
- Tamper-evident audit logs of every Ferryte run, every finding, every
  remediation action.
- SOC2-ready posture and a customer-side compliance pack.
- **Premium adapters:**
  - AWS Bedrock AgentCore (with full lineage of derived long-term memory).
  - Zep / Graphiti (with shared-node-summary verification).
  - GovCloud / regulated-network variants.
  - Customer-specific adapters built and maintained by the Ferryte team.
- **Signed compliance attestations:** tamper-evident receipts proving the
  transitive deletion of a tagged source. Designed to satisfy GDPR
  Article 17 and CCPA 1798.105 right-to-be-forgotten audits.
- **Runtime retrieval enforcement (v2):** inline filtering of tainted
  retrievals before they reach the prompt, on the agent's hot path. Opt-in,
  per-tenant, latency-budgeted.
- Dedicated engineering point of contact, dedicated Slack channel, SLA on
  response and resolution.

**How to get in:** email `pranav@ferryte.dev` with subject `Ferryte Enterprise`.

---

## Open questions, answered

**Will the license ever change again?**
Not without 90 days' notice and an explicit tagged release. Every BSL version
already converts to Apache 2.0 automatically after four years, so the
community's long-term access is guaranteed in the license itself. See
LICENSING.md.

**Can I self-host the closed-source bits?**
The Enterprise tier is self-hosted. The Cloud tier is not — it is a hosted
SaaS by definition. The Core engine is, of course, self-hostable for free
under BSL.

**Can I use Core in production for free?**
Yes. Running Ferryte to debug and verify your own agents — in CI or
production — is a Permitted Purpose named in the license text. The only thing
you can't do is resell Ferryte itself as a competing product or service.

**Can I contribute to the closed-source bits?**
No. Contributions are accepted into the source-available Core only. The
contributor license (in LICENSING.md) covers our right to incorporate
contributions into the commercial tiers.

**What happens if Ferryte (the company) is acquired or shuts down?**
Every published BSL version converts to Apache 2.0 four years after its
release, and that conversion is irrevocable and baked into the license. You
can always fork and maintain your own copy. The commercial tiers are subject
to their agreements; we will publish a public commitment to a reasonable
wind-down or escrow path before taking customer money for them.

**Do you offer non-commercial / academic discounts?**
Yes for Cloud. Email us. Core is already free under BSL.

---

— The Ferryte team. `hello@ferryte.dev`.
