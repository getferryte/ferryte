# Licensing

Ferryte is **open-core**: the detection engine is MIT-licensed, the commercial
trust plane is closed-source. This document is the authoritative boundary
between the two.

If you are an engineer adopting Ferryte: everything you need to run scenarios
in your CI pipeline against your own infrastructure is **MIT-licensed and
free**, forever.

If you are an enterprise buyer looking for hosted continuous verification,
signed compliance attestations, premium adapters, or runtime enforcement: see
[COMMERCIAL.md](COMMERCIAL.md).

---

## What is MIT-licensed (Ferryte Core)

The MIT license applies to the entire contents of this repository at the
commit referenced by the latest tagged `ferryte-core-*` release, except as
explicitly carved out below. The full text of the license is in
[LICENSE](LICENSE).

The MIT surface includes, without limitation:

- The Python package `ferryte` published to PyPI:
  - `ferryte.instrument()` and the auto-patching machinery
  - `ferryte.tag()` provenance context manager
  - The lineage graph (`ferryte.lineage`) and its SQLite store
  - The four shipped scenarios:
    - `source-revocation`
    - `cross-tenant-isolation`
    - `stale-fact`
    - `memory-poisoning`
  - The forgetting-oracle runner (`ferryte.oracle`)
  - The Mem0 adapter (`ferryte.adapters.mem0`)
  - The generic vector-store adapter (`ferryte.adapters.vector`)
  - The coverage and blind-spot report writers (`ferryte.reports`)
  - The local HTTP API for the dashboard (`ferryte.api`)
- The `ferryte` CLI:
  - `ferryte init`
  - `ferryte test`
  - `ferryte coverage`
  - `ferryte list-scenarios`
  - `ferryte serve`
- The Next.js dashboard (`dashboard/`) when run locally against a local API.
- The marketing site source (`dashboard/src/app/(marketing)/`).
- All tests, demos, and documentation under `tests/`, `demo/`, `launch/`.

You may use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of this surface, subject only to the conditions in [LICENSE](LICENSE).

## What is NOT MIT-licensed (Ferryte Cloud + Enterprise)

The following are **separate, closed-source products** built and maintained by
the Ferryte team, distributed under separate commercial agreements, and **not**
present in this repository:

- **Ferryte Cloud** — the hosted forgetting oracle.
  - Continuous, multi-environment verification runs.
  - Historical report retention and regression alerting.
  - Slack, PagerDuty, Linear, and webhook integrations.
  - Multi-tenant management of Ferryte itself (orgs, projects, RBAC).
  - Public status badges for OSS repos.

- **Ferryte Enterprise** — the self-hosted hardened distribution (roadmap).
  - SSO (SAML / OIDC), SCIM, and RBAC.
  - Tamper-evident audit logs.
  - SOC2-ready posture and customer support SLA.
  - Premium support, dedicated Slack channel, dedicated engineering point of contact.

- **Premium adapters** — closed-source connectors for systems with proprietary
  delete semantics, regulated environments, or commercial source code. As of
  v0.1, these include (planned):
  - AWS Bedrock AgentCore
  - Zep / Graphiti
  - GovCloud / regulated-network variants
  - Customer-specific adapters bundled with Enterprise

- **Compliance attestation layer** — the signed, tamper-evident receipts
  produced when a forgetting run completes successfully against a
  customer-tagged source. GDPR Article 17 and CCPA 1798.105 evidence
  generation. Available in Enterprise.

- **Runtime retrieval enforcement** — the inline filter that blocks tainted
  retrievals before they reach the prompt. Latency-sensitive, load-bearing,
  intentionally not in the OSS core. Available in Enterprise (v2).

- **Ferryte trademarks, logos, and brand assets** — see "Trademarks" below.

These products may incorporate, depend on, or wrap MIT-licensed code from this
repository. The MIT license does **not** grant any right to redistribute,
relicense, or rebrand the closed-source products under any name (including
"Ferryte").

## Contributor License Agreement

By submitting a pull request, issue comment, patch, suggestion, or any other
contribution to this repository, you grant Ferryte and its successors a
perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable
license to:

1. Use, reproduce, prepare derivative works of, publicly display, publicly
   perform, sublicense, and distribute your contributions under the MIT
   license; **and**
2. Incorporate your contributions into the closed-source Ferryte Cloud and
   Ferryte Enterprise products described above, under whatever commercial
   license those products are distributed under.

This dual-license grant is the standard open-core CLA pattern. It exists so
that Ferryte can continue to invest in the OSS core, fund full-time engineering
on it, and survive as a company. If you cannot accept these terms, please do
not submit contributions.

If you contribute on behalf of an employer, you represent that you are
authorized to grant this license on your employer's behalf.

You retain all moral rights and the right to use your contribution for any
other purpose. Ferryte will list significant contributors in the project's
CONTRIBUTORS file.

For large or strategic contributions (e.g. a new adapter, a new scenario, a
significant rework of the lineage engine), we encourage opening an issue or
RFC first so we can discuss scope, ownership, and whether the contribution is
a better fit for Core, a third-party plugin, or a commercial Premium adapter.

## Trademarks

"Ferryte" and the Ferryte wordmark and dot mark are trademarks of the Ferryte
project and its commercial entity. The MIT license **does not** grant
permission to use the Ferryte trademarks, logos, or design assets in
connection with derived works, forks, or commercial products. Forks must be
clearly distinguished by name.

For permitted uses (academic citation, fair use, integration documentation that
says "works with Ferryte"), no permission is needed. For anything else
(distributing a fork under a similar name, using the wordmark in a commercial
product, t-shirts, conference branding), email `hello@ferryte.dev`.

## Trust statement

We chose open-core because:

1. **Security tooling that inspects sensitive memory data cannot be
   closed-source** and be trusted at the scale we are targeting. Every claim
   Ferryte makes about your data must be auditable by reading our source.
2. **Bottoms-up adoption** by engineering leads is the only credible go-to-
   market for a developer security product. Closed-source kills adoption
   velocity before it can compound.
3. **The moat is not the code.** It is the brand, the network of adapter
   integrations, the design-partner data, and the team's expertise across
   every major memory backend. Those things are not threatened by an open
   engine; they are accelerated by one.

We will publish significant model changes (e.g. a new license, a major
re-license, a change to the contributor agreement) at least 90 days in advance
and tag the last MIT-licensed release explicitly.

— The Ferryte team
