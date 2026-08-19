# Ferryte

**Memory debugging for AI agents.**
**Source-available (BSL 1.1 → Apache 2.0) · commercial Cloud + Enterprise tiers.**

[Marketing site](https://ferryte.dev) · [Live dashboard demo](https://ferryte.dev/app) · [**$3,000 Memory Audit**](https://ferryte.dev/audit) · [LICENSING](LICENSING.md) · [COMMERCIAL](COMMERCIAL.md)

Your agent gave a wrong, stale, or leaked answer. Somewhere in its memory is
the artifact that caused it. Ferryte finds that artifact, shows you the
evidence, and proves the fix worked.

```bash
pip install ferryte
ferryte why "your plan includes 24/7 phone support" --tenant acme
```

```
#1  mem_a41f9c2e  ·  confidence 1.00  ·  STALE BELIEF
    shared span: "includes 24/7 phone support"
    superseded by mem_77b0d1 ("phone support was dropped in the March plan change")
    last retrieved 2h ago · written 41 days ago · source: sales-call-0311
    fix: ferryte delete mem_a41f9c2e --cascade
```

## Why this exists

Agent memory is production state, but when it misbehaves there is no
debugger for it. Logs show *what* the agent said; nothing shows *which
memory made it say that*. Teams grep vector stores by hand, guess, delete,
and hope.

Ferryte is the missing layer — think Sentry, but for agent memory:

- **Trace**: one line (`ferryte.instrument()`) records every memory write,
  retrieval, and delete, building a lineage graph from each source to every
  derived artifact.
- **Attribute**: `ferryte why` ranks the memories that caused a given answer
  — IDF-weighted content overlap, shared-span evidence, retrieval traces,
  and exact answer→memory edges when you opt in via `ferryte.record_answer()`.
- **Diagnose**: each suspect is labeled — stale belief (structurally provable
  via supersession edges), zombie memory (deleted but still retrieved),
  cross-tenant leak, phantom memory (source revoked), hub memory
  (poisoning-style retrieval fan-out).
- **Replay & verify**: `ferryte why --replay` re-runs retrieval without the
  suspect and shows what would have entered the context instead. After the
  fix, the same command proves the bad memory is gone.

## Quickstart

```python
import ferryte

ferryte.instrument()          # one line; auto-patches detected memory clients
# ... your agent runs as usual ...

# optional, for exact attribution:
ferryte.record_answer(answer_text, query=user_query, artifact_ids=context_ids)
```

Then, when something goes wrong:

```bash
ferryte why "the bad answer text" --tenant acme --since 2h
ferryte why "the bad answer text" --tenant acme --query "original user query" --replay
```

## Can one tenant reach another's data?

Published measurements put cross-tenant leakage at **83%** in multi-tenant RAG
built on logical isolation without access control at the retrieval layer — which
is the default shape of most AI SaaS, because per-tenant indexes are expensive.
Most teams have no instrument that would tell them either way.

One command, no instrumentation, read-only:

```bash
ferryte isolation-check "postgres://user:pass@host/db" \
  --table memories \
  --tenants acme,globex \
  -q "what are our renewal terms?" \
  --markdown isolation.md
```

Three probes, in increasing order of what they prove:

1. **Filtered** — each tenant's queries run *with* the tenant filter. A foreign
   document here means the filter itself is broken. Hard fail.
2. **Unfiltered blast radius** — the same queries with no filter, measuring what
   a single forgotten `WHERE` clause would expose. Reported as exposure, never
   as a defect, because an unfiltered query is not by itself a bug.
3. **Semantic neighbours** — queries derived from one tenant's own documents,
   run as another tenant. This is reach through *similarity* rather than a
   missing predicate, and it is the path that produces no error in any log.

Exits non-zero on a real leak, so it works as a CI gate as well as a one-off.

## Proving a deletion actually happened

GDPR's accountability principle means it is not enough to delete — you have to be
able to demonstrate it. The EDPB's 2025 coordinated enforcement action on the
right to erasure found most organisations cannot.

```bash
ferryte attest-deletion "postgres://…" \
  --source user_8813 \
  --probe "the distinctive phrase that should now be gone" \
  --sign --markdown attestation.md

ferryte verify-attestation attestation.json
```

You get a dated, hash-chained, Ed25519-signed record of what was deleted, what
was probed afterwards, what those probes returned — and, printed as prominently
as the successes, **what could not be verified**.

> This attests to what Ferryte observed through the connections it was given. It
> is **not** a certificate of regulatory compliance, and it does not claim to be.
> Backups, replicas, downstream exports and model weights are outside its reach,
> and every generated attestation says so on its face.

## CI gate

Fail the build when a change lets one tenant reach another, or when a deletion
cannot be verified:

```yaml
- uses: getferryte/ferryte@v1
  with:
    uri: postgres://…
    tenants: acme,globex
    queries: |
      what are our renewal terms?
      summarise last quarter
```

Or drive the forgetting battery directly:

```bash
ferryte init
ferryte test --scenario source-revocation
ferryte coverage        # what was verified + the honest blind-spot map
```

Scenarios: `source-revocation`, `cross-tenant-isolation`, `stale-fact`,
`memory-poisoning`, `mosaic`.

## Supported backends

| Backend | State | Install |
|---|---|---|
| **pgvector** (PostgreSQL) | shipped | `pip install 'ferryte[pgvector]'` |
| **Chroma** | shipped | `pip install 'ferryte[chroma]'` |
| **Qdrant** | shipped | `pip install 'ferryte[qdrant]'` |
| Mem0 | shipped | `pip install 'ferryte[mem0]'` |
| In-memory reference store | shipped | included |
| Zep · Letta · Cloudflare Agents | beta | included |
| AWS Bedrock AgentCore | benchmark-only — no runtime adapter yet | — |

`pip install 'ferryte[all]'` gets every backend plus attestation signing.

**On embeddings, plainly:** pgvector and Qdrant store vectors from *your* model,
which Ferryte cannot reproduce. Pass an `embedder` and probes run true vector
similarity; omit it and they fall back to a lexical scan, which still catches
exact-token leaks but can miss paraphrased ones — and records a blind spot
saying exactly that. Chroma embeds queries itself, so semantic probing there is
meaningful out of the box. Anything else with write/search/delete can be wrapped
by implementing the five hooks in `adapters/base.py`.

## Project layout

```
ferryte/
├── src/ferryte/            # Python core + CLI (pip install ferryte)
│   ├── instrument.py       # one-line auto-patching
│   ├── adapters/           # memory-backend adapters
│   ├── lineage/            # source → artifact graph, answer lineage, supersessions
│   ├── oracle/             # attribution engine, counterfactual replay, scenarios
│   ├── reports/            # coverage + blind-spot map
│   └── api/                # local HTTP server feeding the dashboard
├── dashboard/              # Next.js marketing site + dashboard
├── benchmark/              # public backend benchmark harness
├── action.yml              # GitHub Action: isolation + forgetting checks in CI
└── tests/
```

## Licensing

Ferryte is **source-available** under the Business Source License 1.1: read,
run, modify, and self-host in production for free. Each version converts to
Apache 2.0 four years after release. The one thing the license does not
permit is reselling Ferryte itself as a competing hosted or embedded service.
Same model as MariaDB, CockroachDB, and HashiCorp.

- **v0.2.3 and later:** BSL 1.1, 4-year conversion — see [LICENSE](LICENSE).
- **v0.2.0 – v0.2.2:** BSL 1.1, 3-year conversion — see [LICENSE-BSL.txt](LICENSE-BSL.txt).
- **v0.1.0:** MIT — see [LICENSE-MIT.txt](LICENSE-MIT.txt).

Details, contributor license, and trademark policy: [LICENSING.md](LICENSING.md).
Commercial tiers (Cloud, Enterprise): [COMMERCIAL.md](COMMERCIAL.md).

## Want us to run this on your stack?

The **[Agent Memory Audit](https://ferryte.dev/audit)** — fixed $3,000,
48-hour turnaround, runs entirely in your infrastructure. We instrument your
agent with you, run the full forgetting battery, trace your worst wrong
answers to the memories that caused them, and hand you the evidence and the
fix list. Money back if we find nothing actionable.
Email `pranav@ferryte.dev` with subject `Audit`.

## Status

Pre-launch. The source-available engine ships now; Cloud and Enterprise gate
behind design partners. Looking for teams running AI agents with persistent
memory in production who are fighting wrong answers they can't explain.

If that is you: open an issue, email `pranav@ferryte.dev`, or reach out via
the site.
