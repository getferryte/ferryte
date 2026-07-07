"use client";

import Link from "next/link";

import { CopyableCommand } from "@/components/CopyableCommand";
import {
  Magnetic,
  Reveal,
  RevealOnScroll,
  Stagger,
  StaggerItem,
} from "@/components/motion/Motion";

export default function ProductPage() {
  return (
    <main className="px-8 sm:px-12 lg:px-20">
      <div className="mx-auto max-w-6xl">
        <Header />
        <HowItWorks />
        <BeforeAfter />
        <WhatItProves />
        <Stack />
        <Close />
      </div>
    </main>
  );
}

/* ---------------------------------------------------------- Header */

function Header() {
  return (
    <section className="pt-28 pb-12 sm:pt-36 sm:pb-20">
      <Reveal delay={0.05}>
        <div className="flex items-center gap-2.5">
          <span className="dot dot-royal dot-live" />
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
            Product · how Ferryte works
          </span>
        </div>
      </Reveal>

      <Reveal delay={0.18} className="mt-10 max-w-4xl">
        <h1 className="font-display text-[44px] font-light leading-[1.02] tracking-[-0.04em] text-ink sm:text-[72px] lg:text-[96px]">
          One line.
          <br />
          <span className="text-ink-3">Full memory provenance.</span>
        </h1>
      </Reveal>

      <Reveal delay={0.4} className="mt-8 max-w-2xl">
        <p className="text-lede text-ink-2">
          Ferryte does not ask you to migrate your memory layer or wrap your agent.
          It instruments what you already run, records where every memory came
          from, and lets you trace any answer back to the memory behind it.
        </p>
      </Reveal>

      <Reveal delay={0.55} className="mt-10 flex flex-wrap items-center gap-3">
        <CopyableCommand command="pip install ferryte" />
        <CopyableCommand command={'ferryte why "that wrong answer"'} />
      </Reveal>
    </section>
  );
}

/* -------------------------------------------------------- How it works */

const STEPS = [
  {
    num: "01",
    title: "Instrument",
    body: "One line — ferryte.instrument(). Auto-patches your memory client at construction time — the generic vector base, AgentCore, Zep, Letta, Cloudflare, Mem0 — plus subclasses for pgvector, Chroma, Qdrant. Your agent code does not change.",
    code: `import ferryte
ferryte.instrument()

# the rest of your app stays the same`,
  },
  {
    num: "02",
    title: "Trace",
    body: "As your agent runs, Ferryte records write-time lineage for every memory: the source it came from, the summaries and embeddings it derived into, every retrieval that pulled it into a prompt, and — with one optional call per turn — the exact answer those memories produced.",
    code: `# recorded automatically
mem_3f9c
  ← source  zendesk-ticket-8821
  → derived summary_v2, embedding
  → retrieved 14x (tenant=acme)

# optional: exact answer→memory edge
ferryte.record_answer(
  answer_id=turn_id,
  content=answer,
  artifact_ids=[m.id for m in context],
)`,
  },
  {
    num: "03",
    title: "Attribute",
    body: "Point at a wrong, stale, or leaked answer. Ferryte ranks the memories that caused it using recorded answer-input edges, retrieval evidence, IDF-weighted overlap, and quote-level shared spans — then flags phantom, stale, cross-tenant, zombie, and poison-pattern hub memories.",
    code: `$ ferryte why "Legacy Free plan"
#1  stale belief · conf 1.00
  from zendesk-ticket-8821
  recorded in context for this answer
  shared span: "legacy free plan"
  superseded by billing-sync-0601`,
  },
  {
    num: "04",
    title: "Replay, fix, verify",
    body: "Before you delete anything, Ferryte can run a retrieval-layer counterfactual: remove the top suspect and show what would have entered the agent's context instead. Then delete or supersede the bad memory and run the forgetting oracle to prove no revoked residue survives.",
    code: `$ ferryte why "Legacy Free plan" --replay
counterfactual: without mem_old → Pro plan

$ ferryte test --scenario source-revocation
source-revocation   PASS
no surviving markers in retrieval ✓`,
  },
];

function HowItWorks() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-28">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          How it works
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[52px]">
          Four steps from install to root cause.
        </h2>
      </RevealOnScroll>

      <div className="mt-16 flex flex-col gap-12">
        {STEPS.map((s, i) => (
          <Step key={s.num} {...s} index={i} />
        ))}
      </div>
    </section>
  );
}

