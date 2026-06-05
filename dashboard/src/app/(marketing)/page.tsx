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
            For teams shipping multi-tenant AI agents
          </span>
        </Reveal>

        <WordReveal
          as="h1"
          text="You deleted the data."
          delay={0.28}
          staggerDelay={0.07}
          className="font-display block max-w-[18ch] text-[56px] font-light leading-[0.98] tracking-tightest text-ink sm:text-[92px] lg:text-[120px]"
        />
        <WordReveal
          as="h1"
          text="Your agent kept it."
          delay={0.92}
          staggerDelay={0.07}
          className="font-display -mt-1 block max-w-[18ch] text-[56px] font-light leading-[0.98] tracking-tightest text-royal sm:text-[92px] lg:text-[120px]"
        />

        <Reveal delay={1.65} className="mt-10 max-w-xl">
          <p className="text-lede text-ink-2 sm:text-[20px]">
            Plants canaries. Calls your real delete API. Breaks CI when the
            leak survives.
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
              Watch it leak (30s)
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
        See it leak
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
    { name: "Mem0", status: "stable" },
    { name: "in-memory vector", status: "stable" },
    { name: "pgvector / Chroma / Qdrant via subclass", status: "stable" },
    { name: "Zep", status: "planned" },
    { name: "AWS AgentCore", status: "planned" },
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
  { kind: "command", text: 'store.delete_by_source("acme-doc-1")' },
  { kind: "output", text: "# returns 1 — primary record removed", tone: "muted" },
  { kind: "spacer" },
  { kind: "command", text: 'agent.ask("acme", "what is the launch code?")' },
  { kind: "output", text: "Based on what I remember:" },
  { kind: "output", text: "the launch code is ORION-DELTA-77.", tone: "issue" },
  { kind: "spacer" },
  { kind: "output", text: "# the per-tenant summary absorbed it.", tone: "muted" },
  { kind: "output", text: "# nothing flagged.", tone: "muted" },
];

const LEAK_GOOD: TerminalLine[] = [
  { kind: "command", text: "ferryte test --scenario source-revocation" },
  {
    kind: "output",
    text: "source-revocation       FAIL    3 findings",
    tone: "issue",
  },
  { kind: "spacer" },
  { kind: "output", text: "FAIL revoked_marker_in_probe", tone: "issue" },
  { kind: "output", text: "  Revoked source 'acme-doc-1' still surfaces" },
  { kind: "output", text: "  marker 'ORION-DELTA-77' via retrieval on" },
  { kind: "output", text: "  tenant 'acme' (kind=summary, id=27dea877…)." },
  { kind: "spacer" },
  { kind: "output", text: "exit code 1 — build break", tone: "brand" },
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
            The leak, in thirty seconds
          </span>
        </RevealOnScroll>

        <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
          <h2 className="font-display text-[36px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[56px] lg:text-[64px]">
            You delete the row.
            <br />
            <span className="text-ink-3">The agent answers from it anyway.</span>
          </h2>
        </RevealOnScroll>

        <RevealOnScroll delay={0.25} className="mt-14 grid gap-5 lg:grid-cols-2">
          <Terminal
            tone="bad"
            title="Without Ferryte"
            tag="silent leak"
            lines={LEAK_BAD}
          />
          <Terminal
            tone="good"
            title="With Ferryte in CI"
            tag="caught in pre-prod"
            lines={LEAK_GOOD}
          />
        </RevealOnScroll>
      </div>
    </section>
  );
}

/* ===================================================== RECOGNITION */

const SCENARIOS = [
  "A customer revoked their document. Your agent still cites it.",
  "Tenant A's prompt surfaced something only Tenant B was meant to see.",
  "Legal asked for GDPR / CCPA delete evidence. You had to mumble.",
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
    body: "One line. Auto-patches your memory client.",
    code: `import ferryte
ferryte.instrument()`,
  },
  {
    num: "02",
    title: "Probe",
    body: "Plant canaries your data can’t produce.",
    code: `oracle.plant(
  tenant="acme",
  source="acme-doc-1",
  marker="ORION-DELTA-77",
)`,
  },
  {
    num: "03",
    title: "Verify",
    body: "Call your real delete. Break the build on survivors.",
    code: `$ ferryte test
FAIL revoked_marker_in_probe
exit 1 — build break`,
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
            <span className="text-ink-3">A broken build out.</span>
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
    body: "Drop ferryte test in CI. Stop debugging leaks at midnight.",
  },
  {
    tag: "appsec",
    title: "The reviewer who unblocks the deal.",
    body: "Trade “trust us” for a coverage number and a signed report.",
  },
  {
    tag: "compliance",
    title: "The team that signs the receipt.",
    body: "GDPR / CCPA evidence that propagates past the row.",
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
            Three buyers.
            <br />
            <span className="text-ink-3">One report they all sign.</span>
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
            <span className="text-ink-3">caught the leak first.</span>
          </h2>
        </RevealOnScroll>

        <RevealOnScroll delay={0.25} className="mt-10 max-w-xl">
          <p className="text-lede text-ink-2">
            Five teams running multi-tenant agents in production. Paired with the
            founding engineer for the first integration. You shape the roadmap.
          </p>
        </RevealOnScroll>

        <RevealOnScroll
          delay={0.4}
          className="mt-10 flex flex-wrap items-center gap-4"
        >
          <Magnetic>
            <a
              href="mailto:hello@ferryte.dev?subject=Ferryte%20design%20partner&body=Stack%3A%20%0ATenants%3A%20%0AMemory%20backend(s)%3A%20%0ALeak%20you%E2%80%99re%20worried%20about%3A%20"
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
            Or watch it leak again ↑
          </a>
        </RevealOnScroll>
      </div>
    </section>
  );
}
