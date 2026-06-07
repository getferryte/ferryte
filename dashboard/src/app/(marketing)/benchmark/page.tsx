"use client";

import Link from "next/link";

import { CopyableCommand } from "@/components/CopyableCommand";
import {
  Magnetic,
  RevealOnScroll,
  Stagger,
  StaggerItem,
  WordReveal,
} from "@/components/motion/Motion";
import {
  META,
  RESULTS,
  SCENARIOS,
  type Verdict,
} from "@/data/benchmark";

export default function Benchmark() {
  return (
    <main>
      <Hero />
      <Leaderboard />
      <HowScored />
      <Reproduce />
      <Honest />
      <CTA />
    </main>
  );
}

/* ============================================================ HERO */

function Hero() {
  const tested = RESULTS.filter((r) => r.tested).length;
  return (
    <section className="relative px-8 pb-20 pt-24 sm:px-12 lg:px-20 lg:pt-32">
      <div className="mx-auto w-full max-w-6xl">
        <RevealOnScroll className="mb-9 flex items-center gap-2.5">
          <span className="dot dot-royal dot-live" />
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
            The Forgetting Report · open benchmark
          </span>
        </RevealOnScroll>

        <WordReveal
          as="h1"
          text="We deleted the data."
          staggerDelay={0.06}
          className="font-display block text-[44px] font-light leading-[1.0] tracking-tightest text-ink sm:text-[76px] lg:text-[92px]"
        />
        <WordReveal
          as="h1"
          text="The memory kept it."
          delay={0.5}
          staggerDelay={0.06}
          className="font-display -mt-1 block text-[44px] font-light leading-[1.0] tracking-tightest text-royal sm:text-[76px] lg:text-[92px]"
        />

        <RevealOnScroll delay={0.2} className="mt-9 max-w-2xl">
          <p className="text-lede text-ink-2 sm:text-[20px]">
            A reproducible test of <span className="text-ink">delete-after-revoke</span>{" "}
            behaviour across popular agent-memory stacks. We plant a canary, call
            each stack&rsquo;s <span className="text-ink">real delete API</span>, then
            check whether the agent can still surface it — first without Ferryte,
            then with.
          </p>
        </RevealOnScroll>

        <RevealOnScroll delay={0.32} className="mt-9 flex flex-wrap items-center gap-4">
          <Magnetic>
            <a
              href="#reproduce"
              className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2"
            >
              Reproduce it yourself
              <span aria-hidden>↓</span>
            </a>
          </Magnetic>
          <Link
            href="https://github.com/getferryte/ferryte/tree/main/benchmark"
            className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
          >
            Benchmark source →
          </Link>
        </RevealOnScroll>

        <RevealOnScroll
          delay={0.42}
          className="mt-8 flex flex-wrap gap-x-8 gap-y-2 font-mono text-[11px] uppercase tracking-[0.16em] text-ink-3"
        >
          <span>{tested} stacks tested</span>
          <span>· {SCENARIOS.length} scenarios</span>
          <span>· embedder {META.embedder}</span>
          <span>· summarizer {META.summarizer}</span>
          <span>· updated {META.updated}</span>
        </RevealOnScroll>
      </div>
    </section>
  );
}

/* ===================================================== LEADERBOARD */