function Step({
  num,
  title,
  body,
  code,
  index,
}: {
  num: string;
  title: string;
  body: string;
  code: string;
  index: number;
}) {
  return (
    <RevealOnScroll delay={index * 0.05}>
      <article className="grid gap-10 border-t border-rule/60 pt-10 lg:grid-cols-[1fr_1.2fr] lg:gap-16">
        <header>
          <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-royal">
            Step {num}
          </div>
          <h3 className="mt-4 font-display text-[28px] font-light leading-[1.1] tracking-[-0.024em] text-ink sm:text-[36px]">
            {title}
          </h3>
          <p className="mt-5 text-body text-ink-2">{body}</p>
        </header>
        <pre className="overflow-x-auto rounded-lg border border-rule bg-surface p-6 font-mono text-[13px] leading-[1.6] text-ink-2">
          <code>{code}</code>
        </pre>
      </article>
    </RevealOnScroll>
  );
}

/* ----------------------------------------------- Before / after columns */

function BeforeAfter() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-28">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          What it catches
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[52px]">
          The invisible memory bug, in two columns.
        </h2>
      </RevealOnScroll>

      <Stagger
        className="mt-14 grid gap-6 lg:grid-cols-2"
        staggerDelay={0.12}
      >
        <StaggerItem>
          <Column
            tone="bad"
            label="Without Ferryte"
            tag="grep the traces"
            code={`› agent.ask("acme", "what plan is this customer on?")
You're on the Legacy Free plan.

# wrong — they upgraded to Pro last week.
# somewhere a stale fact still wins retrieval.
# which memory? open the logs and start reading…`}
          />
        </StaggerItem>
        <StaggerItem>
          <Column
            tone="good"
            label="With Ferryte"
            tag="root cause"
            code={`› ferryte why "Legacy Free plan"
caused by 3 candidate memories · top conf 1.00

#1  stale belief · conf 1.00
  Customer acme is on the Legacy Free plan.
  from 'zendesk-ticket-8821'
  recorded in context for this answer
  shared span: "legacy free plan"

› ferryte why "Legacy Free plan" --replay
counterfactual: without it → Pro plan

fix: delete it, then re-run why to confirm`}
          />
        </StaggerItem>
      </Stagger>
    </section>
  );
}

function Column({
  tone,
  label,
  tag,
  code,
}: {
  tone: "good" | "bad";
  label: string;
  tag: string;
  code: string;
}) {
  return (
    <div className="rounded-lg border border-rule bg-surface p-7">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          {label}
        </span>
        <span
          className={[
            "inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.18em]",
            tone === "bad" ? "text-issue" : "text-ok",
          ].join(" ")}
        >
          <span
            className={[
              "dot",
              tone === "bad" ? "dot-issue" : "dot-ok",
            ].join(" ")}
          />
          {tag}
        </span>
      </div>
      <pre className="mt-5 overflow-x-auto font-mono text-[12.5px] leading-[1.65] text-ink-2">
        <code>{code}</code>
      </pre>
    </div>
  );
}

/* ----------------------------------------------- What it proves */

const COVERED = [
  "Stale belief — an old fact still outranking the correction that replaced it.",
  "Cross-contamination — tenant A receiving something only tenant B ever told the agent.",
  "Phantom memory — deleted data still driving answers via a summary or embedding.",
  "Hub / poisoned memory — one record showing up across too many unrelated queries.",
  "Answer attribution — the exact memories present when a wrong answer was produced.",
  "Mosaic mis-belief — fragments across sources recombining into a wrong conclusion.",
];

const HONEST = [
  "Stores Ferryte cannot reach through the adapter interface.",
  "Retrieval paths that bypass the patched memory client entirely.",
  "Attribution confidence below the configured replay budget — reported as ranked candidates, never a false certainty.",
];

