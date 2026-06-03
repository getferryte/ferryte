import { Chip, Dot, type Tone } from "@/components/Pill";
import { loadReport } from "@/lib/report";

export default async function LineagePage() {
  const report = await loadReport();
  const blasts = report.results
    .flatMap((r) => r.blast.map((b) => ({ scenario: r.scenario, ...b })))
    .sort((a, b) => b.artifact_count - a.artifact_count);

  return (
    <div className="space-y-20 ui-fade">
      <header className="ui-rise">
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          Lineage
        </span>
        <h1 className="mt-6 max-w-[18ch] font-display text-h1 font-light leading-[1.02] tracking-tightest text-ink">
          Every source.
          <br />
          <span className="text-ink-3">Every descendant.</span>
        </h1>
        <p className="mt-8 max-w-xl text-lede text-ink-2">
          Ferryte traces what each source produced — raw memories, summaries,
          embeddings — and which retrievals each one influenced. When a source is
          revoked, this is the exact blast radius that must vanish.
        </p>
      </header>

      {blasts.length === 0 ? (
        <p className="text-body text-ink-2">
          No sources yet. Run{" "}
          <code className="font-mono text-ink">ferryte test</code>.
        </p>
      ) : (
        <section>
          <div className="border-b border-rule">
            {blasts.map((b, i) => (
              <BlastRow
                key={`${b.scenario}-${b.source_id}-${i}`}
                scenario={b.scenario}
                sourceId={b.source_id}
                artifactCount={b.artifact_count}
                retrievalCount={b.retrieval_count}
                minConfidence={b.min_confidence}
                artifacts={b.artifacts}
                retrievals={b.retrievals}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

type Artifact = {
  artifact_id: string;
  backend: string;
  kind: string;
  tenant_id?: string;
  content?: string;
};

type Retrieval = {
  backend: string;
  query: string;
  score?: number;
  tenant_id?: string;
  content?: string;
};

function BlastRow({
  scenario,
  sourceId,
  artifactCount,
  retrievalCount,
  minConfidence,
  artifacts,
  retrievals,
}: {
  scenario: string;
  sourceId: string;
  artifactCount: number;
  retrievalCount: number;
  minConfidence: number;
  artifacts: Artifact[];
  retrievals: Retrieval[];
}) {
  const leaking = artifactCount > 0;
  const tone: Tone = leaking ? "issue" : "ok";

  return (
    <article className="row-hover border-t border-rule px-2 py-7 sm:px-4">
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
        <div className="flex items-center gap-3 min-w-0">
          <Dot tone={tone} />
          <span className="font-mono text-[14px] text-ink truncate">{sourceId}</span>
          <Chip>{scenario}</Chip>
        </div>
        <div className="flex items-center gap-7 font-mono text-[12px] tabular">
          <Metric label="Artifacts" value={artifactCount} tone={leaking ? "issue" : undefined} />
          <Metric label="Retrievals" value={retrievalCount} />
          <Metric label="Confidence" value={minConfidence.toFixed(2)} />
        </div>
      </div>

      {artifacts.length > 0 && (
        <div className="mt-7">
          <SubHead label="Derived artifacts" count={artifacts.length} />
          <ul className="mt-3 divide-y divide-rule border-y border-rule">
            {artifacts.map((a) => (
              <li key={a.artifact_id} className="py-3.5">
                <div className="flex flex-wrap items-center gap-2 text-[11.5px]">
                  <span className="font-mono text-ink">{a.backend}</span>
                  <span className="text-ink-4">·</span>
                  <span className="font-mono text-ink-2">{a.kind}</span>
                  {a.tenant_id && (
                    <>
                      <span className="text-ink-4">·</span>
                      <span className="font-mono text-ink-3">
                        tenant {a.tenant_id}
                      </span>
                    </>
                  )}
                  <span className="ml-auto font-mono text-[10.5px] text-ink-3">
                    {a.artifact_id.slice(0, 10)}…
                  </span>
                </div>
                {a.content && (
                  <p className="mt-2 font-mono text-[12px] leading-relaxed text-ink-2">
                    {a.content.slice(0, 220)}
                    {a.content.length > 220 ? "…" : ""}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {retrievals.length > 0 && (
        <div className="mt-7">
          <SubHead label="Retrievals influenced" count={retrievals.length} />
          <ul className="mt-3 divide-y divide-rule border-y border-rule">
            {retrievals.slice(0, 6).map((r, j) => (
              <li
                key={j}
                className="flex items-baseline justify-between gap-4 py-3"
              >
                <span className="truncate font-mono text-[12.5px] text-ink-2">
                  {r.query}
                </span>
                <span className="shrink-0 font-mono text-[11px] tabular text-ink-3">
                  score {r.score?.toFixed(3) ?? "—"} · {r.backend}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}

function Metric({
  label,
  value,
  tone,
}: {
  label: string;
  value: number | string;
  tone?: Tone;
}) {
  return (
    <div className="flex flex-col items-end gap-1">
      <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-3">
        {label}
      </span>
      <span
        className={[
          "font-mono text-[14px] tabular",
          tone === "issue" ? "text-issue" : "text-ink",
        ].join(" ")}
      >
        {value}
      </span>
    </div>
  );
}

function SubHead({ label, count }: { label: string; count: number }) {
  return (
    <div className="flex items-baseline justify-between">
      <span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-ink-3">
        {label}
      </span>
      <span className="font-mono text-[11px] tabular text-ink-3">{count}</span>
    </div>
  );
}
