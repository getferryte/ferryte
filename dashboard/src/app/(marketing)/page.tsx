"use client";

import Link from "next/link";
import { motion } from "framer-motion";

import { CopyableCommand } from "@/components/CopyableCommand";
import { Terminal, type TerminalLine } from "@/components/Terminal";
import {
  Magnetic,
  Reveal,
  RevealOnScroll,
  Stagger,
  StaggerItem,
  WordReveal,
} from "@/components/motion/Motion";

const EASE = [0.22, 1, 0.36, 1] as const;

export default function Landing() {
  return (
    <main>
      <Hero />
      <Compatibility />
      <LeakProof />
      <Recognition />
      <HowItWorks />
      <Authority />
      <BuiltFor />
      <Ask />
    </main>
  );
}

/* ============================================================ HERO */

function Hero() {
  return (
    <section className="relative flex min-h-[calc(100vh-73px)] flex-col items-stretch justify-center px-8 sm:px-12 lg:px-20">
      <div className="mx-auto w-full max-w-6xl">
        <Reveal delay={0.1} className="mb-10 flex items-center gap-2.5">
          <span className="dot dot-royal dot-live" />
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
            For teams running stateful AI agents
          </span>
        </Reveal>

        <WordReveal
          as="h1"
          text="Your agent got it wrong."
          delay={0.28}
          staggerDelay={0.07}
          className="font-display block max-w-[18ch] text-[56px] font-light leading-[0.98] tracking-tightest text-ink sm:text-[92px] lg:text-[120px]"
        />
        <WordReveal
          as="h1"
          text="See which memory did it."
          delay={0.92}
          staggerDelay={0.07}
          className="font-display -mt-1 block max-w-[18ch] text-[56px] font-light leading-[0.98] tracking-tightest text-royal sm:text-[92px] lg:text-[120px]"
        />

        <Reveal delay={1.65} className="mt-10 max-w-xl">
          <p className="text-lede text-ink-2 sm:text-[20px]">
            One line to instrument. Ferryte traces any wrong answer back to the
            memory that caused it — where it came from, what it touched, and
            proves your fix stuck.
          </p>
        </Reveal>

        <Reveal
          delay={1.9}
          className="mt-10 flex flex-wrap items-center gap-4"
        >
          <Magnetic>
            <a
              href="#leak"
              className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2"
            >
              See it in 30s
              <span aria-hidden>↓</span>
            </a>
          </Magnetic>
          <CopyableCommand command="pip install ferryte" />
          <Link
            href="https://github.com/getferryte/ferryte"
            className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
          >
            GitHub →
          </Link>
        </Reveal>
      </div>

      <Reveal
        delay={2.4}
        duration={1.2}
        className="absolute bottom-10 left-1/2 -translate-x-1/2"
      >
        <ScrollCue />
      </Reveal>
    </section>
  );
}

function ScrollCue() {
  return (
    <motion.div
      animate={{ y: [0, 6, 0] }}
      transition={{ duration: 2, ease: EASE, repeat: Infinity }}
      className="flex flex-col items-center gap-2 text-ink-3"
    >
      <span className="font-mono text-[10px] uppercase tracking-[0.22em]">
        See the trace
      </span>
      <svg
        width="14"
        height="22"
        viewBox="0 0 14 22"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect
          x="0.5"
          y="0.5"
          width="13"
          height="21"
          rx="6.5"
          stroke="currentColor"
        />
        <motion.circle
          cx="7"
          cy="7"
          r="1.5"
          fill="currentColor"
          animate={{ cy: [7, 14, 7] }}
          transition={{ duration: 2, ease: EASE, repeat: Infinity }}
        />
      </svg>
    </motion.div>
  );
}

/* =================================================== COMPATIBILITY */

function Compatibility() {
  const items: Array<{ name: string; status: "stable" | "beta" | "planned" }> = [
    { name: "pgvector / Chroma / Qdrant", status: "stable" },
    { name: "AWS AgentCore", status: "beta" },
    { name: "Zep", status: "beta" },
    { name: "Letta", status: "beta" },
    { name: "Cloudflare Agents", status: "beta" },
    { name: "Mem0", status: "stable" },
    { name: "LangGraph", status: "planned" },
  ];
  const tone = {
    stable: "text-ink-2",
    beta: "text-ink-3",
    planned: "text-ink-3/70",
  } as const;
  return (
    <section className="border-t border-rule/40 px-8 py-7 sm:px-12 lg:px-20">
      <RevealOnScroll>
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-8 gap-y-3 text-caption">
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
            Adapters
          </span>
          {items.map((it) => (
            <span key={it.name} className={`flex items-center gap-2 ${tone[it.status]}`}>
              <span>{it.name}</span>
              {it.status !== "stable" && (
                <span className="font-mono text-[9.5px] uppercase tracking-[0.18em] text-ink-3/80">
                  · {it.status}
                </span>
              )}
            </span>
          ))}
        </div>
      </RevealOnScroll>
    </section>
  );
}

