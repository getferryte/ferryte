"use client";

import Link from "next/link";

import { CopyableCommand } from "@/components/CopyableCommand";
import {
  Magnetic,
  Reveal,
  RevealOnScroll,
  Stagger,
  StaggerItem,
} from "@/components/motion/Motion";

export default function PricingPage() {
  return (
    <main className="px-8 sm:px-12 lg:px-20">
      <div className="mx-auto max-w-6xl">
        <Header />
        <Tiers />
        <Compare />
        <Waitlist />
        <FAQ />
      </div>
    </main>
  );
}

/* ---------------------------------------------------------- Header */

function Header() {
  return (
    <section className="pt-28 pb-12 sm:pt-36 sm:pb-20">
      <Reveal delay={0.05}>
        <div className="flex items-center gap-2.5">
          <span className="dot dot-royal dot-live" />
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
            Open core · MIT engine
          </span>
        </div>
      </Reveal>

      <Reveal delay={0.18} className="mt-10 max-w-5xl">
        <h1 className="font-display text-[44px] font-light leading-[1.02] tracking-[-0.04em] text-ink sm:text-[72px] lg:text-[96px]">
          Free where developers live.
          <br />
          <span className="text-ink-3">Paid where security teams pay.</span>
        </h1>
      </Reveal>

      <Reveal delay={0.4} className="mt-8 max-w-2xl">
        <p className="text-lede text-ink-2">
          Same model as Sentry, PostHog, Supabase. The detection engine is MIT
          because nobody adopts un-auditable security tooling. The trust plane —
          hosted, hardened, attested — is where the revenue lives.
        </p>
      </Reveal>
    </section>
  );
}

/* ---------------------------------------------------------- Tiers */

const TIERS = [
  {
    name: "Core",
    badge: "Available",
    badgeTone: "ok" as const,
    price: "MIT · free",
    blurb: "The library, the CLI, and the four scenarios. Ship it in your CI today.",
    features: [
      "ferryte.instrument() one-line auto-patch",
      "source-revocation · cross-tenant-isolation · stale-fact · memory-poisoning",
      "Lineage graph + blast radius (SQLite)",
      "Mem0 + generic vector adapters",
      "JSON + HTML coverage reports",
      "Local Next.js dashboard",
      "CI gate: non-zero exit on leak",
    ],
    cta: { label: "pip install ferryte", href: null, copyable: "pip install ferryte" },
    accent: false,
  },
  {
    name: "Cloud",
    badge: "Private beta",
    badgeTone: "royal" as const,
    price: "Design-partner waitlist",
    blurb: "The hosted oracle. Continuous verification, regression alerts, full history.",
    features: [
      "Everything in Core",
      "Hosted continuous verification",
      "Historical reports + regression alerts",
      "Slack, PagerDuty, Linear integrations",
      "Multi-environment management",
      "Per-tenant blast-radius dashboards",
      "Public status badges for the repo",
    ],
    cta: { label: "Join waitlist", href: "mailto:hello@ferryte.dev?subject=Ferryte%20Cloud%20waitlist", copyable: null },
    accent: true,
  },
  {
    name: "Enterprise",
    badge: "Private beta",
    badgeTone: "pending" as const,
    price: "Annual · contact us",
    blurb: "Self-hosted, hardened, and where compliance receipts and runtime enforcement live.",
    features: [
      "Everything in Cloud",
      "Self-hosted with SSO + RBAC",
      "Audit logs + SOC2-ready posture",
      "Signed compliance attestations (GDPR / CCPA)",
      "Premium adapters: AgentCore, Zep, GovCloud",
      "Runtime retrieval enforcement (v2)",
      "Support SLA + dedicated channel",
    ],
    cta: { label: "Talk to us", href: "mailto:hello@ferryte.dev?subject=Ferryte%20Enterprise", copyable: null },
    accent: false,
  },
];

