"use client";

import Link from "next/link";

import {
  Magnetic,
  Reveal,
  RevealOnScroll,
  Stagger,
  StaggerItem,
} from "@/components/motion/Motion";

export default function ManifestoPage() {
  return (
    <main className="px-8 sm:px-12 lg:px-20">
      <div className="mx-auto max-w-4xl">
        <Header />
        <Lede />
        <Quotes />
        <Synthesis />
        <Buyers />
        <Close />
      </div>
    </main>
  );
}

/* ---------------------------------------------------------- Header */

function Header() {
  return (
    <section className="pt-28 pb-12 sm:pt-36 sm:pb-16">
      <Reveal delay={0.05}>
        <div className="flex items-center gap-2.5">
          <span className="dot dot-royal dot-live" />
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
            Manifesto · v1
          </span>
        </div>
      </Reveal>

      <Reveal delay={0.18} className="mt-10">
        <h1 className="font-display text-[44px] font-light leading-[1.02] tracking-[-0.04em] text-ink sm:text-[72px] lg:text-[88px]">
          Your AI deleted the data.
          <br />
          <span className="text-ink-3">The derived memories didn’t.</span>
        </h1>
      </Reveal>

      <Reveal delay={0.4} className="mt-8 flex items-center gap-3 text-caption text-ink-3">
        <span>Pranav Chahal</span>
        <span aria-hidden>·</span>
        <span>Founder, Ferryte</span>
        <span aria-hidden>·</span>
        <span>4 min read</span>
      </Reveal>
    </section>
  );
}

/* ---------------------------------------------------------- Lede */

function Lede() {
  return (
    <section className="border-t border-rule/60 py-16">
      <RevealOnScroll>
        <p className="text-[22px] font-light leading-[1.5] tracking-[-0.014em] text-ink sm:text-[24px]">
          Modern AI agents do not just hold the data you gave them. They hold every
          summary, every embedding, every per-tenant fact they distilled from it.
          When you delete the original, those derivations stay behind — and the next
          retrieval brings them right back to the prompt.
        </p>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8">
        <p className="text-body text-ink-2">
          We do not know this because we are guessing. We know it because the
          platforms themselves say so, in their own documentation, in 2025. Three
          different vendors, three different products, the same admission.
        </p>
      </RevealOnScroll>
    </section>
  );
}

/* --------------------------------------------------------- Quotes */

const ADMISSIONS = [
  {
    source: "AWS Bedrock AgentCore",
    quote:
      "Deleting an event doesn’t remove the structured information derived out of it from the long term memory.",
    href: "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/short-term-delete-event.html",
    note: "Translation: rows go, summaries stay.",
  },
  {
    source: "Zep documentation",
    quote:
      "Deleting an episode does not regenerate the names or summaries of nodes shared with other episodes.",
    href: "https://help.getzep.com/deleting-data-from-the-graph",
    note: "Translation: revocation does not propagate through the graph.",
  },
  {
    source: "OWASP Top 10 for Agentic AI · ASI06:2026 (Dec 9, 2025)",
    quote:
      "Adversaries corrupt or seed this context with malicious or misleading data, causing future reasoning, planning, or tool use to become biased, unsafe, or aid exfiltration.",
    href: "https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/",
    note: "Translation: the industry standard already names this risk.",
  },
];

function Quotes() {
  return (
    <section className="border-t border-rule/60 py-20">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          The platform vendors said it themselves
        </span>
      </RevealOnScroll>

      <Stagger className="mt-12 flex flex-col gap-12" staggerDelay={0.14}>
        {ADMISSIONS.map((a) => (
          <StaggerItem key={a.source}>
            <blockquote className="border-l-2 border-royal pl-6">
              <p className="font-display text-[26px] font-light leading-[1.32] tracking-[-0.022em] text-ink sm:text-[32px]">
                “{a.quote}”
              </p>
              <footer className="mt-5 flex flex-col gap-1">
                <a
                  href={a.href}
                  target="_blank"
                  rel="noreferrer"
                  className="font-mono text-[11px] not-italic uppercase tracking-[0.18em] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
                >
                  — {a.source} ↗
                </a>
                <span className="text-caption text-ink-3">{a.note}</span>
              </footer>
            </blockquote>
          </StaggerItem>
        ))}
      </Stagger>
    </section>
  );
}

