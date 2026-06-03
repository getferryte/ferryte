import { type ReactNode } from "react";

export type Tone = "royal" | "ok" | "pending" | "issue" | "neutral";

const dotClass: Record<Tone, string> = {
  royal: "dot-royal",
  ok: "dot-ok",
  pending: "dot-pending",
  issue: "dot-issue",
  neutral: "dot-neutral",
};

const inkClass: Record<Tone, string> = {
  royal: "text-royal",
  ok: "text-ok",
  pending: "text-pending",
  issue: "text-issue",
  neutral: "text-ink-2",
};

/** Bare dot. The entire status vocabulary. */
export function Dot({ tone, live = false }: { tone: Tone; live?: boolean }) {
  return <span className={`dot ${dotClass[tone]} ${live ? "dot-live" : ""}`} />;
}

/** Tiny label-style pill, no background, just dot + label. */
export function StatusLabel({
  tone,
  children,
  live = false,
}: {
  tone: Tone;
  children: ReactNode;
  live?: boolean;
}) {
  return (
    <span className="inline-flex items-center gap-2 font-mono text-[10.5px] uppercase tracking-[0.16em] text-ink-2">
      <Dot tone={tone} live={live} />
      <span className={inkClass[tone]}>{children}</span>
    </span>
  );
}

/** A subtle outlined chip — used very sparingly. */
export function Chip({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-rule px-2.5 py-1 font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink-2">
      <Dot tone={tone} />
      {children}
    </span>
  );
}