function Tiers() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-24">
      <Stagger className="grid gap-5 lg:grid-cols-3" staggerDelay={0.12}>
        {TIERS.map((t) => (
          <StaggerItem key={t.name}>
            <article
              className={[
                "flex h-full flex-col rounded-xl border bg-surface p-8 transition-colors duration-base ease-out",
                t.accent
                  ? "border-royal/40 shadow-[0_24px_64px_-24px_rgba(90,138,150,0.45)]"
                  : "border-rule hover:border-rule-2",
              ].join(" ")}
            >
              <header className="flex items-center justify-between">
                <h3 className="font-display text-[28px] font-light tracking-[-0.022em] text-ink">
                  {t.name}
                </h3>
                <BadgePill tone={t.badgeTone}>{t.badge}</BadgePill>
              </header>

              <p className="mt-1 text-caption text-ink-3">{t.price}</p>

              <p className="mt-6 text-body text-ink-2">{t.blurb}</p>

              <ul className="mt-7 flex flex-col gap-3 border-t border-rule/60 pt-6 text-body text-ink-2">
                {t.features.map((f) => (
                  <li
                    key={f}
                    className="before:mr-3 before:text-royal before:content-['+']"
                  >
                    {f}
                  </li>
                ))}
              </ul>

              <div className="mt-8 flex-1" />

              <div className="pt-2">
                {t.cta.copyable ? (
                  <CopyableCommand command={t.cta.copyable} />
                ) : (
                  <Magnetic>
                    <a
                      href={t.cta.href ?? "#"}
                      className={[
                        "inline-flex items-center gap-1.5 rounded-full px-5 py-3 text-[14px] font-medium transition-colors duration-fast ease-out",
                        t.accent
                          ? "bg-royal text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] hover:bg-royal-2"
                          : "border border-rule-2 text-ink hover:bg-surface-2",
                      ].join(" ")}
                    >
                      {t.cta.label}
                      <span aria-hidden>→</span>
                    </a>
                  </Magnetic>
                )}
              </div>
            </article>
          </StaggerItem>
        ))}
      </Stagger>

      <RevealOnScroll delay={0.2} className="mt-10">
        <p className="text-caption text-ink-3">
          See{" "}
          <a
            href="https://github.com/getferryte/ferryte/blob/main/LICENSING.md"
            className="text-ink-2 underline-offset-4 hover:text-ink hover:underline"
          >
            LICENSING.md
          </a>{" "}
          and{" "}
          <a
            href="https://github.com/getferryte/ferryte/blob/main/COMMERCIAL.md"
            className="text-ink-2 underline-offset-4 hover:text-ink hover:underline"
          >
            COMMERCIAL.md
          </a>{" "}
          in the repo for the exact open-core boundary, contributor policy, and commercial-tier scope.
        </p>
      </RevealOnScroll>
    </section>
  );
}

function BadgePill({
  tone,
  children,
}: {
  tone: "ok" | "royal" | "pending";
  children: React.ReactNode;
}) {
  const styles = {
    ok: "text-ok border-ok/30",
    royal: "text-royal border-royal/30",
    pending: "text-pending border-pending/30",
  }[tone];
  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 rounded-full border bg-black/60 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.18em]",
        styles,
      ].join(" ")}
    >
      <span
        className={[
          "dot",
          tone === "ok" ? "dot-ok" : tone === "royal" ? "dot-royal" : "dot-pending",
        ].join(" ")}
      />
      {children}
    </span>
  );
}

/* ---------------------------------------------------------- Compare */

const COMPARE_ROWS = [
  { feature: "Local CLI + dashboard", core: true, cloud: true, ent: true },
  { feature: "Four canary scenarios", core: true, cloud: true, ent: true },
  { feature: "Mem0 + pgvector adapters", core: true, cloud: true, ent: true },
  { feature: "Hosted continuous verification", core: false, cloud: true, ent: true },
  { feature: "Historical reports + regression alerts", core: false, cloud: true, ent: true },
  { feature: "Slack / PagerDuty / Linear", core: false, cloud: true, ent: true },
  { feature: "SSO + RBAC", core: false, cloud: false, ent: true },
  { feature: "Audit logs · SOC2 posture", core: false, cloud: false, ent: true },
  { feature: "Signed GDPR / CCPA attestations", core: false, cloud: false, ent: true },
  { feature: "Premium adapters (AgentCore / Zep / GovCloud)", core: false, cloud: false, ent: true },
  { feature: "Runtime retrieval enforcement (v2)", core: false, cloud: false, ent: true },
];

