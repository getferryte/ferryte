# The Forgetting Report — benchmark harness

A reproducible benchmark of **delete-after-revoke** behaviour across popular
agent-memory stacks. Plant a canary, call the stack's real delete API, then check
whether the agent (and the underlying store) can still surface it.

> Full plan and methodology: [`../launch/forgetting_report.md`](../launch/forgetting_report.md)

## What's measured

For each backend × scenario we record:

- **PASS** — the marker is gone from every store and every retrieval path.
- **FAIL** — a revoked/leaked marker still surfaces (the leak).
- **BLIND** — Ferryte could not verify (surfaced honestly, never hidden).

The **Forgetting Score** per backend = % of scenarios cleanly passed.

## Why a summarization layer is part of the test

Raw vector stores (pgvector / Chroma / Qdrant) do **not** leak on their own — a row
delete cleanly removes the embedding. The leak appears when an **LLM summarization
layer** sits on top (per-tenant summaries, derived memory), which is exactly what
real agent-memory frameworks do internally. So the benchmark runs a realistic
multi-tenant *summary memory* over each raw store and tests whether deleting the
source also clears the derived summary. Frameworks with built-in derived memory
(Mem0, Zep, AgentCore) are tested through their own delete APIs.

## Prerequisites

- Python 3.10+ and `pip install -r requirements.txt`
- An `OPENAI_API_KEY` in `.env` (copy from `.env.example`)
- Docker (for pgvector / Qdrant / Chroma) — see the setup guide
- (Optional) AWS Bedrock + AgentCore access for the AgentCore backend

## Quick start

```bash
cp .env.example .env          # then edit .env with your real key
docker compose up -d          # start pgvector, qdrant, chroma
pip install -r requirements.txt
# harness entrypoint (in progress):
# python -m benchmark.run --backends pgvector,chroma,qdrant,mem0 --all-scenarios
docker compose down -v        # stop + wipe when done
```

## Backends (launch set)

| Backend | Runs via | Status |
|---|---|---|
| Mem0 | in-process | adapter exists |
| pgvector | docker-compose | building |
| Chroma | docker-compose (or embedded) | building |
| Qdrant | docker-compose (or local mode) | building |
| Zep | separate setup (TBD) | building |
| AWS Bedrock AgentCore | AWS account | building |

## Reproducibility note

Before the public launch: pin exact image digests in `docker-compose.yml`, pin exact
package versions in `requirements.txt`, and record each backend's exact config so
anyone can falsify the results.
