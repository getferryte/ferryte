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
          Your agent remembers everything.
          <br />
          <span className="text-ink-3">You can see almost none of it.</span>
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
          Modern AI agents do not just store what you tell them. They distill it —
          into summaries, embeddings, graph nodes, per-user facts — and answer from
          those derivations weeks later. So when the agent gets something wrong, the
          cause is buried in a memory nobody can see, derived from a source nobody
          remembers writing.
        </p>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8">
        <p className="text-body text-ink-2">
          This is not a guess. The platforms themselves document it — that deleting
          a source leaves its derived memory behind, that revocation does not
          propagate, that poisoned context survives. Three different vendors, three
          different products, the same admission: memory misbehaves, and it does so
          invisibly.
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
          A customer corrects a fact. A tenant churns. A user asks to be forgotten.
          Your app does the obvious thing — updates the record, calls delete, moves
          on. The primary row is handled.
        </p>
        <p>
          Then your agent answers a question, and the answer is sourced from a
          summary generated weeks ago that absorbed the old fact. The model isn&rsquo;t
          hallucinating — it is faithfully retrieving from a derivation nobody knew
          existed. And when it&rsquo;s wrong, the person on call opens the logs and
          starts reading: no map from the bad answer to the memory behind it, no
          record of where that memory came from, no way to know what else it touched.
        </p>
        <p className="text-ink">
          The bug is not the model. The bug is that agent memory is a black box —
          you can see what it said, never why it believed it.
        </p>
        <p>
          Almost nobody can trace this. The cost is borne at incident time — a
          confused customer, a screenshot in a Slack thread, a support ticket, a
          privacy email — and the fix is hours of grepping traces and hoping you
          deleted the right thing.
        </p>
        <p className="text-ink">
          So we stopped guessing and started tracing. We reproduced one class of
          this live on AWS Bedrock AgentCore — delete the source, the derived records
          still answer. Deletion is only one way memory misbehaves; stale facts,
          cross-tenant bleed, and poisoned writes are the rest. All of them live in the <span className="text-ink">derived
          layer</span> an app composes on top. The honest, reproducible evidence is{" "}
          <Link href="/benchmark" className="text-royal underline-offset-4 hover:underline">
            The Memory Report
          </Link>
          .
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
    body: "Run `ferryte why` on the bad answer instead of grepping traces until midnight. Get the memory that caused it, its full lineage, and a one-command fix — in minutes.",
  },
  {
    tag: "support & ops",
    title: "The team fielding \u201cthe AI is confused about me.\u201d",
    body: "Open the customer\u2019s memory timeline and see exactly what the agent believes about them and where each belief came from — then correct the one that\u2019s wrong, without wiping the rest.",
  },
  {
    tag: "compliance",
    title: "The team that signs the receipt.",
    body: "GDPR and CCPA right-to-be-forgotten don\u2019t end at the row. Ferryte proves a deleted memory \u2014 and everything derived from it \u2014 is gone across raw stores, summaries, embeddings, and retrievals, and (in Enterprise) signs the attestation.",
  },
];

function Buyers() {
  return (
    <section className="border-t border-rule/60 py-20">
      <RevealOnScroll>
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          Three teams. One view of the memory.
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
          A memory you can’t explain
          <br />
          <span className="text-ink-3">is a memory you can’t trust.</span>
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
          href="/audit"
          className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
        >
          Book the $500 audit →
        </Link>
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
