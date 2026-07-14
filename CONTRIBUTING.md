# Contributing to Ferryte

Ferryte is source-available under the Business Source License 1.1. The engine
in this repository accepts contributions; the closed-source Cloud and
Enterprise tiers do not. See [LICENSING.md](LICENSING.md) for the precise
boundary and the contributor license terms.

We deeply value contributions that make the source-available core more useful
to more teams. We also keep a tight bar on scope so the product stays sharp.

## What we eagerly accept

- **New adapters** for memory backends (Mem0 plugins, pgvector dialects,
  Chroma, Pinecone, in-process stores). New adapters are the single highest-
  leverage contribution path.
- **New scenarios** for forgetting properties we don't yet cover. Open an
  issue first so we can discuss whether it belongs in Core or as a plugin.
- **Bug fixes** with an accompanying test.
- **Docs improvements** — typos, clarifications, missing edge cases.
- **Better blind-spot detection** — anywhere Ferryte should be honest about
  what it cannot prove but currently isn't.
- **Performance** — particularly around the lineage graph at scale.

## What we politely decline

- Features that turn Ferryte into a generic AI-security tool. We are
  deliberately narrow: forgetting verification. Generic prompt or runtime
  threat detection belongs in other products.
- Premium-adapter implementations (AgentCore, Zep, GovCloud). These are
  Enterprise-scoped — see COMMERCIAL.md.
- Runtime retrieval enforcement. Latency-sensitive, intentionally not in OSS
  core — see LICENSING.md.

## Dev setup

```bash
git clone https://github.com/getferryte/ferryte
cd ferryte

python -m venv .venv
source .venv/bin/activate

pip install -e ".[dev,api]"

pytest -q
ruff check src tests
```

The Next.js dashboard:

```bash
cd dashboard
npm install
npm run dev
```

## Workflow

1. Open an issue first for anything non-trivial. We've politely closed PRs
   we wished had been a discussion.
2. Branch off `main`. Conventional commit messages are nice but not required.
3. Add tests. We won't merge an adapter or scenario without one.
4. Run `pytest -q` and `ruff check src tests`.
5. Open the PR with the template filled in.

We aim to review PRs within three business days. If we're slower than that,
ping the PR — sometimes notifications fall on the floor.

## Contributor license

By contributing, you grant Ferryte the dual-license terms described in
[LICENSING.md § Contributor License Agreement](LICENSING.md). This is the
standard BSL pattern: contributions flow into the source-available core (BSL
1.1, converting to Apache 2.0) *and* may be incorporated into the
closed-source Cloud / Enterprise tiers. We do not ask this lightly — it is the
structural prerequisite for the company to fund full-time work on the core.

If you cannot accept these terms, please do not submit contributions.

## Code of conduct

By participating, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).
We do not have a lot of patience for rude behaviour toward maintainers or
other contributors. Be the kind of person you would want to ship code with.

## Talk to us

- **Discussions:** GitHub Discussions tab
- **Bug reports:** issue template
- **Design-partner applications / commercial questions:** pranav@ferryte.dev
- **Security disclosures:** see [SECURITY.md](SECURITY.md)
