"use client";

/**
 * FooterWhy — the easter egg. `ferryte why "you're still scrolling"`.
 * Click it and attribution runs on you. Costs ~20 lines; earns screenshots.
 */

import { useState } from "react";

export function FooterWhy() {
  const [ran, setRan] = useState(false);

  return (
    <div className="mt-6 font-mono text-[11.5px] leading-[1.8]">
      <button
        type="button"
        onClick={() => setRan(true)}
        className="text-ink-4 transition-colors duration-fast ease-out hover:text-ink-3"
        aria-expanded={ran}
      >
        <span className="select-none text-royal/60">› </span>
        ferryte why &quot;you&rsquo;re still scrolling&quot;
      </button>
      {ran && (
        <div className="ui-rise" aria-live="polite">
          <div className="ph-royal">#1 genuine-interest · conf 0.97</div>
          <div className="text-ink-4">
            {"   "}retrieved 1× into context · shared span: &quot;memory debugging&quot;
          </div>
          <div className="text-ink-3">
            {"   "}fix: <span className="text-ink-2">pip install ferryte</span>
          </div>
        </div>
      )}
    </div>
  );
}