/* ---------------------------------------------------- Synthesis */

function Synthesis() {
  return (
    <section className="border-t border-rule/60 py-20">
      <RevealOnScroll>
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          What this means in production
        </h2>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-10 grid gap-5 text-body text-ink-2">
        <p>
          You ship a tool that lets a tenant revoke a document, or a customer hits
          the right-to-be-forgotten button, or a stale fact is supposed to be
          overwritten. Your delete API returns success. The row is gone.
        </p>
        <p>
          Then your agent answers a question. The answer is sourced from a summary
          that was generated weeks ago. The summary absorbed a marker from the
          deleted document. The model has no idea anything was supposed to be
          forgotten. Neither does your test suite, because all your test suite
          checked was whether the row was missing.
        </p>
        <p className="text-ink">
          The leak is not the model hallucinating. The leak is the model
          faithfully retrieving from a derivation that nobody knew existed.
        </p>
        <p>
          Almost nobody tests for this in CI. The cost is exclusively borne at
          incident time — a confused customer, a screenshot in a Slack thread, an
          appsec ticket, a privacy regulator email.
        </p>
      </RevealOnScroll>
    </section>
  );
}

/* ------------------------------------------------------ Buyers */

const BUYERS = [
  {
    tag: "engineering",
    title: "The lead who owns the agent.",
    body: "Drop `ferryte test` into CI. The build breaks the moment a revoked source re-enters retrieval. Catch the leak in pre-prod, not in a Slack thread on Sunday.",
  },
  {
    tag: "appsec",
    title: "The reviewer who unblocks the deal.",
    body: "Replace \u201cwe delete the row, trust us\u201d with a regenerated forgetting-test report, an explicit blind-spot map, and a coverage number. Security review goes from weeks to days.",
  },
  {
    tag: "compliance",
    title: "The team that signs the receipt.",
    body: "GDPR and CCPA right-to-be-forgotten don\u2019t end at the row. Ferryte gives you transitive deletion evidence across raw stores, summaries, embeddings, and retrievals — and (in Enterprise) signed attestations.",
  },
];

function Buyers() {
  return (
    <section className="border-t border-rule/60 py-20">
      <RevealOnScroll>
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          Three buyers. One artifact.
        </h2>
      </RevealOnScroll>

      <Stagger className="mt-12 flex flex-col gap-10" staggerDelay={0.1}>
        {BUYERS.map((b) => (
          <StaggerItem key={b.tag}>
            <article className="grid gap-2 border-l-2 border-rule pl-6 transition-colors duration-base ease-out hover:border-royal">
              <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-royal">
                {b.tag}
              </span>
              <h3 className="font-display text-[24px] font-light leading-[1.18] tracking-[-0.02em] text-ink sm:text-[28px]">
                {b.title}
              </h3>
              <p className="mt-1 text-body text-ink-2">{b.body}</p>
            </article>
          </StaggerItem>
        ))}
      </Stagger>
    </section>
  );
}

/* ------------------------------------------------------ Close */

function Close() {
  return (
    <section className="border-t border-rule/60 py-24">
      <RevealOnScroll>
        <h2 className="font-display text-[36px] font-light leading-[1.04] tracking-[-0.03em] text-ink sm:text-[52px]">
          Verification is not a feature.
          <br />
          <span className="text-ink-3">It’s the difference between trust and a press release.</span>
        </h2>
      </RevealOnScroll>

      <RevealOnScroll delay={0.15} className="mt-10 flex flex-wrap items-center gap-4">
        <Magnetic>
          <Link
            href="/product"
            className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2"
          >
            See how it works
            <span aria-hidden>→</span>
          </Link>
        </Magnetic>
        <Link
          href="/pricing"
          className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
        >
          Pricing breakdown →
        </Link>
        <a
          href="https://github.com/getferryte/ferryte"
          className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
        >
          GitHub →
        </a>
      </RevealOnScroll>
    </section>
  );
}
