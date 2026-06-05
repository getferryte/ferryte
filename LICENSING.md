# Licensing

Ferryte is **source-available**, licensed under the **Business Source License
1.1 (BSL)**. You can read all of the source, run it, modify it, and use it in
production for free — the one thing you cannot do is sell a hosted or embedded
service that competes with Ferryte's own commercial offering. Three years
after each version ships, that version automatically converts to the
**Apache License 2.0** and becomes fully open source.

This is the same model used by Sentry, CockroachDB, HashiCorp (Terraform/
Vault), and MariaDB. It exists so we can fund full-time engineering on Ferryte
without a hyperscaler cloning the hosted product the week we launch it.

This document is the authoritative explanation of the boundary.

---

## TL;DR

| You want to... | Allowed under BSL? |
| --- | --- |
| Read the full source, audit every line | ✅ Yes |
| Run Ferryte in your own CI / infra, in production | ✅ Yes |
| Modify it, fork it, build internal tooling on it | ✅ Yes |
| Redistribute it (with the license intact) | ✅ Yes |
| Use the 3-year-old version under Apache 2.0 | ✅ Yes |
| Offer a hosted "memory forgetting verification" service that competes with Ferryte Cloud | ❌ No — buy a commercial license |

If you are an engineer adopting Ferryte to verify *your own* agents: you are
unambiguously in the green. The restriction only bites would-be competitors.

---

## Version history of the license

- **v0.1.0** — published under the **MIT License**. A published release cannot
  be retroactively relicensed, so v0.1.0 (and any earlier release) remain MIT
  in perpetuity. See [LICENSE-MIT.txt](LICENSE-MIT.txt).
- **v0.2.0 and later** — published under the **Business Source License 1.1**,
  converting to **Apache 2.0** three years after each version's release date.
  See [LICENSE](LICENSE).

---

## What the BSL allows (plain language)

The license text in [LICENSE](LICENSE) is the canonical, legally-binding
version. This section is the human summary; if the two ever conflict, the
LICENSE file wins.

**You may, for free:**

- Copy, modify, and create derivative works of the source.
- Run Ferryte in production — in your CI pipeline, against your own agents,
  inside your own company, for your own customers' data. Using Ferryte to
  verify the agents *you* ship is explicitly permitted production use.
- Redistribute Ferryte, as long as you keep the license and notices intact.
- Use any version that is three years old or older under the Apache 2.0
  license, with no restrictions at all.

**You may not, without a commercial license:**

- Offer the Licensed Work to third parties as a hosted or embedded service
  that competes with a Ferryte commercial offering — i.e. you cannot stand up
  "ForgetfulCloud, powered by Ferryte" and sell memory-forgetting
  verification as a managed service.

That single carve-out is the entire commercial protection. Everything else is
permitted.

---

## The Additional Use Grant, in detail

The LICENSE file contains an "Additional Use Grant" that defines exactly what
production use is permitted. In plain terms:

> You may make production use of Ferryte, provided you do not offer it to
> third parties on a hosted or embedded basis that competes with a Ferryte
> commercial offering.

A **competing offering** means a product or service, marketed to third
parties, whose value proposition is verification, auditing, or attestation of
AI agent memory forgetting delivered as a managed or hosted service.

Things that are **fine**:

- A SaaS company running Ferryte in CI to verify its own multi-tenant agent.
- A consultancy running Ferryte during a client engagement and handing the
  client a report.
- A platform embedding Ferryte to test *its own* product internally.

Things that **need a commercial license**:

- A cloud vendor wrapping Ferryte in an API and reselling "agent memory
  verification as a service" to the public.
- A competitor shipping a hosted dashboard that is, in substance, Ferryte
  Cloud under a different name.

If you are not sure which side of the line you are on, email
`hello@ferryte.dev` and we will tell you plainly. We would much rather grant a
free exception than have a confused user walk away.

---

## What the commercial products add

The commercial tiers are described in [COMMERCIAL.md](COMMERCIAL.md). At a
high level, paying for Ferryte gets you the things a source-available CLI
cannot give you on its own:

- **Ferryte Cloud** — the hosted, continuous verification service: scheduled
  re-runs, historical reports, regression alerting, and integrations
  (Slack / PagerDuty / Linear).
- **Compliance attestations** — signed, tamper-evident receipts that a
  forgetting run succeeded against a customer-tagged source, for GDPR
  Article 17 and CCPA evidence.
- **Enterprise** — SSO, RBAC, audit logs, premium adapters, runtime retrieval
  enforcement, and a support SLA.

You never *need* these to use Ferryte. They exist for teams that want the
hosted trust plane and the compliance paper trail rather than running and
operating everything themselves.

---

## Contributor License Agreement

By submitting a pull request, patch, or any other contribution to this
repository, you grant Ferryte and its successors a perpetual, worldwide,
non-exclusive, no-charge, royalty-free, irrevocable license to:

1. Use, reproduce, prepare derivative works of, publicly display, publicly
   perform, sublicense, and distribute your contributions under the Business
   Source License 1.1 and its eventual Apache 2.0 conversion; **and**
2. Incorporate your contributions into the commercial Ferryte Cloud and
   Ferryte Enterprise products, under whatever license those are distributed.

This dual-license grant is the standard pattern for BSL projects. It exists so
Ferryte can keep investing in the source-available core and survive as a
company. If you cannot accept these terms, please do not submit contributions.

If you contribute on behalf of an employer, you represent that you are
authorized to grant this license on your employer's behalf.

For large or strategic contributions (a new adapter, a new scenario, a rework
of the lineage engine), please open an issue or RFC first so we can discuss
scope and ownership.

---

## Trademarks

"Ferryte" and the Ferryte wordmark and dot mark are trademarks of the Ferryte
project and its commercial entity. The license **does not** grant permission
to use the Ferryte trademarks, logos, or design assets for derived works,
forks, or commercial products. Forks must be clearly renamed.

Permitted without asking: academic citation, fair use, and integration
documentation that says "works with Ferryte." For anything else, email
`hello@ferryte.dev`.

---

## Why BSL and not MIT or pure-closed

We started on MIT (v0.1.0) and deliberately moved to BSL for v0.2.0. The
reasoning:

1. **Auditability is non-negotiable.** Security tooling that inspects
   sensitive memory data must be readable end-to-end. BSL keeps 100% of the
   source open to read and self-host — it is *source-available*, not closed.
2. **A pure-MIT core invites a hyperscaler clone.** The 2021–2024 wave
   (Elasticsearch, Redis, HashiCorp, Sentry) taught the whole industry that an
   MIT/Apache infra tool can be repackaged as a managed service by a cloud
   provider faster than the original author can monetize it. BSL closes that
   one hole and nothing else.
3. **It still becomes fully open.** Every version converts to Apache 2.0 after
   three years. Nothing is locked away forever; we are buying a three-year
   head start on the hosted product, not permanent enclosure.

We will publish any future licensing change at least 90 days in advance and
tag the affected releases explicitly.

— The Ferryte team. `hello@ferryte.dev`
