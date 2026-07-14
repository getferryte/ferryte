"use client";

import {
  Magnetic,
  Reveal,
  RevealOnScroll,
  Stagger,
  StaggerItem,
} from "@/components/motion/Motion";

const MAILTO =
  "mailto:pranav@ferryte.dev?subject=Agent%20Memory%20Audit&body=Stack%20(framework%2C%20memory%20backend%2C%20hosting)%3A%20%0ATenants%20served%3A%20%0AWorst%20memory%20bug%20you're%20fighting%3A%20%0APreferred%20kickoff%20window%3A%20";

export default function AuditPage() {
  return (
    <main className="px-8 sm:px-12 lg:px-20">
      <div className="mx-auto max-w-6xl">
        <Header />
        <Deliverables />
        <HowItWorks />
        <SampleReport />
        <Guarantee />
        <FAQ />
      </div>
    </main>
  );
}

function Header() {
  return (
    <section className="pt-28 pb-12 sm:pt-36 sm:pb-20">
      <Reveal delay={0.05}>
        <div className="flex items-center gap-2.5">
          <span className="dot dot-royal dot-live" />
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
            Fixed price · 48-hour turnaround · runs in your infra
          </span>
        </div>
      </Reveal>

      <Reveal delay={0.18} className="mt-10 max-w-5xl">
        <h1 className="font-display text-[44px] font-light leading-[1.02] tracking-[-0.04em] text-ink sm:text-[72px] lg:text-[88px]">
          Your agent&rsquo;s memory has bugs
          <br />
          <span className="text-ink-3">you can&rsquo;t see. We&rsquo;ll show you every one.</span>
        </h1>
      </Reveal>

      <Reveal delay={0.4} className="mt-8 max-w-2xl">
        <p className="text-lede text-ink-2">
          The Agent Memory Audit: we instrument your agent, run the full
          forgetting battery against your real memory backend, trace your
          worst wrong answers to the exact memories that caused them — and
          hand you the evidence, the blind-spot map, and the fix list. In 48
          hours, for a fixed <span className="text-ink">$500</span>.
        </p>
      </Reveal>

      <Reveal delay={0.52} className="mt-10 flex flex-wrap items-center gap-4">
        <Magnetic>
          <a
            href={MAILTO}
            className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2"
          >
            Book the audit — $500
            <span aria-hidden>→</span>
          </a>
        </Magnetic>
        <a
          href="/sample-audit.html"
          className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
        >
          Read a sample report →
        </a>
      </Reveal>
    </section>
  );
}

const DELIVERABLES = [
  {
    title: "Instrumentation, paired",
    body: "A 60–90 minute kickoff call where we wire ferryte.instrument() into your agent together. One line; no agent-code changes. You keep the instrumentation forever.",
  },
  {
    title: "The full forgetting battery",
    body: "All five structural scenarios against your real backend: source-revocation, cross-tenant-isolation, stale-fact, memory-poisoning, and mosaic reconstruction. Both retrieval results and raw store contents are checked.",
  },
  {
    title: "Root cause for your worst answers",
    body: "Bring up to three wrong, stale, or leaked answers. ferryte why traces each one to the memory that caused it — with shared-span evidence and counterfactual replay proving what would have happened without it.",
  },
  {
    title: "The written report",
    body: "A print-ready deliverable your boss can read: executive summary, findings ranked by severity, evidence chains, the honest blind-spot map (what we could NOT verify), and a prioritized fix list.",
  },
  {
    title: "The readout",
    body: "A 30-minute call walking your team through every finding and exactly how to fix each one. Re-run the same commands after the fix to prove it stuck.",
  },
];

function Deliverables() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-24">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          What you get
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          Five deliverables. One fixed price.
        </h2>
      </RevealOnScroll>

      <Stagger className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3" staggerDelay={0.08}>
        {DELIVERABLES.map((d, i) => (
          <StaggerItem key={d.title}>
            <article className="flex h-full flex-col rounded-xl border border-rule bg-surface p-7 transition-colors duration-base ease-out hover:border-rule-2">
              <span className="font-mono text-[11px] text-royal">
                0{i + 1}
              </span>
              <h3 className="mt-3 font-display text-[20px] font-light tracking-[-0.014em] text-ink">
                {d.title}
              </h3>
              <p className="mt-3 text-body text-ink-2">{d.body}</p>
            </article>
          </StaggerItem>
        ))}
      </Stagger>
    </section>
  );
}

const STEPS = [
  {
    step: "Day 0",
    title: "15-minute fit call",
    body: "Free. We confirm the integration path for Mem0, Zep, Letta, Cloudflare Agents, or your vector store; AgentCore engagements are assessed case-by-case through the benchmark harness. We agree on scope and sign NDAs if needed. If we're not a fit, we tell you plainly.",
  },
  {
    step: "Day 1",
    title: "Kickoff + runs",
    body: "We instrument together on a call, seed canaries, and run the battery in your staging or prod-adjacent environment. Nothing leaves your infrastructure — Ferryte is source-available, so your security team can read every line first.",
  },
  {
    step: "Day 2",
    title: "Report + readout",
    body: "You get the written report and a 30-minute readout: every finding, its evidence, its fix — and what we couldn't verify, stated honestly.",
  },
];

