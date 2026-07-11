"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";

const EASE = [0.22, 1, 0.36, 1] as const;

export type TerminalLine =
  | { kind: "command"; text: string }
  | { kind: "output"; text: string; tone?: "default" | "muted" | "issue" | "brand" }
  | { kind: "spacer" };

interface TerminalProps {
  title: string;
  tag: string;
  tone: "bad" | "good";
  lines: TerminalLine[];
  /** seconds before the first line appears once the block is in view */
  startDelay?: number;
  /** seconds between line reveals */
  perLineDelay?: number;
}

/**
 * Animated terminal block — lines fade + lift in sequence when scrolled
 * into view. Designed for the landing-page "watch it leak" moment.
 */
export function Terminal({
  title,
  tag,
  tone,
  lines,
  startDelay = 0.25,
  perLineDelay = 0.16,
}: TerminalProps) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.25 });

  return (
    <div
      ref={ref}
      className={["term p-6 sm:p-7", tone === "bad" ? "opacity-[0.94]" : "term-glow"].join(" ")}
    >
      <header className="mb-5 flex items-center justify-between">
        <span className="flex items-center gap-3">
          <span className="term-dots" aria-hidden>
            <i />
            <i />
            <i />
          </span>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
            {title}
          </span>
        </span>
        <span
          className={[
            "inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.18em]",
            tone === "bad" ? "text-issue" : "text-ok",
          ].join(" ")}
        >
          <span
            className={["dot", tone === "bad" ? "dot-issue" : "dot-ok"].join(" ")}
          />
          {tag}
        </span>
      </header>

      <div className="font-mono text-[12.5px] leading-[1.65]">
        {lines.map((line, i) => (
          <Line
            key={i}
            line={line}
            inView={inView}
            delay={startDelay + i * perLineDelay}
          />
        ))}
      </div>
    </div>
  );
}

function Line({
  line,
  inView,
  delay,
}: {
  line: TerminalLine;
  inView: boolean;
  delay: number;
}) {
  if (line.kind === "spacer") {
    return <div className="h-3" aria-hidden />;
  }

  const tone =
    line.kind === "output" ? line.tone ?? "default" : "default";
  const colorClass =
    line.kind === "command"
      ? "text-ink"
      : tone === "issue"
        ? "ph-issue"
        : tone === "brand"
          ? "ph-royal"
          : tone === "muted"
            ? "text-ink-3"
            : "text-ink-2";

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 4 }}
      transition={{ duration: 0.36, delay, ease: EASE }}
      className={colorClass}
      style={{ whiteSpace: "pre-wrap" }}
    >
      {line.kind === "command" ? (
        <>
          <span className="select-none text-royal">› </span>
          {line.text}
        </>
      ) : (
        line.text
      )}
    </motion.div>
  );
}
