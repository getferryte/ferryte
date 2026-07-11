"use client";

/**
 * The landing. One living centerpiece, then an explorable evidence field.
 *
 * Composition: an editorial serif wordmark the width of the page, with the
 * Memory Bloom — a ferrite-core plane stitched from ~9,000 pixels — blooming
 * over its lower half. The bloom warps under the cursor and breathes on its
 * own. Below: two lines of copy, a constellation of ring-links, one command,
 * one status line, and primary-source proof that the category is real.
 */

import { EvidenceOrbit } from "@/components/EvidenceOrbit";
import { InstallTerminal } from "@/components/InstallTerminal";
import { MemoryBloom } from "@/components/MemoryBloom";
import { Reveal } from "@/components/motion/Motion";
import Image from "next/image";
import Link from "next/link";
import { useRef } from "react";

const LINKS = [
  { label: "Why it exists", href: "/manifesto" },
  { label: "How it works", href: "/product" },
  { label: "The Memory Report", href: "/benchmark" },
  { label: "$500 Audit", href: "/audit" },
  { label: "Pricing", href: "/pricing" },
  { label: "GitHub", href: "https://github.com/getferryte/ferryte" },
];

export default function Landing() {
  const bloomRef = useRef<HTMLDivElement>(null);

  return (
    <main className="relative flex min-h-screen flex-col overflow-hidden [font-family:var(--font-fraunces),Georgia,serif]">
      <div className="aurora" aria-hidden />

      <a
        href="https://github.com/getferryte/ferryte"
        target="_blank"
        rel="noreferrer"
        aria-label="Open Ferryte on GitHub"
        className="group absolute right-10 top-12 z-30 hidden h-10 items-center justify-center gap-2.5 rounded-full border border-white/[0.09] bg-black/20 px-4 text-ink-3 backdrop-blur-md transition duration-300 hover:-translate-y-0.5 hover:border-brand-light/25 hover:bg-white/[0.035] hover:text-ink sm:inline-flex"
      >
        <svg
          aria-hidden
          viewBox="0 0 24 24"
          className="size-[17px] fill-current"
        >
          <path d="M12 .8a11.4 11.4 0 0 0-3.6 22.2c.57.1.78-.24.78-.55v-2.13c-3.18.69-3.85-1.35-3.85-1.35-.52-1.32-1.27-1.67-1.27-1.67-1.04-.71.08-.7.08-.7 1.15.08 1.75 1.18 1.75 1.18 1.02 1.75 2.68 1.24 3.33.95.1-.74.4-1.24.73-1.53-2.54-.29-5.21-1.27-5.21-5.64 0-1.25.45-2.27 1.18-3.07-.12-.29-.51-1.45.11-3.02 0 0 .96-.31 3.14 1.17A10.9 10.9 0 0 1 12 6.25c.97 0 1.93.13 2.84.38 2.18-1.48 3.14-1.17 3.14-1.17.62 1.57.23 2.73.11 3.02.73.8 1.18 1.82 1.18 3.07 0 4.38-2.68 5.34-5.23 5.63.41.36.78 1.06.78 2.14v3.13c0 .31.21.66.79.55A11.4 11.4 0 0 0 12 .8Z" />
        </svg>
        <span className="hidden text-[11px] font-semibold tracking-[0.04em] sm:inline">
          Explore on GitHub
        </span>
        <span className="hidden transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 sm:inline">
          ↗
        </span>
      </a>

      {/* ------------------------------------------------------- the pill */}
      <div className="relative z-20 mx-auto pt-12 sm:pt-14">
        <Reveal delay={0.1}>
          <span className="inline-flex items-center gap-2.5 rounded-full border border-rule-2/80 bg-black/40 px-4 py-1.5 text-[11px] font-medium uppercase tracking-[0.16em] text-ink-2 backdrop-blur">
            <Image
              src="/icon.png"
              alt=""
              width={16}
              height={16}
              aria-hidden
              className="size-4 rounded-full object-cover opacity-90 ring-1 ring-white/10"
            />
            Memory debugging for AI agents
          </span>
        </Reveal>
      </div>

      {/* ------------------------------- the wordmark, and the bloom on it */}
      <header className="relative z-10 mx-auto mt-6 w-full max-w-[1400px] px-3 text-center sm:mt-8">
        {/* print-texture halo behind everything */}
        <div
          aria-hidden
          className="halftone absolute left-1/2 top-[8%] -z-10 h-[110%] w-[min(120vw,1100px)] -translate-x-1/2"
        />
        <Reveal delay={0.22} duration={1.2}>
          <h1
            aria-label="Ferryte"
            className="wordmark mx-auto grid w-[82vw] max-w-[1180px] select-none grid-cols-7 font-serif text-[20.5vw] uppercase leading-[0.92] lg:text-[266px]"
          >
            {"FERRYTE".split("").map((letter, index) => (
              <span
                key={`${letter}-${index}`}
                aria-hidden
                className={index < 4 ? "wordmark-solid" : "wordmark-fade"}
              >
                {letter}
              </span>
            ))}
          </h1>
        </Reveal>

        <EvidenceOrbit targetRef={bloomRef} />

        {/* the centerpiece — in front of the letters, like a pressed bloom */}
        <Reveal
          delay={0.4}
          duration={1.4}
          className="pointer-events-none relative z-10 mx-auto -mt-[13vw] h-[min(94vw,620px)] w-[min(94vw,620px)] lg:-mt-[168px]"
        >
          <div ref={bloomRef} className="h-full w-full">
            <MemoryBloom className="h-full w-full" />
          </div>
        </Reveal>

        {/* The historical reference, explained instead of presented as a museum code. */}
        <Reveal delay={0.8} className="relative z-20 -mt-2">
          <p className="text-[12px] font-medium tracking-[0.04em] text-ink-3">
            Memory was once wired by hand.
          </p>
          <p className="mt-1 text-[12px] italic tracking-[0.025em] text-ink-3">
            Ferryte makes every agent memory traceable again.
          </p>
        </Reveal>
      </header>

      {/* ------------------------------------------------ the words (few) */}
      <div className="relative z-10 mx-auto mt-10 max-w-xl px-6 text-center sm:mt-12">
        <Reveal delay={0.6}>
          <p className="text-[17px] leading-relaxed text-ink-2 sm:text-[19px]">
            Your agent said something wrong.{" "}
            <span className="text-ink">Ask it why.</span>
          </p>
          <p className="mt-2 text-[13.5px] leading-relaxed text-ink-3">
            One line to instrument. Every answer traced to the exact memory
            that caused it — and the fix, proven.
          </p>
        </Reveal>
      </div>

      {/* --------------------------------------------- the constellation */}
      <nav
        aria-label="Site"
        className="pointer-events-auto relative z-20 mx-auto mt-12 flex max-w-4xl flex-wrap items-center justify-center gap-x-9 gap-y-4 px-6 sm:mt-14"
      >
        {LINKS.map((link, index) => {
          const external = link.href.startsWith("http");
          return (
            <Reveal key={link.href} delay={0.9 + index * 0.06}>
              {external ? (
                <a
                  href={link.href}
                  target="_blank"
                  rel="noreferrer"
                  className="ring-link"
                >
                  {link.label}
                </a>
              ) : (
                <Link href={link.href} className="ring-link">
                  {link.label}
                </Link>
              )}
            </Reveal>
          );
        })}
      </nav>

      {/* ------------------------------------------------- the last line */}
      <footer className="relative z-10 mx-auto mt-12 flex w-full max-w-4xl flex-col items-center gap-6 px-6 pb-12 sm:mt-14">
        <Reveal delay={1.2}>
          <InstallTerminal />
        </Reveal>
        <Reveal delay={1.35}>
          <p className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-[11px] font-medium uppercase tracking-[0.13em] text-ink-4">
            <span className="inline-flex items-center gap-2">
              <span className="dot dot-ok" />
              <span className="text-ink-3">Engine operational</span>
            </span>
            <span>v0.2.3</span>
            <span>source-available · BSL 1.1 → Apache 2.0</span>
            <span>ferryte.dev</span>
          </p>
        </Reveal>
      </footer>
    </main>
  );
}
