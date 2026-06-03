"use client";

import { useState } from "react";

interface CopyableCommandProps {
  command: string;
  prefix?: string;
  label?: string;
}

/**
 * A code-styled, copy-to-clipboard install/run command.
 * Click anywhere on the surface to copy; affordance switches to "Copied".
 */
export function CopyableCommand({
  command,
  prefix = "›",
  label = "Copy",
}: CopyableCommandProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      /* ignore — clipboard blocked */
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="
        group relative inline-flex items-center gap-3 rounded-md
        border border-rule bg-surface px-4 py-2.5
        font-mono text-[13px] text-ink
        transition-colors duration-fast ease-out
        hover:border-rule-2 hover:bg-surface-2
        focus-visible:outline-none
      "
    >
      <span className="text-royal">{prefix}</span>
      <span className="select-all">{command}</span>
      <span
        className={[
          "ml-2 font-mono text-[10.5px] uppercase tracking-[0.18em]",
          copied ? "text-royal" : "text-ink-3 group-hover:text-ink-2",
        ].join(" ")}
        aria-live="polite"
      >
        {copied ? "Copied" : label}
      </span>
    </button>
  );
}