function Compare() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-24">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          Side by side
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          Where the boundary actually sits.
        </h2>
      </RevealOnScroll>

      <RevealOnScroll delay={0.2} className="mt-12 overflow-x-auto">
        <table className="w-full min-w-[640px] border-separate border-spacing-0 text-[14px]">
          <thead>
            <tr className="text-left">
              <th className="border-b border-rule pb-4 font-mono text-[10.5px] font-normal uppercase tracking-[0.22em] text-ink-3">
                Feature
              </th>
              <th className="border-b border-rule pb-4 text-center font-mono text-[10.5px] font-normal uppercase tracking-[0.22em] text-ink-3">
                Core
              </th>
              <th className="border-b border-rule pb-4 text-center font-mono text-[10.5px] font-normal uppercase tracking-[0.22em] text-royal">
                Cloud
              </th>
              <th className="border-b border-rule pb-4 text-center font-mono text-[10.5px] font-normal uppercase tracking-[0.22em] text-ink-3">
                Enterprise
              </th>
            </tr>
          </thead>
          <tbody>
            {COMPARE_ROWS.map((r) => (
              <tr key={r.feature} className="group">
                <td className="border-b border-rule/60 py-4 text-ink-2 group-hover:text-ink">
                  {r.feature}
                </td>
                <td className="border-b border-rule/60 py-4 text-center">
                  <Mark on={r.core} />
                </td>
                <td className="border-b border-rule/60 py-4 text-center">
                  <Mark on={r.cloud} accent />
                </td>
                <td className="border-b border-rule/60 py-4 text-center">
                  <Mark on={r.ent} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </RevealOnScroll>
    </section>
  );
}

function Mark({ on, accent }: { on: boolean; accent?: boolean }) {
  if (!on) return <span className="text-ink-4">—</span>;
  return (
    <span className={accent ? "text-royal" : "text-ink"}>●</span>
  );
}

/* ---------------------------------------------------------- Waitlist */

function Waitlist() {
  return (
    <section
      id="waitlist"
      className="brand-hairline relative border-t border-rule/60 py-24 lg:py-32"
    >
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

      <RevealOnScroll delay={0.2} className="mt-10 max-w-2xl">
        <p className="text-lede text-ink-2">
          Ferryte Cloud goes private beta with five companies running multi-tenant
          memory in production. We pair an engineer with your team and wire the
          first integration in a day. We say no to most. The few we say yes to get
          the first six months free and a direct line to engineering.
        </p>
      </RevealOnScroll>

      <RevealOnScroll delay={0.32} className="mt-10 flex flex-wrap items-center gap-4">
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
          href="/product"
          className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
        >
          See how it works first →
        </Link>
      </RevealOnScroll>
    </section>
  );
}

/* ---------------------------------------------------------- FAQ */

const FAQ_ITEMS = [
  {
    q: "Why open-core and not fully closed?",
    a: "Nobody adopts un-auditable security tooling. Putting the detection engine under MIT means appsec teams can read the source on a Friday afternoon and ship a CI gate on Monday. The trust plane — hosted, hardened, attested — is where the revenue lives.",
  },
  {
    q: "Can I self-host the dashboard without paying?",
    a: "Yes. The local Next.js dashboard is MIT-licensed and ships in the repo. Run it against the JSON reports the CLI produces. Enterprise adds SSO, audit logs, multi-environment management, and signed compliance receipts on top of the same surface.",
  },
  {
    q: "Do contributions to the core stay MIT?",
    a: "Yes — contributors sign a CLA that grants us a license to relicense their changes, but the core repository remains MIT in perpetuity. See LICENSING.md and CONTRIBUTING.md.",
  },
  {
    q: "When does Cloud GA?",
    a: "After the design-partner cohort. We are deliberately not pushing the button until we have five teams running multi-tenant memory in production and the alerting + history surface have survived a quarter of regressions.",
  },
];

function FAQ() {
  return (
    <section className="border-t border-rule/60 py-20 lg:py-24">
      <RevealOnScroll>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
          FAQ
        </span>
      </RevealOnScroll>

      <RevealOnScroll delay={0.1} className="mt-8 max-w-3xl">
        <h2 className="font-display text-[34px] font-light leading-[1.06] tracking-[-0.028em] text-ink sm:text-[44px]">
          The four questions everyone asks.
        </h2>
      </RevealOnScroll>

      <Stagger className="mt-12 flex flex-col gap-10" staggerDelay={0.08}>
        {FAQ_ITEMS.map((item) => (
          <StaggerItem key={item.q}>
            <article className="grid gap-3 border-l-2 border-rule pl-6 transition-colors duration-base ease-out hover:border-royal">
              <h3 className="font-display text-[20px] font-light tracking-[-0.014em] text-ink sm:text-[24px]">
                {item.q}
              </h3>
              <p className="text-body text-ink-2">{item.a}</p>
            </article>
          </StaggerItem>
        ))}
      </Stagger>
    </section>
  );
}
