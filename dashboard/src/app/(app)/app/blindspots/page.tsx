import { Dot, type Tone } from "@/components/Pill";
import { loadReport } from "@/lib/report";

export default async function BlindspotsPage() {
  const report = await loadReport();
  return (
    <div className="space-y-20 ui-fade">
      <header className="ui-rise">
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          Blind spots
        </span>
        <h1 className="mt-6 max-w-[18ch] font-display text-h1 font-light leading-[1.02] tracking-tightest text-ink">
          What Ferryte
          <br />
          <span className="text-ink-3">cannot verify.</span>
        </h1>
        <p className="mt-8 max-w-xl text-lede text-ink-2">
          Ferryte does not pretend. When the backend can&rsquo;t tell us what was
          derived from a source — un-instrumented stores, laundered paraphrases,
          external caches — we say so. A pass means something. A blind spot is
          something to act on, not something to discover from a customer.
        </p>
      </header>

      <BlindSection
        eyebrow="Runtime"
        title="Observed during this run"
        emptyMessage="No runtime blind spots observed."
        items={report.coverage.blindspots.map((b) => ({
          tone: "pending",
          backend: b.backend,
          kind: b.kind,
          detail: b.detail,
        }))}
      />

      <BlindSection
        eyebrow="Structural"
        title="Adapter capability gaps"
        emptyMessage="Every instrumented backend supports the full Ferryte capability set."
        items={report.coverage.structural_gaps.map((g) => ({
          tone: "neutral",
          backend: g.backend,
          kind: g.capability,
          detail: g.detail,
        }))}
      />
    </div>
  );
}

function BlindSection({
  eyebrow,
  title,
  emptyMessage,
  items,
}: {
  eyebrow: string;
  title: string;
  emptyMessage: string;
  items: { tone: Tone; backend: string; kind: string; detail: string }[];
}) {
  return (
    <section>
      <header className="flex items-baseline justify-between gap-6">
        <div>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
            {eyebrow}
          </span>
          <h2 className="mt-3 font-display text-h3 font-medium tracking-[-0.022em] text-ink">
            {title}
          </h2>
        </div>
        <span className="font-mono text-[11px] tabular text-ink-3">
          {items.length}
        </span>
      </header>

      {items.length === 0 ? (
        <p className="mt-8 text-body text-ink-2">{emptyMessage}</p>
      ) : (
        <ul className="mt-8 divide-y divide-rule border-y border-rule">
          {items.map((it, i) => (
            <li key={i} className="row-hover px-2 py-6 sm:px-4">
              <div className="flex items-center gap-3">
                <Dot tone={it.tone} />
                <span className="font-mono text-[14px] text-ink">{it.backend}</span>
                <span className="text-ink-4">·</span>
                <span className="font-mono text-[13px] text-ink-2">{it.kind}</span>
              </div>
              <p className="mt-3 max-w-3xl text-body text-ink-2">{it.detail}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
