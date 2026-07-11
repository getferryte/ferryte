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
        <EvidenceLadder />
        <Stack />
        <TrustArchitecture />
        <Personas />
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
    body: "Start with one line — ferryte.instrument(). Mem0 and Zep clients created afterward are detected automatically; shipped adapters cover Letta, Cloudflare, and Ferryte's vector reference store, while custom stores plug into the same small adapter protocol.",
    code: `import ferryte
ferryte.instrument()

# the rest of your app stays the same`,
  },
  {
    num: "02",
    title: "Trace",
    body: "As your agent runs, Ferryte records where every memory came from, what it derived into, and every retrieval that pulled it into a prompt. One optional call per turn links memories to the exact answers they produced.",
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
    body: "Point at a wrong, stale, or leaked answer. Ferryte ranks the memories that caused it — using recorded answer edges, retrieval evidence, and quote-level shared spans — and names the fault: phantom, stale, cross-tenant, zombie, or poisoned.",
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
    body: "Before deleting anything, replay the retrieval without the top suspect and see what would have entered the context instead. Then delete or supersede the bad memory and re-run to prove nothing survived.",
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
  { name: "Vector stores", status: "stable", body: "Instrumented reference store + adapter base ship today. pgvector, Chroma, and Qdrant need a thin store-specific adapter." },
  { name: "Mem0", status: "stable", body: "Auto-patch on construction. Full lineage across its LLM-extracted facts." },
  { name: "AWS AgentCore", status: "benchmark", body: "Verified live in the public benchmark harness. A Core runtime adapter is not shipped yet." },
  { name: "Zep", status: "beta", body: "Captures episodes + graph facts; traces shared-node summaries back to source." },
  { name: "Letta", status: "beta", body: "Archival passages + derived summaries. Shipped in Core; pass the client explicitly." },
  { name: "Cloudflare Agents", status: "beta", body: "Vectorize-backed memory. Shipped in Core; pass the client explicitly." },
  { name: "Custom stores", status: "stable", body: "Implement the small Adapter protocol for your write, search, and delete surface." },
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


/* ----------------------------------------------- Evidence ladder */

const LADDER = [
  {
    rank: "strongest",
    name: "Recorded answer edge",
    body: "Your app called record_answer() — we know exactly which memories were in context when this answer was produced. Anchored, not inferred.",
    method: "method: exact",
  },
  {
    rank: "strong",
    name: "Retrieval trace",
    body: "The memory demonstrably entered the prompt for a matching query. The difference between a plausible suspect and a live one.",
    method: "retrieved into context",
  },
  {
    rank: "good",
    name: "IDF-weighted span overlap",
    body: "Rare shared terms count, common ones don't. Contiguous shared spans of three or more meaningful tokens are quoted back as evidence.",
    method: "shared span",
  },
  {
    rank: "fallback",
    name: "Semantic residue",
    body: "A pluggable embedder catches paraphrase when the exact words differ. Token-bag by default, neural drop-in when you want it.",
    method: "method: semantic",
  },
];

function EvidenceLadder() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-28">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          How attribution earns your trust
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          Four signals, strongest first.
          <br />
          <span className="text-ink-3">And it never pretends.</span>
        </h2>
      </RevealOnScroll>

      <Stagger className="mt-12 flex flex-col gap-4" staggerDelay={0.08}>
        {LADDER.map((l, i) => (
          <StaggerItem key={l.name}>
            <article className="flex flex-col gap-3 rounded-lg border border-rule bg-surface px-7 py-6 transition-colors duration-base ease-out hover:border-rule-2 sm:flex-row sm:items-baseline sm:gap-8">
              <span className="w-24 shrink-0 font-mono text-[10.5px] uppercase tracking-[0.18em] text-royal">
                {i + 1} · {l.rank}
              </span>
              <div className="flex-1">
                <h3 className="font-display text-[19px] font-light tracking-[-0.014em] text-ink">
                  {l.name}
                </h3>
                <p className="mt-2 text-body text-ink-2">{l.body}</p>
              </div>
              <span className="shrink-0 font-mono text-[11px] text-ink-3">{l.method}</span>
            </article>
          </StaggerItem>
        ))}
      </Stagger>

      <RevealOnScroll delay={0.3} className="mt-8 max-w-2xl">
        <p className="text-caption text-ink-3">
          No recorded edge? The report says <span className="font-mono">method: overlap</span>,
          never <span className="font-mono">exact</span>. Ferryte labels the strength of its own
          evidence — the same honesty that powers the blind-spot map.
        </p>
      </RevealOnScroll>
    </section>
  );
}

/* ----------------------------------------------- Trust architecture */

const TRUST = [
  {
    q: "What does instrument() actually touch?",
    a: "It patches the write/search/delete methods of detected memory clients (plus a constructor hook for clients built later). Your agent code is unchanged; remove the line and Ferryte is gone.",
  },
  {
    q: "Where does the data live?",
    a: "A local SQLite file (.ferryte/lineage.db) in your environment. No telemetry, no phone-home, no external service. The optional dashboard reads a local API you start yourself.",
  },
  {
    q: "What leaves my machine?",
    a: "Nothing. Reports are files you generate and choose to share. A hash-only fingerprint mode exists for teams that don't want raw content even in the local store.",
  },
  {
    q: "Can my security team read the code first?",
    a: "Every line. The engine is source-available (BSL 1.1) — auditability is the whole reason the license keeps the source open.",
  },
];

function TrustArchitecture() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-28">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          For the pre-integration security review
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          The questions your security team
          <br />
          <span className="text-ink-3">will ask. Answered now.</span>
        </h2>
      </RevealOnScroll>

      <Stagger className="mt-12 grid gap-10 sm:grid-cols-2" staggerDelay={0.08}>
        {TRUST.map((t) => (
          <StaggerItem key={t.q}>
            <article className="grid gap-3 border-l-2 border-rule pl-6 transition-colors duration-base ease-out hover:border-royal">
              <h3 className="font-display text-[19px] font-light tracking-[-0.014em] text-ink sm:text-[22px]">
                {t.q}
              </h3>
              <p className="text-body text-ink-2">{t.a}</p>
            </article>
          </StaggerItem>
        ))}
      </Stagger>
    </section>
  );
}

/* ----------------------------------------------- Personas */

const PERSONAS = [
  {
    tag: "engineering",
    title: "The lead who owns the agent.",
    body: "Stop grepping traces at midnight. One command to the memory that caused it.",
  },
  {
    tag: "support & ops",
    title: "The team fielding \u201cthe AI is confused about me.\u201d",
    body: "See exactly what the agent remembers about a user — and correct it.",
  },
  {
    tag: "compliance",
    title: "The team that signs the receipt.",
    body: "Prove a deleted memory — and everything derived from it — is really gone.",
  },
];

function Personas() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-28">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          Built for
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          Three teams.
          <br />
          <span className="text-ink-3">One view of the memory.</span>
        </h2>
      </RevealOnScroll>

      <Stagger className="mt-12 grid gap-12 md:grid-cols-3" staggerDelay={0.1}>
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
    </section>
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