function HowItWorks() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-24">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          How it works
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          Kickoff to fix list in 48 hours.
        </h2>
      </RevealOnScroll>

      <Stagger className="mt-12 grid gap-5 lg:grid-cols-3" staggerDelay={0.1}>
        {STEPS.map((s) => (
          <StaggerItem key={s.step}>
            <article className="grid gap-3 border-l-2 border-rule pl-6 transition-colors duration-base ease-out hover:border-royal">
              <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
                {s.step}
              </span>
              <h3 className="font-display text-[20px] font-light tracking-[-0.014em] text-ink sm:text-[24px]">
                {s.title}
              </h3>
              <p className="text-body text-ink-2">{s.body}</p>
            </article>
          </StaggerItem>
        ))}
      </Stagger>
    </section>
  );
}

function SampleReport() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-24">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          The deliverable
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          Read a sample before you buy.
        </h2>
      </RevealOnScroll>

      <RevealOnScroll delay={0.2} className="mt-6 max-w-2xl">
        <p className="text-body text-ink-2">
          This is a real report generated by the same pipeline your audit
          uses, run against our reproducible multi-tenant-leak demo and
          anonymized. Every claim in your report carries its evidence:
          the shared span, the retrieval trace, the supersession edge, the
          replay verdict.
        </p>
      </RevealOnScroll>

      <RevealOnScroll delay={0.3} className="mt-8">
        <Magnetic>
          <a
            href="/sample-audit.html"
            className="inline-flex items-center gap-1.5 rounded-full border border-rule-2 px-5 py-3 text-[14px] font-medium text-ink transition-colors duration-fast ease-out hover:bg-surface-2"
          >
            Open the sample report
            <span aria-hidden>→</span>
          </a>
        </Magnetic>
      </RevealOnScroll>
    </section>
  );
}

function Guarantee() {
  return (
    <section className="brand-hairline relative border-t border-rule/60 py-24 lg:py-32">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-royal">
          The guarantee
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-4xl">
        <h2 className="font-display text-[40px] font-light leading-[1.04] tracking-[-0.03em] text-ink sm:text-[64px]">
          Nothing actionable found?
          <br />
          <span className="text-ink-3">Full refund. No argument.</span>
        </h2>
      </RevealOnScroll>

      <RevealOnScroll delay={0.2} className="mt-10 max-w-2xl">
        <p className="text-lede text-ink-2">
          If the audit surfaces no actionable finding — no structural failure,
          no attributable wrong answer, no blind spot worth closing — you pay
          nothing. Audit customers also get first claim on the five
          design-partner seats: six months of Cloud free when it ships, and
          the audit fee credited against it.
        </p>
      </RevealOnScroll>

      <RevealOnScroll delay={0.32} className="mt-10 flex flex-wrap items-center gap-4">
        <Magnetic>
          <a
            href={MAILTO}
            className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2"
          >
            Email pranav@ferryte.dev
            <span aria-hidden>→</span>
          </a>
        </Magnetic>
        <span className="text-caption text-ink-3">
          Two audit slots per week. First reply within 24 hours.
        </span>
      </RevealOnScroll>
    </section>
  );
}

const FAQ_ITEMS = [
  {
    q: "Does our data leave our infrastructure?",
    a: "No. Ferryte runs inside your environment; memory contents never leave it. The only artifact that crosses the boundary is the report itself, and you review it before anyone else sees it. Ferryte is source-available (BSL 1.1), so your security team can audit every line of what runs.",
  },
  {
    q: "What do you need from us?",
    a: "A Python agent with a persistent memory backend, one engineer on the kickoff call, access to a staging or prod-adjacent environment, and — ideally — up to three wrong answers you want explained. That's it.",
  },
  {
    q: "Our memory layer is custom / not on your list.",
    a: "If it's a vector store with write, search, and delete, the generic adapter usually covers it — that's exactly what the free fit call establishes. If we can't support your stack, we say so on that call and you pay nothing.",
  },
  {
    q: "Why is it so cheap?",
    a: "Because it's also how we choose design partners for Ferryte Cloud. You get a senior engineer and the full engine at a price that needs no procurement; we get to see real production memory bugs. The fee is credited against Cloud if you take a design-partner seat.",
  },
  {
    q: "Can you also fix what you find?",
    a: "The audit hands you the fix list and proves each fix when you apply it. If you want us to implement the fixes with you, that's the Fix Sprint — $1,500, scoped on the readout call.",
  },
];

function FAQ() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-24">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          FAQ
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          What buyers ask first.
        </h2>
      </RevealOnScroll>

      <Stagger className="mt-12 flex flex-col gap-10" staggerDelay={0.08}>
        {FAQ_ITEMS.map((item) => (
          <StaggerItem key={item.q}>
            <article className="grid gap-3 border-l-2 border-rule pl-6 transition-colors duration-base ease-out hover:border-royal">
              <h3 className="font-display text-[20px] font-light tracking-[-0.014em] text-ink sm:text-[24px]">
                {item.q}
              </h3>
              <p className="text-body text-ink-2">{item.a}</p>
            </article>
          </StaggerItem>
        ))}
      </Stagger>
    </section>
  );
}
