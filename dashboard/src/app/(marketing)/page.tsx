"use client";

import Link from "next/link";
import { motion } from "framer-motion";

import { CopyableCommand } from "@/components/CopyableCommand";
import {
  Magnetic,
  Reveal,
  RevealOnScroll,
  Stagger,
  StaggerItem,
  WordReveal,
} from "@/components/motion/Motion";

const EASE = [0.22, 1, 0.36, 1] as const;

export default function Landing() {
  return (
    <main>
      <Hero />
      <ProofStrip />
      <CommandStrip />
      <ApplyStrip />
    </main>
  );
}

/* ---------------------------------------------------------------- Hero */

function Hero() {
  return (
    <section className="relative flex min-h-[calc(100vh-73px)] flex-col items-start justify-center px-8 sm:px-12 lg:px-20">
      {/* ambient royal glow behind the headline */}
      <motion.div
        aria-hidden
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 2.4, ease: EASE }}
        className="pointer-events-none absolute -top-32 left-1/4 -z-10 h-[600px] w-[600px] rounded-full"
        style={{
          background:
            "radial-gradient(circle, rgba(126,167,176,0.18) 0%, rgba(13,61,78,0.08) 45%, rgba(13,61,78,0) 72%)",
        }}
      />

      <div className="mx-auto w-full max-w-6xl">
        <Reveal delay={0.1} className="mb-12 flex items-center gap-2.5">
          <span className="dot dot-royal dot-live" />
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
            Open beta · MIT
          </span>
        </Reveal>

        <WordReveal
          as="h1"
          text="Forgetting,"
          delay={0.25}
          staggerDelay={0.08}
          className="font-display block max-w-[14ch] text-[64px] font-light leading-[0.96] tracking-tightest text-ink sm:text-[96px] lg:text-[128px]"
        />
        <WordReveal
          as="h1"
          text="verified."
          delay={0.55}
          staggerDelay={0.08}
          className="font-display -mt-2 block max-w-[14ch] text-[64px] font-light leading-[0.96] tracking-tightest text-ink-3 sm:text-[96px] lg:text-[128px]"
        />

        <Reveal delay={1.1} className="mt-12 max-w-xl">
          <p className="text-lede text-ink-2 sm:text-[20px]">
            The deterministic verification layer for AI agent memory.
          </p>
        </Reveal>

        <Reveal delay={1.35} className="mt-10 flex flex-wrap items-center gap-4">
          <Magnetic>
            <Link
              href="/manifesto"
              className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2"
            >
              Read the manifesto
              <span aria-hidden>→</span>
            </Link>
          </Magnetic>
          <CopyableCommand command="pip install ferryte" />
          <Link
            href="https://github.com/getferryte/ferryte"
            className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
          >
            GitHub →
          </Link>
        </Reveal>
      </div>

      {/* scroll cue */}
      <Reveal
        delay={1.9}
        duration={1.2}
        className="absolute bottom-10 left-1/2 -translate-x-1/2"
      >
        <ScrollCue />
      </Reveal>
    </section>
  );
}

function ScrollCue() {
  return (
    <motion.div
      animate={{ y: [0, 6, 0] }}
      transition={{ duration: 2, ease: EASE, repeat: Infinity }}
      className="flex flex-col items-center gap-2 text-ink-3"
    >
      <span className="font-mono text-[10px] uppercase tracking-[0.22em]">
        Scroll for proof
      </span>
      <svg
        width="14"
        height="22"
        viewBox="0 0 14 22"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect x="0.5" y="0.5" width="13" height="21" rx="6.5" stroke="currentColor" />
        <motion.circle
          cx="7"
          cy="7"
          r="1.5"
          fill="currentColor"
          animate={{ cy: [7, 14, 7] }}
          transition={{ duration: 2, ease: EASE, repeat: Infinity }}
        />
      </svg>
    </motion.div>
  );
}

/* --------------------------------------------------------- Proof strip */

const QUOTES = [
  { vendor: "AWS Bedrock AgentCore", line: "Deletion does not propagate to derivations." },
  { vendor: "Zep documentation", line: "Episode deletion leaves shared summaries intact." },
  { vendor: "OWASP Agentic Top 10", line: "Memory poisoning · ASI06 · Dec 2025." },
];

