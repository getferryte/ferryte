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
            Source-available · BSL 1.1
          </span>
        </div>
      </Reveal>

      <Reveal delay={0.18} className="mt-10 max-w-5xl">
        <h1 className="font-display text-[44px] font-light leading-[1.02] tracking-[-0.04em] text-ink sm:text-[72px] lg:text-[96px]">
          Free where developers debug.
          <br />
          <span className="text-ink-3">Paid where teams run in prod.</span>
        </h1>
      </Reveal>

      <Reveal delay={0.4} className="mt-8 max-w-2xl">
        <p className="text-lede text-ink-2">
          Same model as Sentry and MariaDB. The debugging engine is
          source-available (BSL 1.1) — read every line, self-host it, run it
          in production free. The hosted plane — persistent timelines, prod
          alerts, shared history — is the paid product.
        </p>
      </Reveal>
    </section>
  );
}

/* ---------------------------------------------------------- Tiers */

const TIERS = [
  {
    name: "Core",
    badge: "Available today",
    badgeTone: "ok" as const,
    price: "BSL 1.1 · free forever (self-hosted)",
    blurb: "The library, the CLI, and the local memory inspector. Read it, self-host it, debug your agent today — free forever for self-hosted use.",
    featuresNote: null as string | null,
    features: [
      "ferryte.instrument() one-line auto-patch",
      "ferryte why — attribute any answer to the memory behind it",
      "Write-time lineage graph + blast radius (SQLite)",
      "Mem0 · vector · Zep · Letta · Cloudflare adapters (pgvector / Chroma / Qdrant)",
      "Local memory inspector dashboard",
      "Fix & verify: prove a deleted memory is really gone",
      "CI gate for memory regressions",
    ],
    cta: { label: "pip install ferryte", href: null, copyable: "pip install ferryte" },
    accent: false,
  },
  {
    name: "Cloud",
    badge: "Pre-release",
    badgeTone: "royal" as const,
    price: "Free for design partners · paid after · pricing TBD",
    blurb: "Not built yet — five design partners are shaping it. Free during the design-partner window, then a paid product. When it ships, the hosted memory-observability plane for agents in production.",
    featuresNote: "What it will do once we ship it",
    features: [
      "Everything in Core",
      "Hosted memory timelines (persistent, cross-session)",
      "Prod incident alerts when memory misbehaves",
      "Regression detection across deploys",
      "Slack, PagerDuty, Linear integrations",
      "Per-user & per-tenant memory dashboards",
      "Team collaboration + shared history",
    ],
    cta: { label: "Join design-partner cohort", href: "/cloud#waitlist", copyable: null },
    accent: true,
  },
  {
    name: "Enterprise",
    badge: "Roadmap",
    badgeTone: "pending" as const,
    price: "TBD · talk to us",
    blurb: "Direction, not product yet. Self-hosted hardening + signed compliance — built once Cloud is mature.",
    featuresNote: "What we plan to build, once Cloud is in hands",
    features: [
      "Everything in Cloud",
      "Self-hosted / VPC with SSO + RBAC",
      "Audit logs + SOC2-ready posture",
      "Signed deletion attestations (GDPR / CCPA)",
      "Premium adapters: deep AgentCore, GovCloud, custom",
      "Runtime memory governance (v2)",
      "Support SLA + dedicated channel",
    ],
    cta: { label: "Talk to us", href: "/cloud#book-a-call", copyable: null },
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

              {t.featuresNote && (
                <p className="mt-7 border-t border-rule/60 pt-6 font-mono text-[10.5px] uppercase tracking-[0.18em] text-ink-3">
                  {t.featuresNote}
                </p>
              )}
              <ul
                className={[
                  "flex flex-col gap-3 text-body text-ink-2",
                  t.featuresNote
                    ? "mt-5"
                    : "mt-7 border-t border-rule/60 pt-6",
                ].join(" ")}
              >
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
          in the repo for the exact licensing boundary, contributor policy, and commercial-tier scope.
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
  { feature: "Local CLI + memory inspector", core: true, cloud: true, ent: true },
  { feature: "ferryte why — memory attribution", core: true, cloud: true, ent: true },
  { feature: "Fix & verify a deletion", core: true, cloud: true, ent: true },
  { feature: "Mem0 · vector · Zep · Letta · Cloudflare adapters", core: true, cloud: true, ent: true },
  { feature: "Hosted memory timelines (cross-session)", core: false, cloud: true, ent: true },
  { feature: "Prod incident alerts + regression detection", core: false, cloud: true, ent: true },
  { feature: "Slack / PagerDuty / Linear", core: false, cloud: true, ent: true },
  { feature: "SSO + RBAC", core: false, cloud: false, ent: true },
  { feature: "Audit logs · SOC2 posture", core: false, cloud: false, ent: true },
  { feature: "Signed GDPR / CCPA deletion attestations", core: false, cloud: false, ent: true },
  { feature: "Premium adapters (deep AgentCore / GovCloud / custom)", core: false, cloud: false, ent: true },
  { feature: "Runtime memory governance (v2)", core: false, cloud: false, ent: true },
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

      <RevealOnScroll delay={0.15} className="mt-6 max-w-2xl">
        <p className="text-caption text-ink-3">
          ●&nbsp; in Core = ships today.&nbsp;&nbsp;
          ●&nbsp; in Cloud = building it with the first five design partners.&nbsp;&nbsp;
          ●&nbsp; in Enterprise = roadmap, once Cloud is mature.
        </p>
      </RevealOnScroll>

      <RevealOnScroll delay={0.2} className="mt-10 overflow-x-auto">
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
          Paired with the founder.
          <br />
          <span className="text-ink-3">Six months of Cloud free. Shape the roadmap.</span>
        </h2>
      </RevealOnScroll>

      <RevealOnScroll delay={0.2} className="mt-10 max-w-2xl">
        <p className="text-lede text-ink-2">
          Ferryte Cloud isn&rsquo;t built yet — five design partners will shape it
          before we ship. Today: the founding engineer paired with your team for
          the first Core integration. When Cloud ships: six months free for
          design partners.
        </p>
      </RevealOnScroll>

      <RevealOnScroll delay={0.32} className="mt-10 flex flex-wrap items-center gap-4">
        <Magnetic>
          <Link
            href="/cloud#waitlist"
            className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2"
          >
            Join the waitlist
            <span aria-hidden>→</span>
          </Link>
        </Magnetic>
        <Link
          href="/cloud#book-a-call"
          className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
        >
          Or book a call →
        </Link>
      </RevealOnScroll>
    </section>
  );
}

