# Licensing

Ferryte is **source-available** under the **Business Source License 1.1
(BSL 1.1)**. You can read every line, run it, modify it, and use it in
production for free — the one thing you cannot do is resell Ferryte itself as
a competing commercial product or service. Four years after each version
ships, that version automatically converts to **Apache 2.0** and becomes
fully open source.

This is the model MariaDB created and that CockroachDB, HashiCorp, and
Couchbase use. It exists so we can fund full-time engineering on Ferryte
without a hyperscaler cloning the hosted product the week we launch it.

---

## TL;DR

| You want to... | Allowed? |
| --- | --- |
| Read the full source, audit every line | ✅ Yes |
| Run Ferryte in your own CI / infra, in production | ✅ Yes |
| Modify it, fork it, build internal tooling on it | ✅ Yes |
| Redistribute it (with the license intact) | ✅ Yes |
| Use any 4-year-old version under Apache 2.0 | ✅ Yes |
| Sell a hosted or embedded product that is, in substance, Ferryte | ❌ No — buy a commercial license |

If you are an engineer using Ferryte to debug and verify *your own* agents:
you are unambiguously in the green. The restriction only bites would-be
resellers of Ferryte itself.

---

## License history

| Versions | License | Converts to |
| --- | --- | --- |
| v0.1.0 | MIT ([LICENSE-MIT.txt](LICENSE-MIT.txt)) | — (MIT forever) |
| v0.2.0 – v0.2.2 | BSL 1.1 ([LICENSE-BSL.txt](LICENSE-BSL.txt)) | Apache 2.0, 3 years after each release |
| v0.2.3 and later | BSL 1.1, updated grant ([LICENSE](LICENSE)) | Apache 2.0, 4 years after each release |

A published release cannot be retroactively relicensed; each version keeps
the terms it shipped with. The v0.2.3 update did two things: refreshed the
"competing offering" definition to match what Ferryte actually is now (memory
debugging and observability for AI agents, not just deletion verification),
and set the Change Date to the BSL maximum of four years.

---

## What the license allows (plain language)

The license text in [LICENSE](LICENSE) is canonical; this section is the
human summary. If the two ever conflict, the LICENSE file wins.

**You may, for free:**

- Copy, modify, and create derivative works of the source.
- Run Ferryte in production — in CI, against your own agents, inside your own
  company, for your own customers' data. The Additional Use Grant permits
  production use explicitly.
- Use it in professional services (e.g. a consultancy debugging a client's
  agent memory and handing them the report).
- Redistribute it, keeping the license and notices intact.
- Use any version that is four years old or older under plain Apache 2.0.

**You may not, without a commercial license:**

- Offer Ferryte to third parties on a hosted or embedded basis that competes
  with a Ferryte commercial offering — i.e. you cannot stand up
  "MemoryDebugCloud, powered by Ferryte" and sell agent-memory debugging,
  observability, attribution, or verification as a managed service.

That single carve-out is the entire commercial protection. Everything else is
permitted.

If you are not sure which side of the line you are on, email
`hello@ferryte.dev` and we will tell you plainly. We would much rather grant a
free exception than have a confused user walk away.

---

## What the commercial products add

The commercial tiers are described in [COMMERCIAL.md](COMMERCIAL.md):

- **Ferryte Cloud** — hosted, continuous memory observability: scheduled
  verification runs, historical memory timelines, regression alerts, and
  integrations (Slack / PagerDuty / Linear).
- **Enterprise** — self-hosted distribution with SSO, RBAC, audit logs,
  premium adapters, signed compliance attestations, and an SLA.

You never *need* these to use Ferryte. They exist for teams that want the
hosted trust plane and the compliance paper trail rather than operating
everything themselves.

---

## Contributor License Agreement

By submitting a pull request, patch, or any other contribution to this
repository, you grant Ferryte and its successors a perpetual, worldwide,
non-exclusive, no-charge, royalty-free, irrevocable license to:

1. Use, reproduce, prepare derivative works of, publicly display, publicly
   perform, sublicense, and distribute your contributions under the
   Business Source License 1.1 and its eventual Apache 2.0 conversion;
   **and**
2. Incorporate your contributions into the commercial Ferryte Cloud and
   Ferryte Enterprise products, under whatever license those are distributed.

This dual-license grant is the standard pattern for BSL projects. If you
cannot accept these terms, please do not submit contributions.

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

1. **Auditability is non-negotiable.** A tool that inspects your agents'
   memory, retrieval traces, and answers must be readable end-to-end. BSL
   keeps 100% of the source open to read, run, and self-host.
2. **A pure-MIT core invites a clone of the hosted product.** The 2021–2024
   relicensing wave taught the industry that a permissively-licensed infra
   tool can be repackaged as a managed service faster than the original
   author can monetize it. BSL closes that one hole and nothing else — and we
   adopted it early, before mass adoption, rather than pulling the rug later.
3. **It still becomes fully open, guaranteed.** Every version converts to
   Apache 2.0 after four years, irrevocably, baked into the license text.
   Nothing is locked away forever.

We will announce any future licensing change at least 90 days in advance and
tag the affected releases explicitly.

— The Ferryte team. `hello@ferryte.dev`