function WhatItProves() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-28">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          What it catches — and where it’s honest
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[52px]">
          The memory bugs you can name, and the ones we won’t fake.
        </h2>
      </RevealOnScroll>

      <div className="mt-14 grid gap-12 lg:grid-cols-2">
        <RevealOnScroll>
          <h3 className="flex items-center gap-2 font-mono text-[10.5px] uppercase tracking-[0.22em] text-ok">
            <span className="dot dot-ok" /> Covered
          </h3>
          <ul className="mt-5 flex flex-col gap-3.5">
            {COVERED.map((c) => (
              <li
                key={c}
                className="text-body text-ink-2 before:mr-3 before:text-ok before:content-['+']"
              >
                {c}
              </li>
            ))}
          </ul>
        </RevealOnScroll>

        <RevealOnScroll delay={0.1}>
          <h3 className="flex items-center gap-2 font-mono text-[10.5px] uppercase tracking-[0.22em] text-pending">
            <span className="dot dot-pending" /> Honest about
          </h3>
          <ul className="mt-5 flex flex-col gap-3.5">
            {HONEST.map((h) => (
              <li
                key={h}
                className="text-body text-ink-2 before:mr-3 before:text-pending before:content-['~']"
              >
                {h}
              </li>
            ))}
          </ul>
          <p className="mt-6 text-caption text-ink-3">
            Blind spots are surfaced in every report. We would rather hand you ranked candidates than a confident wrong answer.
          </p>
        </RevealOnScroll>
      </div>
    </section>
  );
}

/* ----------------------------------------------- Stack */

const STACK = [
  { name: "Vector stores", status: "stable", body: "Generic vector base ships today. Subclass for pgvector, Chroma, Qdrant." },
  { name: "Mem0", status: "stable", body: "Auto-patch on construction. Full lineage across its LLM-extracted facts." },
  { name: "AWS AgentCore", status: "beta", body: "Traces semantic long-term memory. Verified live: derived records survive DeleteEvent — Ferryte surfaces them." },
  { name: "Zep", status: "beta", body: "Captures episodes + graph facts; traces shared-node summaries back to source." },
  { name: "Letta", status: "beta", body: "Archival passages + derived summaries. Shipped in Core." },
  { name: "Cloudflare Agents", status: "beta", body: "Vectorize-backed memory. Shipped in Core." },
  { name: "Custom stores", status: "stable", body: "Implement the 80-line MemoryAdapter protocol." },
  { name: "LangGraph", status: "planned", body: "Tracing hooks on the roadmap." },
];

function Stack() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-28">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          What we plug into
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          Adapters.
        </h2>
      </RevealOnScroll>

      <Stagger className="mt-12 grid gap-3 md:grid-cols-2 lg:grid-cols-3" staggerDelay={0.06}>
        {STACK.map((s) => (
          <StaggerItem key={s.name}>
            <div className="rounded-lg border border-rule bg-surface p-5 transition-colors duration-base ease-out hover:border-rule-2">
              <div className="flex items-center justify-between">
                <span className="font-display text-[20px] font-light tracking-[-0.014em] text-ink">
                  {s.name}
                </span>
                <StatusBadge status={s.status as "stable" | "beta" | "planned"} />
              </div>
              <p className="mt-3 text-caption text-ink-3">{s.body}</p>
            </div>
          </StaggerItem>
        ))}
      </Stagger>
    </section>
  );
}

function StatusBadge({ status }: { status: "stable" | "beta" | "planned" }) {
  const tone = {
    stable: "text-ok",
    beta: "text-pending",
    planned: "text-ink-3",
  }[status];
  const dot = {
    stable: "dot-ok",
    beta: "dot-pending",
    planned: "dot-neutral",
  }[status];
  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 font-mono text-[9.5px] uppercase tracking-[0.18em]",
        tone,
      ].join(" ")}
    >
      <span className={["dot", dot].join(" ")} />
      {status}
    </span>
  );
}

/* ----------------------------------------------- Close */

function Close() {
  return (
    <section className="border-t border-rule/60 py-24">
      <RevealOnScroll>
        <h2 className="font-display text-[36px] font-light leading-[1.04] tracking-[-0.03em] text-ink sm:text-[56px]">
          Open it up. See the memory.
        </h2>
      </RevealOnScroll>

      <RevealOnScroll delay={0.15} className="mt-10 flex flex-wrap items-center gap-4">
        <Magnetic>
          <Link
            href="/app"
            className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2"
          >
            Open the dashboard
            <span aria-hidden>→</span>
          </Link>
        </Magnetic>
        <a
          href="https://github.com/getferryte/ferryte"
          className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
        >
          Read the source on GitHub →
        </a>
        <Link
          href="/pricing"
          className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
        >
          See pricing →
        </Link>
      </RevealOnScroll>
    </section>
  );
}
