# Ferryte

**Memory debugging for AI agents.**
**Source-available (BSL 1.1 → Apache 2.0) · commercial Cloud + Enterprise tiers.**

[Marketing site](https://ferryte.dev) · [Live dashboard demo](https://ferryte.dev/app) · [**$500 Memory Audit**](https://ferryte.dev/audit) · [LICENSING](LICENSING.md) · [COMMERCIAL](COMMERCIAL.md)

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

## CI gate

The same lineage engine powers a deletion-verification gate. Seed canaries,
revoke through the backend's real delete API, and fail the build if a revoked
marker re-enters retrieval:

```bash
ferryte init
ferryte test --scenario source-revocation
ferryte coverage        # what was verified + the honest blind-spot map
```

Scenarios: `source-revocation`, `cross-tenant-isolation`, `stale-fact`,
`memory-poisoning`.

## Supported backends

Core ships runtime adapters for Mem0; Zep, Letta, and Cloudflare Agents
(beta); plus the instrumented `InMemoryVectorStore` reference adapter. Custom
vector stores such as pgvector, Chroma, and Qdrant need a thin adapter around
their write/search/delete surface. AWS Bedrock AgentCore is live-validated in
the public benchmark harness; a Core runtime adapter is not shipped yet.

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

The **[Agent Memory Audit](https://ferryte.dev/audit)** — fixed $500,
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
