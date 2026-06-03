import { Dot, type Tone } from "./Pill";
import type { ScenarioResultRow } from "../lib/report";

function severityToTone(s: ScenarioResultRow["severity"]): Tone {
  if (s === "pass") return "ok";
  if (s === "warn") return "pending";
  return "issue";
}

function severityLabel(s: ScenarioResultRow["severity"], passed: boolean): string {
  if (s === "fail") return "failed";
  if (s === "warn") return "warnings";
  return passed ? "verified" : "passed";
}

function humanizeScenario(id: string) {
  return id
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/**
 * One scenario per row. No card. Hairline at the top.
 * Left: scenario name + severity + headline finding.
 * Right: a few tabular metrics, tight and quiet.
 */
export function ScenarioRow({ row }: { row: ScenarioResultRow }) {
  const tone = severityToTone(row.severity);
  const topFinding = row.findings[0];

  return (
    <article className="row-hover grid grid-cols-12 items-start gap-x-8 gap-y-3 border-t border-rule px-2 py-7 sm:px-4">
      {/* Status + name */}
      <div className="col-span-12 lg:col-span-5">
        <div className="flex items-center gap-3">
          <Dot tone={tone} />
          <h3 className="font-display text-[20px] font-medium tracking-[-0.024em] text-ink">
            {humanizeScenario(row.scenario)}
          </h3>
        </div>
        <p className="mt-2 max-w-md text-body text-ink-2">
          {topFinding ? topFinding.summary : "No findings."}
        </p>
        {topFinding ? (
          <p className="mt-1.5 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-3">
            {topFinding.code}
          </p>
        ) : null}
      </div>

      {/* Quiet tabular metrics */}
      <dl className="col-span-12 grid grid-cols-2 gap-y-3 lg:col-span-7 lg:grid-cols-4">
        <Metric label="Status" value={severityLabel(row.severity, row.passed)} tone={tone} />
        <Metric label="Seeded" value={row.artifacts_seeded.toLocaleString()} />
        <Metric label="Deleted" value={row.artifacts_deleted.toLocaleString()} />
        <Metric label="Duration" value={`${row.duration_ms.toFixed(0)} ms`} />
      </dl>
    </article>
  );
}

function Metric({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: Tone;
}) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-3">
        {label}
      </dt>
      <dd
        className={[
          "font-mono text-[15px] tabular",
          tone === "ok"
            ? "text-ok"
            : tone === "issue"
              ? "text-issue"
              : tone === "pending"
                ? "text-pending"
                : "text-ink",
        ].join(" ")}
      >
        {value}
      </dd>
    </div>
  );
}