/* ==================================================== LEAK PROOF */

const LEAK_BAD: TerminalLine[] = [
  { kind: "command", text: 'agent.ask("acme", "what plan is this customer on?")' },
  { kind: "output", text: "You're on the Legacy Free plan.", tone: "issue" },
  { kind: "spacer" },
  { kind: "output", text: "# wrong — they upgraded to Pro last week.", tone: "muted" },
  { kind: "output", text: "# the old fact is still in memory. where?", tone: "muted" },
  { kind: "output", text: "# 4 hours grepping traces later…", tone: "muted" },
];

const LEAK_GOOD: TerminalLine[] = [
  { kind: "command", text: 'ferryte why "Legacy Free plan" --replay' },
  {
    kind: "output",
    text: "caused by 3 candidate memories · top conf 1.00",
    tone: "brand",
  },
  { kind: "spacer" },
  { kind: "output", text: "#1  stale belief · conf 1.00", tone: "issue" },
  { kind: "output", text: "  Customer acme is on the Legacy Free plan." },
  { kind: "output", text: "  from 'zendesk-ticket-8821'" },
  { kind: "output", text: "  recorded in context for this answer" },
  { kind: "output", text: '  shared span: "legacy free plan"' },
  { kind: "output", text: "  superseded by billing-sync-0601" },
  { kind: "spacer" },
  { kind: "output", text: "counterfactual replay: without it → Pro plan", tone: "brand" },
];

function LeakProof() {
  return (
    <section
      id="leak"
      className="border-t border-rule/70 px-8 py-32 sm:px-12 lg:px-20 lg:py-40"
    >
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-royal">
            The four-hour bug, in thirty seconds
          </span>
        </RevealOnScroll>

        <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
          <h2 className="font-display text-[36px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[56px] lg:text-[64px]">
            The agent gave a wrong answer.
            <br />
            <span className="text-ink-3">Now find the memory that caused it.</span>
          </h2>
        </RevealOnScroll>

        <RevealOnScroll delay={0.25} className="mt-14 grid gap-5 lg:grid-cols-2">
          <Terminal
            tone="bad"
            title="Without Ferryte"
            tag="grep the traces"
            lines={LEAK_BAD}
          />
          <Terminal
            tone="good"
            title="With Ferryte"
            tag="root cause"
            lines={LEAK_GOOD}
          />
        </RevealOnScroll>

        <RevealOnScroll delay={0.4} className="mt-8 max-w-3xl">
          <p className="text-body text-ink-2">
            Memory bugs are invisible by default — even the platforms admit it.
            We reproduced one <span className="text-ink">live on AWS Bedrock AgentCore</span>:
            delete the source, the derived memory still answers.{" "}
            <span className="text-ink">Deletion is just one of the ways memory
            misbehaves</span> — stale facts, cross-tenant bleed, and poisoned
            writes are the rest. The honest, reproducible evidence is in{" "}
            <Link href="/benchmark" className="text-royal underline-offset-4 hover:underline">
              The Memory Report
            </Link>
            .
          </p>
        </RevealOnScroll>
      </div>
    </section>
  );
}

/* ===================================================== RECOGNITION */

const SCENARIOS = [
  "Your agent answered from a fact the customer corrected last week.",
  "Tenant A's chat surfaced something only Tenant B ever told the agent.",
  "A user asked to be forgotten. The agent still brings them up.",
];

