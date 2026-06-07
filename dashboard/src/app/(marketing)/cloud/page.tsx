"use client";

import Link from "next/link";

import {
  Magnetic,
  Reveal,
  RevealOnScroll,
  Stagger,
  StaggerItem,
} from "@/components/motion/Motion";
import { WaitlistForm } from "@/components/WaitlistForm";

const BOOKING_URL =
  process.env.NEXT_PUBLIC_BOOKING_URL ||
  "mailto:hello@ferryte.dev?subject=Ferryte%20design-partner%20call&body=Stack%3A%20%0ATenants%3A%20%0AMemory%20backend(s)%3A%20%0ALeak%20you%E2%80%99re%20worried%20about%3A%20%0APreferred%20times%3A%20";

export default function CloudPage() {
  return (
    <main className="px-8 sm:px-12 lg:px-20">
      <div className="mx-auto max-w-6xl">
        <Header />
        <HowItHelps />
        <Waitlist />
        <BookCall />
      </div>
    </main>
  );
}

/* ---------------------------------------------------------- Header */

function Header() {
  return (
    <section className="pt-28 pb-12 sm:pt-36 sm:pb-16">
      <Reveal delay={0.05}>
        <div className="flex items-center gap-2.5">
          <span className="dot dot-royal dot-live" />
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
            Cloud + Enterprise · in private development
          </span>
        </div>
      </Reveal>

      <Reveal delay={0.18} className="mt-10 max-w-5xl">
        <h1 className="font-display text-[42px] font-light leading-[1.03] tracking-[-0.04em] text-ink sm:text-[68px] lg:text-[88px]">
          The test proves it once.
          <br />
          <span className="text-ink-3">We&rsquo;ll prove it forever.</span>
        </h1>
      </Reveal>

      <Reveal delay={0.4} className="mt-8 max-w-2xl">
        <p className="text-lede text-ink-2">
          The free CLI shows your agent leaked deleted data today. Ferryte Cloud
          will watch every deploy and alert you the moment a leak re-opens —
          and Enterprise will hand your compliance team the signed receipt a
          regulator actually accepts. Neither is launched yet. We&rsquo;re
          building them with five design partners. Get in early.
        </p>
      </Reveal>

      <Reveal delay={0.55} className="mt-9 flex flex-wrap items-center gap-4">
        <Magnetic>
          <a
            href="#waitlist"
            className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2"
          >
            Join the waitlist
            <span aria-hidden>→</span>
          </a>
        </Magnetic>
        <a
          href="#book-a-call"
          className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
        >
          Book a design-partner call →
        </a>
      </Reveal>
    </section>
  );
}

/* ---------------------------------------------------------- How it helps */

const TIERS = [
  {
    name: "Cloud",
    audience: "For engineering teams",
    tone: "royal" as const,
    line: "Continuous proof the leak stays closed.",
    blurb:
      "Push every CI run to a hosted project. We keep the history, diff each run, and ping Slack or PagerDuty the second a scenario that used to pass starts leaking again.",
    bullets: [
      "Hosted run history + per-tenant blast radius",
      "Regression alerts when a leak re-opens",
      "Slack · PagerDuty · Linear · webhook",
      "Status badge for your repo",
    ],
  },
  {
    name: "Enterprise",
    audience: "For security & compliance",
    tone: "pending" as const,
    line: "Evidence a regulator accepts.",
    blurb:
      "Everything in Cloud, self-hosted in your VPC, plus the cryptographically signed attestation that proves a deletion request was honored everywhere — the artifact GDPR Article 17 and SOC 2 reviews ask for.",
    bullets: [
      "Signed GDPR / CCPA deletion attestations",
      "SSO + RBAC + immutable audit logs",
      "Self-hosted / VPC deployment",
      "Premium adapters + support SLA",
    ],
  },
];

