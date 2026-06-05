# ProductHunt launch copy

**Schedule for:** the day after the X thread, midnight Pacific (PH days
start at 00:01 PT).

**Hunter:** ideally a friendly with a verified maker badge. If you don't have
one, self-launch is fine for v0.

---

## Name

Ferryte

## Tagline (≤ 60 chars)

> The forgetting oracle for AI agents. Source-available.

## Description (≤ 260 chars)

> Verify your AI agent actually forgot deleted data. Plant canary memories,
> call the real delete API, inspect store contents AND retrieval traces.
> CI breaks on leak. Source-available (BSL 1.1). Built for multi-tenant memory.

## First comment (post immediately as the maker, sets the tone)

Hey everyone — making this because every major agent-memory vendor (AWS
Bedrock AgentCore, Zep, Mem0) ships with a documented caveat: deleting a
record doesn't always remove the summaries, embeddings, or rollups that
absorbed it. Multi-tenant AI products keep leaking deleted data and finding
out from customers.

Ferryte is the source-available layer that proves whether forgetting actually
happened.

- **One line install:** `ferryte.instrument()` auto-patches detected memory
  clients. No SDK migration, no agent code changes.
- **One command verify:** `ferryte test` plants canaries, calls the real
  delete API, inspects store contents AND retrieval traces, fails CI on a
  surviving marker.
- **Honest:** every report has a blind-spot section listing what we
  couldn't see. A passing test means something.

Source-available engine ships today (BSL 1.1, converts to Apache 2.0 after
three years): four scenarios, CLI gate, JSON + HTML reports, local
dashboard. Hosted Cloud is being built **with** the first five design
partners — it doesn't exist yet. Enterprise (SSO, compliance attestations,
premium adapters, runtime enforcement) is on the roadmap after Cloud.

Looking for feedback on:

1. The scenarios you'd want next.
2. Whether the cross-system blind-spot framing reads as honest or as a
   cop-out.

Try the leak demo, zero API keys:

```
pip install ferryte
python demo/multi_tenant_leak.py
```

Code: github.com/getferryte/ferryte
Marketing: ferryte.dev
Design partners (first 5, six months of Cloud free when it ships, paired with the founder): hello@ferryte.dev

## Topics (pick 3, max)

- Developer Tools
- Artificial Intelligence
- Open Source

## Gallery assets

1. The 90-second screencast (same .mp4 as the X post).
2. Hero screenshot of ferryte.dev with "Forgetting failed." visible.
3. Hero screenshot of /app showing the failed scenarios + huge stat numbers.
4. Terminal screenshot of `ferryte test` with the FAIL output.
5. The before/after code-panel screenshot from the marketing site.

All at 1270 × 760 minimum.

## Maker checklist for launch day

- [ ] First comment posted within 5 minutes of go-live.
- [ ] Reply to every comment within an hour.
- [ ] Post the PH link to: company X account, your X account, LinkedIn, and
      the GitHub README.
- [ ] DM five friendlies asking for an honest upvote + comment if they like
      it. (PH bans vote-rings; ask for honesty, not loyalty.)
- [ ] Post a midday "we're #N" update tweet referencing back to the X thread.