function Recognition() {
  return (
    <section className="border-t border-rule/70 px-8 py-32 sm:px-12 lg:px-20 lg:py-40">
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
            If any of these landed
          </span>
        </RevealOnScroll>

        <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
          <h2 className="font-display text-[36px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[56px] lg:text-[64px]">
            You&rsquo;ve already had this incident.
            <br />
            <span className="text-ink-3">
              You just haven&rsquo;t seen the ticket yet.
            </span>
          </h2>
        </RevealOnScroll>

        <Stagger className="mt-14 flex flex-col gap-4" staggerDelay={0.1}>
          {SCENARIOS.map((s) => (
            <StaggerItem key={s}>
              <article className="group flex items-center gap-5 rounded-lg border border-rule bg-surface px-7 py-6 transition-colors duration-base ease-out hover:border-royal/40">
                <span
                  className="dot dot-royal shrink-0 transition-transform duration-base ease-out group-hover:scale-110"
                  aria-hidden
                />
                <h3 className="font-display text-[20px] font-light leading-[1.32] tracking-[-0.015em] text-ink sm:text-[24px]">
                  {s}
                </h3>
              </article>
            </StaggerItem>
          ))}
        </Stagger>
      </div>
    </section>
  );
}

/* ===================================================== HOW IT WORKS */

const STEPS = [
  {
    num: "01",
    title: "Instrument",
    body: "One line. Auto-patches your memory client — no agent code changes.",
    code: `import ferryte
ferryte.instrument()`,
  },
  {
    num: "02",
    title: "Trace",
    body: "Every memory carries its lineage — source, derivation, retrieval.",
    code: `mem_3f9c
  ← zendesk-ticket-8821
  → summary_v2 → retrieval`,
  },
  {
    num: "03",
    title: "Explain",
    body: "Point at a bad answer. Get the memory that caused it, ranked.",
    code: `$ ferryte why "Legacy Free plan"
#1 stale belief · conf 0.82
retrieved into context`,
  },
];

function HowItWorks() {
  return (
    <section className="border-t border-rule/70 px-8 py-32 sm:px-12 lg:px-20 lg:py-40">
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
            How it works
          </span>
        </RevealOnScroll>

        <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
          <h2 className="font-display text-[36px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[56px] lg:text-[64px]">
            One line in.
            <br />
            <span className="text-ink-3">A root cause out.</span>
          </h2>
        </RevealOnScroll>

        <Stagger className="mt-14 grid gap-10 md:grid-cols-3" staggerDelay={0.1}>
          {STEPS.map((s) => (
            <StaggerItem key={s.num}>
              <article>
                <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-royal">
                  Step {s.num}
                </div>
                <h3 className="mt-4 font-display text-[24px] font-light leading-[1.18] tracking-[-0.02em] text-ink sm:text-[28px]">
                  {s.title}
                </h3>
                <p className="mt-3 text-caption text-ink-3">{s.body}</p>
                <pre className="mt-5 overflow-x-auto rounded-md border border-rule bg-surface p-4 font-mono text-[12.5px] leading-[1.6] text-ink-2">
                  <code>{s.code}</code>
                </pre>
              </article>
            </StaggerItem>
          ))}
        </Stagger>

        <RevealOnScroll delay={0.35} className="mt-12">
          <Link
            href="/product"
            className="inline-flex items-center gap-1.5 text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
          >
            See the full pipeline
            <span aria-hidden>→</span>
          </Link>
        </RevealOnScroll>
      </div>
    </section>
  );
}

/* ======================================================= AUTHORITY */

const QUOTES = [
  {
    vendor: "AWS Bedrock AgentCore",
    line: "Deleting an event doesn’t remove the structured information derived out of it from the long term memory.",
    href: "https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/short-term-delete-event.html",
  },
  {
    vendor: "Zep documentation",
    line: "Deleting an episode does not regenerate the names or summaries of nodes shared with other episodes.",
    href: "https://help.getzep.com/deleting-data-from-the-graph",
  },
  {
    vendor: "OWASP Top 10 for Agentic AI · ASI06:2026",
    line: "Adversaries corrupt or seed this context with malicious or misleading data, causing future reasoning, planning, or tool use to become biased, unsafe, or aid exfiltration.",
    href: "https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/",
  },
];

