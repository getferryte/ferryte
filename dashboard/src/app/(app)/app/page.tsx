import Link from "next/link";

import { Chip, Dot, StatusLabel, type Tone } from "@/components/Pill";
import { ScenarioRow } from "@/components/ScenarioRow";
import { Stat, StatRow } from "@/components/Stat";
import { loadReport } from "@/lib/report";

type Verdict = "pass" | "warn" | "fail";

export default async function Page() {
  const report = await loadReport();
  const s = report.coverage.summary;
  const counts = report.coverage.lineage_counts || {};
  const failed = report.results.some((r) => r.severity === "fail");
  const warned = report.results.some((r) => r.severity === "warn");
  const overall: Verdict = failed ? "fail" : warned ? "warn" : "pass";

  return (
    <div className="space-y-28 ui-fade">
      <Hero
        generatedAt={report.generated_at}
        backends={s.backends_instrumented}
        verdict={overall}
      />

      <Numbers
        leaks={s.failed}
        partial={s.warned}
        verified={s.passed}
        blindspots={s.blindspot_observations}
      />

      <Scenarios results={report.results} />

      <Lineage counts={counts} backends={report.coverage.backends} />

      <Quote />
    </div>
  );
}

/* ------------------------------------------------------------------ Hero */

function Hero({
  generatedAt,
  backends,
  verdict,
}: {
  generatedAt: string;
  backends: string[];
  verdict: Verdict;
}) {
  const headline =
    verdict === "fail"
      ? "Forgetting failed."
      : verdict === "warn"
        ? "Forgetting is partial."
        : "Forgetting verified.";
  const subhead =
    verdict === "fail"
      ? "Your agent is still acting on revoked data."
      : verdict === "warn"
        ? "Derived artifacts survived deletion."
        : "Every revoked source was provably removed from retrieval.";
  const accent: Tone =
    verdict === "fail" ? "issue" : verdict === "warn" ? "pending" : "ok";

  return (
    <section className="ui-rise">
      <div className="flex items-center gap-2.5 text-caption text-ink-3">
        <StatusLabel tone="royal" live>
          Live
        </StatusLabel>
        <span className="text-ink-4">/</span>
        <time className="font-mono">{formatTime(generatedAt)}</time>
      </div>

      <h1 className="mt-10 max-w-[18ch] font-display text-[64px] font-light leading-[0.98] tracking-tightest text-ink sm:text-[76px] lg:text-[88px]">
        <span>{headline}</span>
        <br />
        <span className="text-ink-3">{subhead}</span>
      </h1>

      <p className="mt-10 max-w-xl text-lede text-ink-2">
        Ferryte plants canary memories tagged by source and tenant, calls your
        backend&rsquo;s real delete API, replays the agent, then inspects both store
        contents and retrieval traces. The verdict — including what could not be
        seen — is below.
      </p>

      <div className="mt-10 flex flex-wrap items-center gap-3">
        <Command />
        <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-ink-3">
          CI gate · non-zero exit on leak
        </span>
      </div>

      <div className="mt-10 flex flex-wrap items-center gap-2">
        <Dot tone={accent} />
        <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-ink-3">
          Instrumented
        </span>
        {backends.map((b) => (
          <Chip key={b}>{b}</Chip>
        ))}
      </div>
    </section>
  );
}

function Command() {
  return (
    <code className="inline-flex items-center gap-2.5 rounded-md border border-rule bg-surface px-3.5 py-2 font-mono text-[12.5px] text-ink-2 transition-colors duration-base ease-out hover:border-rule-2">
      <span className="text-royal">›</span>
      <span className="text-ink">ferryte test</span>
      <span className="text-ink-3">--scenario source-revocation</span>
    </code>
  );
}

/* ------------------------------------------------------------ Big numbers */