/* ---------------------------------------------------------- FAQ */

const FAQ_ITEMS = [
  {
    q: "Why source-available (BSL) and not MIT or fully closed?",
    a: "Nobody instruments their agent's memory with un-auditable tooling, so the engine stays readable and self-hostable — read the source on a Friday afternoon, ship it Monday. BSL adds exactly one restriction over MIT: you can't resell Ferryte itself as a competing hosted service. That closes the hyperscaler-clone risk that hit Elastic, Redis, and HashiCorp, without locking anything away — every version converts to Apache 2.0 after four years.",
  },
  {
    q: "Can I self-host the dashboard without paying?",
    a: "Yes. The local Next.js dashboard is source-available and ships in the repo. Run it against the JSON reports the CLI produces, in production, for free. Enterprise adds SSO, audit logs, multi-environment management, and signed compliance receipts on top of the same surface.",
  },
  {
    q: "Will Core ever become paid, or get features clawed back into Cloud?",
    a: "No. Core is free forever for self-hosted use — we never paywall something Core already does. Cloud and Enterprise are net-new surface (hosted memory timelines, prod alerts, signed attestations) sold to teams running agents in production. The design-partner cohort gets Cloud free during the build window; after that Cloud is a paid product, while Core stays free.",
  },
  {
    q: "What license do contributions fall under?",
    a: "Contributors sign a CLA that grants us a license to incorporate their changes into both the source-available core (BSL 1.1, converting to Apache 2.0) and the commercial tiers. The core repository stays source-available in perpetuity, and every version becomes Apache 2.0 four years after release. See LICENSING.md and CONTRIBUTING.md.",
  },
  {
    q: "When does Cloud GA?",
    a: "After the design-partner cohort. We are deliberately not pushing the button until we have five teams running stateful agents in production and the timeline + alerting surface have survived a quarter of real memory bugs.",
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
          The questions everyone asks.
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