function Authority() {
  return (
    <section className="border-t border-rule/70 px-8 py-32 sm:px-12 lg:px-20 lg:py-40">
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
            You&rsquo;re not paranoid
          </span>
        </RevealOnScroll>

        <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
          <h2 className="font-display text-[36px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[56px] lg:text-[64px]">
            The platform vendors said it themselves.
          </h2>
        </RevealOnScroll>

        <Stagger
          className="mt-12 grid gap-4 sm:grid-cols-3"
          staggerDelay={0.1}
        >
          {QUOTES.map((q) => (
            <StaggerItem key={q.vendor}>
              <article className="flex h-full flex-col rounded-lg border border-rule bg-surface p-7 transition-colors duration-base ease-out hover:border-rule-2">
                <p className="font-display text-[19px] font-light leading-[1.38] tracking-[-0.012em] text-ink sm:text-[21px]">
                  &ldquo;{q.line}&rdquo;
                </p>
                <a
                  href={q.href}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-auto pt-6 font-mono text-[10.5px] uppercase tracking-[0.18em] text-ink-3 transition-colors duration-fast ease-out hover:text-ink-2"
                >
                  — {q.vendor} ↗
                </a>
              </article>
            </StaggerItem>
          ))}
        </Stagger>

        <RevealOnScroll delay={0.35} className="mt-10">
          <Link
            href="/manifesto"
            className="inline-flex items-center gap-1.5 text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
          >
            Read the full case
            <span aria-hidden>→</span>
          </Link>
        </RevealOnScroll>
      </div>
    </section>
  );
}

/* ======================================================= BUILT FOR */

const PERSONAS = [
  {
    tag: "engineering",
    title: "The lead who owns the agent.",
    body: "Stop grepping traces at midnight. One command to the memory that caused it.",
  },
  {
    tag: "support & ops",
    title: "The team fielding “the AI is confused about me.”",
    body: "See exactly what the agent remembers about a user — and correct it.",
  },
  {
    tag: "compliance",
    title: "The team that signs the receipt.",
    body: "Prove a deleted memory — and everything derived from it — is really gone.",
  },
];

function BuiltFor() {
  return (
    <section className="border-t border-rule/70 px-8 py-32 sm:px-12 lg:px-20 lg:py-40">
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
            Built for
          </span>
        </RevealOnScroll>

        <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
          <h2 className="font-display text-[36px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[56px] lg:text-[64px]">
            Three teams.
            <br />
            <span className="text-ink-3">One view of the memory.</span>
          </h2>
        </RevealOnScroll>

        <Stagger className="mt-14 grid gap-12 md:grid-cols-3" staggerDelay={0.1}>
          {PERSONAS.map((p) => (
            <StaggerItem key={p.tag}>
              <article className="border-l-2 border-rule pl-6 transition-colors duration-base ease-out hover:border-royal">
                <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-royal">
                  {p.tag}
                </span>
                <h3 className="mt-4 font-display text-[22px] font-light leading-[1.22] tracking-[-0.016em] text-ink sm:text-[26px]">
                  {p.title}
                </h3>
                <p className="mt-4 text-body text-ink-2">{p.body}</p>
              </article>
            </StaggerItem>
          ))}
        </Stagger>
      </div>
    </section>
  );
}

/* ============================================================ ASK */

function Ask() {
  return (
    <section className="brand-hairline relative border-t border-rule/70 px-8 py-32 sm:px-12 lg:px-20 lg:py-44">
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-royal">
            Five seats · paired with the founder · six months of Cloud free
          </span>
        </RevealOnScroll>

        <RevealOnScroll delay={0.1} className="mt-8 max-w-5xl">
          <h2 className="font-display text-[40px] font-light leading-[1.04] tracking-[-0.03em] text-ink sm:text-[64px] lg:text-[80px]">
            Be the team that
            <br />
            <span className="text-ink-3">stopped debugging blind.</span>
          </h2>
        </RevealOnScroll>

        <RevealOnScroll delay={0.25} className="mt-10 max-w-xl">
          <p className="text-lede text-ink-2">
            Five teams running stateful agents in production. Paired with the
            founding engineer for the first integration. You shape the roadmap.
          </p>
        </RevealOnScroll>

        <RevealOnScroll
          delay={0.4}
          className="mt-10 flex flex-wrap items-center gap-4"
        >
          <Magnetic>
            <a
              href="mailto:hello@ferryte.dev?subject=Ferryte%20design%20partner&body=Stack%3A%20%0ATenants%3A%20%0AMemory%20backend(s)%3A%20%0AMemory%20bug%20you%E2%80%99re%20fighting%3A%20"
              className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2"
            >
              Email hello@ferryte.dev
              <span aria-hidden>→</span>
            </a>
          </Magnetic>
          <Link
            href="/pricing"
            className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
          >
            See Core, Cloud, Enterprise →
          </Link>
          <a
            href="#leak"
            className="text-[14px] text-ink-3 transition-colors duration-fast ease-out hover:text-ink-2"
          >
            Or watch the trace again ↑
          </a>
        </RevealOnScroll>
      </div>
    </section>
  );
}
