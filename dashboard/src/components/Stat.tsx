import { type ReactNode } from "react";
import { Dot, type Tone } from "./Pill";

interface StatProps {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: Tone;
}

/**
 * One huge number, tiny label, optional dot.
 * No card, no border. Type & whitespace are the design.
 */
export function Stat({ label, value, hint, tone }: StatProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        {tone ? <Dot tone={tone} /> : null}
        <span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-ink-3">
          {label}
        </span>
      </div>
      <div className="font-mono text-[56px] font-light leading-[0.95] tracking-[-0.04em] text-ink tabular">
        {value}
      </div>
      {hint ? <div className="text-caption text-ink-3">{hint}</div> : null}
    </div>
  );
}

/**
 * A 4-up strip on large screens, 2-up on tablet, 1-up on mobile.
 * Each cell is separated by a single hairline so the strip reads like a stencil.
 */
export function StatRow({ children }: { children: ReactNode }) {
  return (
    <div
      className="
        grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4
        [&>*]:relative [&>*]:py-8 [&>*]:px-0
        sm:[&>*]:px-8 lg:[&>*]:px-10
        [&>*]:before:absolute [&>*]:before:bg-rule [&>*]:before:content-['']
        [&>*]:before:left-0 [&>*]:before:right-0 [&>*]:before:top-0 [&>*]:before:h-px
        sm:[&>*]:before:hidden
        sm:[&>*]:after:absolute sm:[&>*]:after:bg-rule sm:[&>*]:after:content-['']
        sm:[&>*]:after:top-2 sm:[&>*]:after:bottom-2 sm:[&>*]:after:left-0 sm:[&>*]:after:w-px
        sm:[&>*:nth-child(2n+1)]:after:hidden
        lg:[&>*:nth-child(2n+1)]:after:block
        lg:[&>*:nth-child(4n+1)]:after:hidden
      "
    >
      {children}
    </div>
  );
}