function ProofStrip() {
  return (
    <section className="border-t border-rule/70 px-8 py-32 sm:px-12 lg:px-20 lg:py-40">
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
            The platform vendors said it themselves
          </span>
        </RevealOnScroll>

        <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
          <h2 className="font-display text-[36px] font-light leading-[1.1] tracking-[-0.028em] text-ink sm:text-[52px] lg:text-[64px]">
            Almost nobody tests for the leak in CI.
            <br />
            <span className="text-ink-3">You find out from a customer.</span>
          </h2>
        </RevealOnScroll>

        <Stagger
          className="mt-16 grid gap-4 sm:grid-cols-3"
          delay={0.2}
          staggerDelay={0.1}
        >
          {QUOTES.map((q) => (
            <StaggerItem key={q.vendor}>
              <div className="rounded-lg border border-rule bg-surface p-6 transition-colors duration-base ease-out hover:border-rule-2">
                <p className="font-display text-[18px] font-light leading-[1.35] tracking-[-0.012em] text-ink">
                  {q.line}
                </p>
                <p className="mt-5 font-mono text-[10.5px] uppercase tracking-[0.18em] text-ink-3">
                  {q.vendor}
                </p>
              </div>
            </StaggerItem>
          ))}
        </Stagger>

        <RevealOnScroll delay={0.3} className="mt-12">
          <Link
            href="/manifesto"
            className="inline-flex items-center gap-1.5 text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
          >
            Read why this matters
            <span aria-hidden className="transition-transform duration-base ease-out group-hover:translate-x-0.5">
              →
            </span>
          </Link>
        </RevealOnScroll>
      </div>
    </section>
  );
}

/* ----------------------------------------------------- Command strip */

function CommandStrip() {
  return (
    <section className="border-t border-rule/70 px-8 py-32 sm:px-12 lg:px-20 lg:py-40">
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
            Run it
          </span>
        </RevealOnScroll>

        <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
          <h2 className="font-display text-[36px] font-light leading-[1.1] tracking-[-0.028em] text-ink sm:text-[52px] lg:text-[64px]">
            One line. Zero accounts.
            <br />
            <span className="text-ink-3">Catch the leak in thirty seconds.</span>
          </h2>
        </RevealOnScroll>

        <RevealOnScroll delay={0.25} className="mt-12">
          <div className="flex flex-wrap items-center gap-3">
            <CopyableCommand command="pip install ferryte" />
            <CopyableCommand command="ferryte test" />
          </div>
        </RevealOnScroll>

        <RevealOnScroll delay={0.4} className="mt-12">
          <Link
            href="/product"
            className="inline-flex items-center gap-1.5 text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
          >
            See exactly how it works
            <span aria-hidden>→</span>
          </Link>
        </RevealOnScroll>
      </div>
    </section>
  );
}

/* ------------------------------------------------------- Apply strip */

function ApplyStrip() {
  return (
    <section className="brand-hairline relative border-t border-rule/70 px-8 py-32 sm:px-12 lg:px-20 lg:py-44">
      <div className="mx-auto max-w-6xl">
        <RevealOnScroll>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-royal">
            Design partners · five seats
          </span>
        </RevealOnScroll>

        <RevealOnScroll delay={0.1} className="mt-8 max-w-4xl">
          <h2 className="font-display text-[40px] font-light leading-[1.04] tracking-[-0.03em] text-ink sm:text-[64px] lg:text-[80px]">
            Six months free.
            <br />
            <span className="text-ink-3">Named engineer. Shape the roadmap.</span>
          </h2>
        </RevealOnScroll>

        <RevealOnScroll delay={0.25} className="mt-10 max-w-xl">
          <p className="text-lede text-ink-2">
            Ferryte Cloud goes private beta with five companies running multi-tenant
            memory in production. We pair an engineer with your team and wire the
            first integration in a day.
          </p>
        </RevealOnScroll>

        <RevealOnScroll delay={0.4} className="mt-10 flex flex-wrap items-center gap-4">
          <Magnetic>
            <a
              href="mailto:hello@ferryte.dev?subject=Ferryte%20design%20partner&body=Stack%3A%20%0ATenants%3A%20%0AMemory%20backend(s)%3A%20%0ALeak%20you%E2%80%99re%20worried%20about%3A%20"
              className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2"
            >
              Email hello@ferryte.dev
              <span aria-hidden>→</span>
            </a>
          </Magnetic>
          <Link
            href="/pricing"
            className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
          >
            See Core, Cloud, Enterprise →
          </Link>
        </RevealOnScroll>
      </div>
    </section>
  );
}
