# Commercial tiers

Ferryte is open-core. The MIT-licensed engine in this repository is enough to
run scenarios in your CI pipeline against your own infrastructure, forever,
for free.

This document describes the closed-source commercial products built on top of
that engine, and how to get access to them.

For the precise open-source / closed-source boundary, see
[LICENSING.md](LICENSING.md).

---

## Core (MIT) — available today

The library, the CLI, the four scenarios, the lineage graph, and the local
dashboard.

- **Price:** free, forever.
- **License:** MIT.
- **Install:** `pip install ferryte`
- **Run:** `ferryte test`
- **Support:** community via GitHub issues and discussions.
- **Best for:** individual developers and small teams who want to verify
  agent forgetting in their own CI without involving procurement.

## Cloud — pre-release

The hosted forgetting oracle. **Not built yet.** We are building Cloud with
the first five design partners, not before. When it ships, you will point
your adapters at Ferryte Cloud instead of running the CI gate locally; we
will run continuous verification, retain history, alert on regressions, and
integrate with the rest of your incident-response stack.

- **Price:** TBD at GA. Free for design partners through 2026.
- **License:** commercial SaaS.
- **Status:** pre-release — five design-partner seats, building together.
- **Best for:** companies running multi-tenant memory in production who want
  continuous verification rather than periodic CI runs, and who need
  regression alerts on memory drift across deploys.

**What it will include beyond Core (once built):**

- Continuous, scheduled verification runs across multiple environments
  (dev, staging, prod).
- Historical retention of every report, every blast-radius graph, every
  finding — searchable, diff-able across runs.
- Regression alerts when a new derived artifact starts surviving deletion.
- Slack, PagerDuty, Linear, and generic webhook destinations.
- Per-tenant blast-radius dashboards (useful for incident triage).
- A public status badge for your OSS repos (`forgetting: passing`).
- Org-level RBAC, projects, and environments.

**How to get in:** email `hello@ferryte.dev` with:

1. Your stack (memory backends, agent framework, hosting).
2. Roughly how many tenants you serve and how sensitive their data is.
3. The specific leak shape you're worried about.

We reply within 24 hours. We say no to most candidates. The ones we say yes
to get the first six months of Cloud free **when Cloud ships**, the
founding engineer paired with their team for the first Core integration, and
a direct line to the roadmap.

## Enterprise — roadmap

The self-hosted, hardened distribution. This is where the trust plane lives:
the things AppSec, CISO, and Compliance teams sign off on.

- **Price:** annual contract; tier based on number of agent products and
  ingested write volume. Mid-five to mid-six figures for typical mid-market
  customers. Contact sales for a quote.
- **License:** commercial enterprise agreement.
- **Status:** roadmap. Not in development yet. First contracts ship after
  Cloud has been in design-partner hands for at least two quarters.
- **Best for:** enterprise companies that cannot put a third party between
  their agent and their memory layer, that need attestation evidence for
  regulators, or that need premium adapters for regulated environments.

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

**How to get in:** email `hello@ferryte.dev` with subject `Ferryte Enterprise`.

---

## Open questions, answered

**Will MIT-licensed features ever be re-licensed?**
Not without 90 days' notice and an explicit final MIT-tagged release. We will
not pull a Redis / Elastic / HashiCorp on the community. See LICENSING.md.

**Can I self-host the closed-source bits?**
The Enterprise tier is self-hosted. The Cloud tier is not — it is a hosted
SaaS by definition.

**Can I contribute to the closed-source bits?**
No. Contributions are accepted into the MIT-licensed Core only. The
contributor license (in LICENSING.md) covers our right to incorporate
contributions into the closed-source tiers.

**What happens if Ferryte (the company) is acquired or shuts down?**
The MIT-licensed Core is, by definition, irrevocable. You can always fork and
maintain your own copy. The closed-source tiers are subject to the terms of
their commercial agreements; we will publish a public commitment to a
reasonable wind-down or escrow path before taking customer money for them.

**Do you offer non-commercial / academic discounts?**
Yes for Cloud. Email us. Core is already MIT.

---

— The Ferryte team. `hello@ferryte.dev`.