function HowItHelps() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-24">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          How we&rsquo;ll help you
        </span>
      </RevealOnScroll>

      <Stagger className="mt-10 grid gap-5 lg:grid-cols-2" staggerDelay={0.12}>
        {TIERS.map((t) => (
          <StaggerItem key={t.name}>
            <article className="flex h-full flex-col rounded-xl border border-rule bg-surface p-8 transition-colors duration-base ease-out hover:border-rule-2">
              <header className="flex items-center justify-between">
                <h3 className="font-display text-[28px] font-light tracking-[-0.022em] text-ink">
                  {t.name}
                </h3>
                <span className="inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.16em] text-ink-3">
                  <span
                    className={`dot ${t.tone === "royal" ? "dot-royal" : "dot-pending"}`}
                  />
                  {t.audience}
                </span>
              </header>

              <p className="mt-5 font-display text-[19px] font-light tracking-[-0.014em] text-ink sm:text-[22px]">
                {t.line}
              </p>

              <p className="mt-4 text-body text-ink-2">{t.blurb}</p>

              <ul className="mt-7 flex flex-col gap-3 border-t border-rule/60 pt-6 text-body text-ink-2">
                {t.bullets.map((b) => (
                  <li
                    key={b}
                    className="before:mr-3 before:text-royal before:content-['+']"
                  >
                    {b}
                  </li>
                ))}
              </ul>
            </article>
          </StaggerItem>
        ))}
      </Stagger>

      <RevealOnScroll delay={0.18} className="mt-8">
        <p className="text-caption text-ink-3">
          The free, source-available engine ships today —{" "}
          <Link
            href="/pricing"
            className="text-ink-2 underline-offset-4 hover:text-ink hover:underline"
          >
            see exactly where the free / paid boundary sits
          </Link>
          .
        </p>
      </RevealOnScroll>
    </section>
  );
}

/* ---------------------------------------------------------- Waitlist */

function Waitlist() {
  return (
    <section
      id="waitlist"
      className="brand-hairline relative border-t border-rule/60 py-20 lg:py-28"
    >
      <div className="grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
        <div>
          <RevealOnScroll>
            <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-royal">
              Waitlist · design-partner cohort
            </span>
          </RevealOnScroll>

          <RevealOnScroll delay={0.1} className="mt-7 max-w-xl">
            <h2 className="font-display text-[34px] font-light leading-[1.05] tracking-[-0.03em] text-ink sm:text-[48px]">
              Shape it before
              <br />
              <span className="text-ink-3">we ship it.</span>
            </h2>
          </RevealOnScroll>

          <RevealOnScroll delay={0.2} className="mt-7 max-w-md">
            <p className="text-body text-ink-2">
              Five teams running multi-tenant agent memory will define what
              Cloud becomes. Design partners get the founder paired with their
              team for the first integration, and six months of Cloud free once
              it ships. Tell us your stack — we read every entry by hand.
            </p>
          </RevealOnScroll>
        </div>

        <RevealOnScroll delay={0.15}>
          <WaitlistForm tier="cloud" />
        </RevealOnScroll>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------- Book a call */

function BookCall() {
  return (
    <section
      id="book-a-call"
      className="border-t border-rule/60 py-20 lg:py-28"
    >
      <div className="flex flex-col items-start justify-between gap-8 lg:flex-row lg:items-center">
        <div className="max-w-2xl">
          <RevealOnScroll>
            <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
              Prefer to talk?
            </span>
          </RevealOnScroll>
          <RevealOnScroll delay={0.1} className="mt-6">
            <h2 className="font-display text-[30px] font-light leading-[1.08] tracking-[-0.028em] text-ink sm:text-[40px]">
              Book 20 minutes with the founder.
            </h2>
          </RevealOnScroll>
          <RevealOnScroll delay={0.18} className="mt-5 max-w-xl">
            <p className="text-body text-ink-2">
              Bring your architecture. We&rsquo;ll map where your agent&rsquo;s
              memory most likely leaks deleted data, and whether the
              design-partner cohort is a fit. No pitch deck.
            </p>
          </RevealOnScroll>
        </div>

        <RevealOnScroll delay={0.22}>
          <Magnetic>
            <a
              href={BOOKING_URL}
              className="inline-flex items-center gap-1.5 rounded-full border border-rule-2 px-6 py-3.5 text-[14px] font-medium text-ink transition-colors duration-fast ease-out hover:bg-surface-2"
            >
              Book a call
              <span aria-hidden>→</span>
            </a>
          </Magnetic>
        </RevealOnScroll>
      </div>
    </section>
  );
}