const VERDICT_STYLE: Record<Verdict, { label: string; cls: string }> = {
  pass: { label: "PASS", cls: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300" },
  fail: { label: "LEAK", cls: "border-rose-500/30 bg-rose-500/10 text-rose-300" },
  warn: { label: "WARN", cls: "border-amber-500/30 bg-amber-500/10 text-amber-300" },
  blind: { label: "BLIND", cls: "border-rule bg-surface text-ink-3" },
  pending: { label: "soon", cls: "border-rule/60 bg-transparent text-ink-3/60" },
};

function VerdictChip({ v }: { v: Verdict }) {
  const s = VERDICT_STYLE[v];
  return (
    <span
      className={`inline-flex min-w-[58px] items-center justify-center rounded-md border px-2.5 py-1.5 font-mono text-[10.5px] uppercase tracking-[0.14em] ${s.cls}`}
    >
      {s.label}
    </span>
  );
}

function ScorePill({ score, size = "lg" }: { score: number | null; size?: "lg" | "md" }) {
  if (score === null) {
    return <span className="font-mono text-[13px] text-ink-3/60">—</span>;
  }
  const tone =
    score >= 75 ? "text-emerald-300" : score >= 50 ? "text-amber-300" : "text-rose-300";
  const sz = size === "lg" ? "text-[26px]" : "text-[20px]";
  return (
    <span className={`font-display ${sz} font-light leading-none ${tone}`}>
      {score}
      <span className="text-[12px] text-ink-3">%</span>
    </span>
  );
}

function Delta({ before, after }: { before: number | null; after: number | null }) {
  if (before === null || after === null) return null;
  const d = after - before;
  if (d === 0) return <span className="font-mono text-[10.5px] text-ink-3/70">no change</span>;
  const sign = d > 0 ? "+" : "";
  return (
    <span className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-emerald-300/90">
      {sign}{d}pp
    </span>
  );
}

function Leaderboard() {
  return (
    <section className="border-t border-rule/70 px-8 py-20 sm:px-12 lg:px-20 lg:py-28">
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-royal">
            The leaderboard
          </span>
        </RevealOnScroll>
        <RevealOnScroll delay={0.1} className="mt-7 max-w-3xl">
          <h2 className="font-display text-[32px] font-light leading-[1.08] tracking-[-0.028em] text-ink sm:text-[48px]">
            Naive delete vs. Ferryte cascade
            <span className="text-ink-3"> — % of scenarios each stack passes cleanly.</span>
          </h2>
        </RevealOnScroll>

        <RevealOnScroll delay={0.15} className="mt-5 max-w-3xl">
          <p className="text-body text-ink-2">
            <span className="text-rose-300">Before</span> is what every framework does today:
            delete the source, hope the derived memory follows.{" "}
            <span className="text-emerald-300">After</span> turns on Ferryte&rsquo;s lineage
            cascade — the same harness, the flag <code className="font-mono text-[12.5px]">--with-ferryte</code>.
          </p>
        </RevealOnScroll>

        <Stagger className="mt-12 flex flex-col gap-6" staggerDelay={0.1}>
          {RESULTS.map((row) => (
            <StaggerItem key={row.name}>
              <BeforeAfterRow row={row} />
            </StaggerItem>
          ))}
        </Stagger>

        <RevealOnScroll delay={0.3} className="mt-10 flex flex-wrap gap-x-6 gap-y-2 text-[12px] text-ink-3">
          <Legend v="pass" text="forgot cleanly" />
          <Legend v="fail" text="leaked the revoked data" />
          <Legend v="warn" text="partial / outranked" />
          <Legend v="blind" text="couldn't verify" />
          <Legend v="pending" text="run in progress" />
        </RevealOnScroll>

        <p className="mt-8 max-w-2xl text-[12.5px] leading-relaxed text-ink-3/80">
          {META.note}
        </p>
      </div>
    </section>
  );
}

function BeforeAfterRow({ row }: { row: (typeof RESULTS)[number] }) {
  return (
    <article
      className={`rounded-lg border border-rule bg-surface p-6 transition-colors duration-base ease-out hover:border-rule-2 ${
        row.tested ? "" : "opacity-65"
      }`}
    >
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-rule/50 pb-4">
        <div>
          <div className="font-display text-[20px] font-light leading-tight tracking-[-0.015em] text-ink">
            {row.name}
          </div>
          <div className="mt-1 text-[12px] leading-snug text-ink-3">{row.kind}</div>
        </div>
        <Delta before={row.before.score} after={row.after.score} />
      </header>

      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <ScoreCard
          tone="before"
          label="Without Ferryte (naive delete)"
          score={row.before.score}
          cells={row.before.cells}
        />
        <ScoreCard
          tone="after"
          label="With Ferryte (lineage cascade)"
          score={row.after.score}
          cells={row.after.cells}
        />
      </div>

      {row.note && (
        <p className="mt-5 text-[12.5px] leading-relaxed text-ink-3/85">{row.note}</p>
      )}
    </article>
  );
}

function ScoreCard({
  tone,
  label,
  score,
  cells,
}: {
  tone: "before" | "after";
  label: string;
  score: number | null;
  cells: Record<string, Verdict>;
}) {
  const accent =
    tone === "after" ? "text-emerald-300/90" : "text-rose-300/90";
  return (
    <div className="rounded-md border border-rule/60 bg-black/30 p-5">
      <div className="flex items-end justify-between gap-3">
        <span className={`font-mono text-[10.5px] uppercase tracking-[0.16em] ${accent}`}>
          {label}
        </span>
        <ScorePill score={score} size="md" />
      </div>
      <div className="mt-4 grid grid-cols-4 gap-2">
        {SCENARIOS.map((s) => (
          <div key={s.id} className="flex flex-col items-stretch gap-1.5">
            <span className="text-center font-mono text-[9.5px] uppercase tracking-[0.12em] text-ink-3/80">
              {s.label.split(" ")[0]}
            </span>
            <VerdictChip v={cells[s.id]} />
          </div>
        ))}
      </div>
    </div>
  );
}

function Legend({ v, text }: { v: Verdict; text: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <VerdictChip v={v} />
      <span>{text}</span>
    </span>
  );
}

/* ===================================================== HOW SCORED */

const METHOD = [
  {
    n: "01",
    t: "Real backends, default configs",
    b: "Each stack runs in its recommended setup on our own deployments — no strawmen, no private systems.",
  },
  {
    n: "02",
    t: "Plant a canary the data can't invent",
    b: "A unique marker is written for one tenant, through one source, so any later appearance is provably a leak.",
  },
  {
    n: "03",
    t: "Call the real delete API",
    b: "We revoke the source the way an app would — then probe retrieval to see what survived.",
  },
  {
    n: "04",
    t: "Score what's left",
    b: "PASS if the marker is gone everywhere, LEAK if it resurfaces, BLIND if we honestly couldn't tell.",
  },
];

function HowScored() {
  return (
    <section className="border-t border-rule/70 px-8 py-20 sm:px-12 lg:px-20 lg:py-28">
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
            How it&rsquo;s scored
          </span>
        </RevealOnScroll>
        <RevealOnScroll delay={0.1} className="mt-7 max-w-3xl">
          <h2 className="font-display text-[30px] font-light leading-[1.1] tracking-[-0.026em] text-ink sm:text-[44px]">
            The raw vector DB isn&rsquo;t the villain.
            <br />
            <span className="text-ink-3">The summary layer on top is.</span>
          </h2>
        </RevealOnScroll>
        <RevealOnScroll delay={0.18} className="mt-6 max-w-2xl">
          <p className="text-body text-ink-2">
            A row delete on pgvector, Chroma, or Qdrant is clean — that&rsquo;s why
            they score identically. The leak appears once an LLM summary or
            knowledge-graph node absorbs the fact and the delete doesn&rsquo;t
            propagate. That derived layer is exactly what real agent-memory
            frameworks add — and exactly what this benchmark measures.
          </p>
        </RevealOnScroll>

        <Stagger className="mt-14 grid gap-10 md:grid-cols-2 lg:grid-cols-4" staggerDelay={0.1}>
          {METHOD.map((m) => (
            <StaggerItem key={m.n}>
              <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-royal">
                {m.n}
              </div>
              <h3 className="mt-4 font-display text-[20px] font-light leading-[1.2] tracking-[-0.018em] text-ink">
                {m.t}
              </h3>
              <p className="mt-3 text-caption text-ink-3">{m.b}</p>
            </StaggerItem>
          ))}
        </Stagger>
      </div>
    </section>
  );
}

/* ===================================================== REPRODUCE */

function Reproduce() {
  return (
    <section
      id="reproduce"
      className="border-t border-rule/70 px-8 py-20 sm:px-12 lg:px-20 lg:py-28"
    >
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-royal">
            Reproduce it yourself
          </span>
        </RevealOnScroll>
        <RevealOnScroll delay={0.1} className="mt-7 max-w-3xl">
          <h2 className="font-display text-[30px] font-light leading-[1.1] tracking-[-0.026em] text-ink sm:text-[44px]">
            Don&rsquo;t trust us. Run it.
          </h2>
        </RevealOnScroll>
        <RevealOnScroll delay={0.18} className="mt-6 max-w-2xl">
          <p className="text-body text-ink-2">
            Every number on this page comes from one command against pinned,
            open-source backends. Clone the repo, bring up the stores, point it at
            your own API key.
          </p>
        </RevealOnScroll>

        <RevealOnScroll delay={0.26} className="mt-10">
          <pre className="overflow-x-auto rounded-md border border-rule bg-surface p-6 font-mono text-[12.5px] leading-[1.7] text-ink-2">
            <code>{`git clone https://github.com/getferryte/ferryte
cd ferryte/benchmark
cp .env.example .env            # add your OpenAI key
docker compose up -d            # pgvector · qdrant · chroma
pip install -r requirements.txt

# Before: naive delete
python -m benchmark.run --scenarios all \\
  --backends mem0,qdrant,chroma,pgvector \\
  --embedder openai --summarizer openai

# After: same harness, lineage cascade on
python -m benchmark.run --scenarios all \\
  --backends mem0,qdrant,chroma,pgvector \\
  --embedder openai --summarizer openai --with-ferryte`}</code>
          </pre>
        </RevealOnScroll>

        <RevealOnScroll delay={0.34} className="mt-6">
          <CopyableCommand command="git clone https://github.com/getferryte/ferryte" />
        </RevealOnScroll>
      </div>
    </section>
  );
}

/* ===================================================== HONEST */

const FAQ = [
  {
    q: "“You sell the fix — of course you found leaks.”",
    a: "Fair to ask. That's why the entire harness is open, the configs and versions are pinned, and you can falsify any cell yourself. We also publish what PASSES — cross-tenant isolation holds on every stack we've tested.",
  },
  {
    q: "Did you rig the configs?",
    a: "No. Backends run in their default / recommended setups on our own deployments. We never touch anyone's private systems, and the in-memory illustrative baseline is kept separate from real-backend results.",
  },
  {
    q: "What did you NOT test?",
    a: "Proprietary managed memory we can't self-host, and any behaviour behind a paywall we didn't buy. Where we can't verify, a cell reads BLIND — never a silent PASS.",
  },
  {
    q: "Isn't a vector DB row-delete enough?",
    a: "For the raw row, yes. The leak is the derived layer — summaries and graph nodes that absorbed the fact. The vendors document this themselves.",
  },
];

function Honest() {
  return (
    <section className="border-t border-rule/70 px-8 py-20 sm:px-12 lg:px-20 lg:py-28">
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
            Blind spots &amp; the obvious objection
          </span>
        </RevealOnScroll>
        <RevealOnScroll delay={0.1} className="mt-7 max-w-3xl">
          <h2 className="font-display text-[30px] font-light leading-[1.1] tracking-[-0.026em] text-ink sm:text-[44px]">
            The part most benchmarks hide.
          </h2>
        </RevealOnScroll>

        <Stagger className="mt-12 grid gap-4 sm:grid-cols-2" staggerDelay={0.08}>
          {FAQ.map((f) => (
            <StaggerItem key={f.q}>
              <article className="flex h-full flex-col rounded-lg border border-rule bg-surface p-7 transition-colors duration-base ease-out hover:border-rule-2">
                <h3 className="font-display text-[19px] font-light leading-[1.3] tracking-[-0.012em] text-ink">
                  {f.q}
                </h3>
                <p className="mt-4 text-body text-ink-2">{f.a}</p>
              </article>
            </StaggerItem>
          ))}
        </Stagger>
      </div>
    </section>
  );
}

/* ============================================================ CTA */

function CTA() {
  return (
    <section className="brand-hairline relative border-t border-rule/70 px-8 py-24 sm:px-12 lg:px-20 lg:py-36">
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-royal">
            Catch it in CI, not in a customer ticket
          </span>
        </RevealOnScroll>
        <RevealOnScroll delay={0.1} className="mt-8 max-w-4xl">
          <h2 className="font-display text-[36px] font-light leading-[1.05] tracking-[-0.03em] text-ink sm:text-[60px] lg:text-[72px]">
            Run the same test
            <br />
            <span className="text-ink-3">against your own stack.</span>
          </h2>
        </RevealOnScroll>
        <RevealOnScroll delay={0.24} className="mt-10 flex flex-wrap items-center gap-4">
          <CopyableCommand command="pip install ferryte" />
          <Magnetic>
            <a
              href="mailto:hello@ferryte.dev?subject=Ferryte%20benchmark%20on%20our%20stack"
              className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2"
            >
              Request a free audit
              <span aria-hidden>→</span>
            </a>
          </Magnetic>
          <Link
            href="/product"
            className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
          >
            How Ferryte works →
          </Link>
        </RevealOnScroll>
      </div>
    </section>
  );
}
