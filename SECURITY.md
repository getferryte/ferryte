# Security policy

Ferryte is a security tool. We take vulnerability reports seriously and we
expect every reporter to be treated as a partner, not an adversary.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for a security vulnerability.
Instead, use one of:

1. **GitHub Security Advisories** — preferred. Open a private advisory at
   <https://github.com/getferryte/ferryte/security/advisories/new>.
2. **Email** — `hello@ferryte.dev`. Encrypt with our PGP key if the
   disclosure is sensitive (key fingerprint published at ferryte.dev/.well-known
   once we ship it).

Please include:

- A description of the issue.
- Steps to reproduce, or a proof-of-concept.
- The version of Ferryte (and any adapter) affected.
- Your assessment of impact.
- Whether you wish to be credited in the advisory.

## What to expect

- **Acknowledgement within 48 hours** of receipt.
- **Initial assessment within 5 business days.**
- **Coordinated disclosure timeline** agreed before any public discussion.
  We default to 90 days from acknowledgement, sooner if a fix lands faster,
  longer only with reporter consent.
- **Credit** in the GitHub advisory and the CHANGELOG, unless you ask
  otherwise.

## Scope

This policy covers:

- The `ferryte` Python package.
- The Ferryte CLI.
- The local Next.js dashboard and FastAPI API surface.
- The shipped adapters (`mem0`, `vector`).

This policy does **not** cover:

- Vulnerabilities in third-party memory backends (Mem0, Zep, AWS AgentCore).
  Please report those upstream; we are happy to relay.
- Vulnerabilities in Ferryte Cloud or Enterprise. Those have their own
  disclosure channels — see your commercial agreement.

## Safe-harbour

If you act in good faith, follow this policy, and avoid privacy violations,
service disruption, or data destruction, we will not pursue legal action and
will work with you on remediation.
