"use client";

import { AnimatePresence, motion, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";

const COMMAND = "pip install ferryte";

export function InstallTerminal() {
  const terminalRef = useRef<HTMLDivElement>(null);
  const inView = useInView(terminalRef, { once: true, amount: 0.45 });
  const [characters, setCharacters] = useState(0);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!inView || characters >= COMMAND.length) return;
    const timer = window.setTimeout(
      () => setCharacters((value) => value + 1),
      characters === 0 ? 260 : 52,
    );
    return () => window.clearTimeout(timer);
  }, [characters, inView]);

  const complete = characters >= COMMAND.length;

  async function copyCommand() {
    try {
      await navigator.clipboard.writeText(COMMAND);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access can be blocked in embedded browsers.
    }
  }

  return (
    <div
      id="install"
      ref={terminalRef}
      className="w-[min(92vw,510px)] overflow-hidden rounded-xl border border-white/[0.11] bg-[#07090a] font-mono text-[12px] shadow-[0_28px_90px_-42px_rgba(90,138,150,0.5)]"
      aria-label="Install Ferryte terminal"
    >
      <div className="flex h-10 items-center border-b border-white/[0.07] bg-white/[0.025] px-4">
        <div className="flex items-center gap-1.5" aria-hidden>
          <span className="size-2.5 rounded-full bg-[#ff6b63]/80" />
          <span className="size-2.5 rounded-full bg-[#d6aa4e]/80" />
          <span className="size-2.5 rounded-full bg-[#55a96b]/80" />
        </div>
        <span className="mx-auto -translate-x-4 text-[9px] uppercase tracking-[0.18em] text-ink-4">
          ferryte · install
        </span>
      </div>

      <div className="relative min-h-[126px] px-5 py-5 text-left">
        <button
          type="button"
          onClick={copyCommand}
          className="absolute right-4 top-4 rounded-md border border-white/[0.07] px-2 py-1 text-[8px] uppercase tracking-[0.16em] text-ink-4 transition hover:border-white/15 hover:text-ink-2"
          aria-label="Copy pip install ferryte"
        >
          {copied ? "Copied" : "Copy"}
        </button>

        <p className="flex items-center pr-16 text-[13px] text-ink">
          <span className="mr-3 text-brand-mid">›</span>
          <span>{COMMAND.slice(0, characters)}</span>
          {!complete ? (
            <motion.span
              aria-hidden
              animate={{ opacity: [1, 0, 1] }}
              transition={{ duration: 0.8, repeat: Number.POSITIVE_INFINITY }}
              className="ml-0.5 inline-block h-4 w-[1.5px] bg-brand-light"
            />
          ) : null}
        </p>

        <AnimatePresence>
          {complete ? (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.35 }}
              className="mt-5 space-y-2 text-[10.5px]"
            >
              <p className="text-ink-3">
                <span className="mr-2 text-ok">✓</span>
                Ferryte installed
              </p>
              <motion.p
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.62, duration: 0.35 }}
                className="text-ink-4"
              >
                <span className="mr-2 text-brand-mid">→</span>
                Next: ferryte why --help
              </motion.p>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>
    </div>
  );
}