function Numbers({
  leaks,
  partial,
  verified,
  blindspots,
}: {
  leaks: number;
  partial: number;
  verified: number;
  blindspots: number;
}) {
  return (
    <section>
      <Eyebrow>Verdict at a glance</Eyebrow>
      <div className="mt-10 stagger">
        <StatRow>
          <Stat
            label="Leaks"
            value={leaks}
            tone={leaks > 0 ? "issue" : "neutral"}
            hint={leaks > 0 ? "revoked context still influenced output" : "none observed"}
          />
          <Stat
            label="Partial"
            value={partial}
            tone={partial > 0 ? "pending" : "neutral"}
            hint={partial > 0 ? "derived artifacts survived deletion" : "no warnings"}
          />
          <Stat
            label="Verified"
            value={verified}
            tone={verified > 0 ? "ok" : "neutral"}
            hint="scenarios that fully forgot"
          />
          <Stat
            label="Blind spots"
            value={blindspots}
            tone="neutral"
            hint="things Ferryte couldn't verify"
          />
        </StatRow>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------ Scenarios */

function Scenarios({ results }: { results: Awaited<ReturnType<typeof loadReport>>["results"] }) {
  return (
    <section>
      <header className="flex items-end justify-between gap-6">
        <div>
          <Eyebrow>Forgetting suite</Eyebrow>
          <h2 className="mt-3 max-w-2xl font-display text-h2 font-medium tracking-[-0.028em] text-ink">
            Each scenario plants a canary, calls the real delete API, and asks the
            agent if it can still see it.
          </h2>
        </div>
        <Link
          href="/app/lineage"
          className="hidden shrink-0 text-[13px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink md:inline"
        >
          Blast radius →
        </Link>
      </header>

      <div className="mt-10 border-b border-rule">
        {results.map((r) => (
          <ScenarioRow key={r.scenario} row={r} />
        ))}
      </div>
    </section>
  );
}

/* -------------------------------------------------------------- Lineage */

function Lineage({
  counts,
  backends,
}: {
  counts: Record<string, number>;
  backends: Awaited<ReturnType<typeof loadReport>>["coverage"]["backends"];
}) {
  const entries = Object.entries(counts);

  return (
    <section>
      <div className="grid gap-x-16 gap-y-14 lg:grid-cols-2">
        <div>
          <Eyebrow>Lineage</Eyebrow>
          <h2 className="mt-3 font-display text-h3 font-medium tracking-[-0.022em] text-ink">
            Captured this run
          </h2>
          <dl className="mt-8 divide-y divide-rule">
            {entries.map(([k, v]) => (
              <div
                key={k}
                className="flex items-baseline justify-between py-3.5 first:pt-0"
              >
                <dt className="text-body capitalize text-ink-2">{k}</dt>
                <dd className="font-mono text-[15px] tabular text-ink">{v}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div>
          <Eyebrow>Backends</Eyebrow>
          <h2 className="mt-3 font-display text-h3 font-medium tracking-[-0.022em] text-ink">
            Instrumented now
          </h2>
          <ul className="mt-8 divide-y divide-rule">
            {backends.map((b) => (
              <li key={b.backend} className="py-4 first:pt-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Dot tone="royal" />
                    <span className="font-mono text-[14px] text-ink">{b.backend}</span>
                  </div>
                  <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-ink-3">
                    {b.client_count} client{b.client_count === 1 ? "" : "s"}
                  </span>
                </div>
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  {b.capabilities.map((c) => (
                    <Chip key={c}>{c}</Chip>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------- Quote */

function Quote() {
  return (
    <section className="border-t border-rule pt-14">
      <Eyebrow>Why this matters</Eyebrow>
      <blockquote className="mt-6 max-w-3xl font-display text-[28px] font-light leading-[1.25] tracking-[-0.024em] text-ink-2 sm:text-[32px]">
        <span className="text-ink">
          &ldquo;Deleting an event doesn&rsquo;t remove the structured information
          derived out of it from the long term memory.&rdquo;
        </span>
      </blockquote>
      <footer className="mt-5 font-mono text-[11px] uppercase tracking-[0.16em] text-ink-3">
        AWS Bedrock AgentCore · official documentation
      </footer>
      <p className="mt-12 max-w-2xl text-lede text-ink-2">
        That sentence is true of nearly every agent-memory backend in production.
        This report is Ferryte&rsquo;s fix-and-verify surface: proof that a
        deleted memory is really gone — honest about what it cannot see.
      </p>
    </section>
  );
}

/* ------------------------------------------------------- shared primitives */

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
      {children}
    </span>
  );
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}
