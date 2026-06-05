# Brand kit

Everything you need to launch the Ferryte X / GitHub / LinkedIn presence
without firing up a design tool.

## Files

| File | Use |
|---|---|
| `wordmark-light.svg` | Wordmark on dark backgrounds (X bio header, dark slide decks). |
| `wordmark-dark.svg` | Wordmark on light backgrounds (white site sections, light decks). |
| `avatar.svg` | Profile picture for X / GitHub / LinkedIn. 400 × 400, OG-safe. |
| `x-banner.svg` | Full X header. 1500 × 500. Drop directly into X's banner upload. |

## Tokens

| Role | Hex | Notes |
|---|---|---|
| Canvas | `#000000` | Always pure black. Never a tint. |
| Ink (primary text) | `#fafafa` | Cool off-white. |
| Ink-2 (secondary) | `#a0a0a0` | For supporting copy. |
| Ink-3 (tertiary) | `#666666` | For labels and meta. |
| Royal (accent) | `#2563eb` | One accent, used sparingly. |

## Typography

- Display + body: **Geist Sans** (Vercel; free via Google Fonts / `next/font`).
- Mono / numerals: **Geist Mono**.
- Display weights: 300 (light) at 56px+, 500 (medium) at 22–32px.
- Always tight tracking on display sizes: -0.028em to -0.045em.

## How to convert SVG → PNG

X requires PNGs for avatar + banner uploads. Quickest path:

```bash
# Install librsvg (one-time):
brew install librsvg

# Avatar (X requires 400x400 minimum, 4000x4000 maximum):
rsvg-convert -w 1000 -h 1000 brand/avatar.svg -o brand/avatar.png

# Banner (X expects 1500x500):
rsvg-convert -w 1500 -h 500 brand/x-banner.svg -o brand/x-banner.png
```

Or open the SVGs in Figma / Sketch / browser, screenshot, done.

## Voice (for any future copy)

- **Declarative, not promotional.** "Forgetting failed." not "We make forgetting better!"
- **Quote the platform vendors against themselves.** AWS, Zep, OWASP did the
  hard work of admitting the problem — let them sell it.
- **Mono is for facts.** When you state a number, command, or technical term,
  set it in mono.
- **No emoji.** Anywhere. The brand is calm.

## X bio variants

Pick one based on field length:

- **80 chars:** `Verification for agent forgetting. Source-available. BSL 1.1.`
- **120 chars:** `Source-available forgetting oracle for AI agents. We prove your delete actually deleted. BSL 1.1. Cloud + Enterprise coming.`
- **160 chars (max):** `Source-available forgetting oracle for AI agents. We prove your delete actually deleted — across memory, summaries, embeddings, retrievals. BSL 1.1. Cloud soon.`

## One-liners (for press / one-pagers / cold emails)

- 8 words: **Verification for agent forgetting.**
- 15 words: **We prove your AI agent stops acting on revoked, stale, or cross-tenant data.**
- 25 words: **Ferryte is the source-available forgetting oracle for AI agents — one line, and your CI breaks the moment a revoked memory still influences output.**
- 50 words: **Ferryte is the source-available forgetting oracle for AI agents. One line — `ferryte.instrument()` — and your memory layer is wired to a canary-based verification engine that plants markers, calls the real delete API, and inspects both store contents and retrieval traces. CI breaks on leak. Cloud and Enterprise tiers handle scale.**
