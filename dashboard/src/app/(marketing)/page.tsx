import Link from "next/link";

import { CopyableCommand } from "@/components/CopyableCommand";
import { Dot } from "@/components/Pill";

export default function MarketingPage() {
  return (
    <main className="ui-fade">
      <Hero />
      <Problem />
      <HowItWorks />
      <Before />
      <BuiltFor />
      <OpenCore />
      <Waitlist />
    </main>
  );
}

/* ------------------------------------------------------------- Hero -- */

function Hero() {
  return (
    <section className="mx-auto max-w-6xl px-8 pb-24 pt-24 sm:pt-32 lg:pt-40 ui-rise">
      <div className="flex items-center gap-2.5 text-caption text-ink-3">
        <span className="dot dot-royal dot-live" />
        <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
          Open beta · MIT
        </span>
      </div>

      <h1 className="mt-10 max-w-[16ch] font-display text-[56px] font-light leading-[0.98] tracking-tightest text-ink sm:text-[80px] lg:text-[104px]">
        Your AI deleted the data.
        <br />
        <span className="text-ink-3">The derived memories didn&rsquo;t.</span>
      </h1>

      <p className="mt-10 max-w-2xl text-[18px] leading-[1.55] text-ink-2 sm:text-[20px]">
        Ferryte is the open-core forgetting oracle for AI agents. It plants
        canary memories, calls your backend&rsquo;s real delete API, inspects
        both store contents and retrieval traces, and fails CI when a revoked
        marker still influences output — or admits exactly what it could not
        see.
      </p>

      <div className="mt-12 flex flex-wrap items-center gap-4">
        <CopyableCommand command="pip install ferryte" />
        <Link
          href="/app"
          className="rounded-full bg-royal px-5 py-2.5 text-[14px] font-medium text-white transition-colors duration-fast ease-out hover:bg-royal-2"
        >
          See a live report →
        </Link>
        <a
          href="https://github.com/getferryte/ferryte"
          className="text-[14px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
        >
          Star on GitHub
        </a>
      </div>

      <div className="mt-14 flex flex-wrap items-center gap-x-7 gap-y-3 text-caption text-ink-3">
        <Trust>Built for Mem0 · pgvector · Zep · AgentCore</Trust>
        <span className="text-ink-4">/</span>
        <Trust>One-line install</Trust>
        <span className="text-ink-4">/</span>
        <Trust>Non-zero exit on leak</Trust>
      </div>
    </section>
  );
}

function Trust({ children }: { children: React.ReactNode }) {
  return (
    <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-ink-3">
      {children}
    </span>
  );
}

/* ---------------------------------------------------------- Problem -- */

function Problem() {
  return (
    <section className="border-t border-rule/70 bg-black">
      <div className="mx-auto max-w-6xl px-8 py-28">
        <Eyebrow>The platform vendors say it themselves</Eyebrow>

        <div className="mt-14 grid gap-x-16 gap-y-16 lg:grid-cols-3">
          <QuoteBlock
            quote="Deleting an event doesn't remove the structured information derived out of it from the long term memory."
            cite="AWS Bedrock AgentCore"
          />
          <QuoteBlock
            quote="Deleting an episode does not regenerate the shared node summaries that already absorbed it."
            cite="Zep documentation"
          />
          <QuoteBlock
            quote="ASI06 — Memory poisoning. Persistent agent memory can absorb adversarial writes that survive normal cleanup."
            cite="OWASP Agentic Top 10, Dec 2025"
          />
        </div>

        <p className="mt-20 max-w-3xl text-[20px] leading-[1.45] text-ink-2 sm:text-[22px]">
          Three different teams, three different products, the same admission.
          <br />
          <span className="text-ink">
            Almost nobody tests for the leak in CI. You find out from a customer.
          </span>
        </p>
      </div>
    </section>
  );
}

function QuoteBlock({ quote, cite }: { quote: string; cite: string }) {
  return (
    <figure className="ui-rise">
      <blockquote className="font-display text-[22px] font-light leading-[1.3] tracking-[-0.018em] text-ink">
        <span className="text-royal">&ldquo;</span>
        {quote}
        <span className="text-royal">&rdquo;</span>
      </blockquote>
      <figcaption className="mt-6 font-mono text-[11px] uppercase tracking-[0.18em] text-ink-3">
        — {cite}
      </figcaption>
    </figure>
  );
}

/* ----------------------------------------------------- How it works -- */

const STEPS: { n: string; title: string; body: string }[] = [
  {
    n: "01",
    title: "Instrument",
    body:
      "One line — ferryte.instrument(). Auto-patches Mem0, pgvector, and custom stores at construction time. Your agent code does not change.",
  },
  {
    n: "02",
    title: "Probe",
    body:
      "Plants deterministic canary memories tagged by source and tenant — markers that cannot occur naturally in your data.",
  },
  {
    n: "03",
    title: "Delete",
    body:
      "Calls your backend's real delete API. Not a mock. Not a wrapper. The exact code path your production runs.",
  },
  {
    n: "04",
    title: "Verify",
    body:
      "Inspects both raw store contents and retrieval traces — not just agent answers, which give false confidence. Fails CI on any surviving marker.",
  },
];

function HowItWorks() {
  return (
    <section id="how" className="border-t border-rule/70">
      <div className="mx-auto max-w-6xl px-8 py-28">
        <Eyebrow>How it works</Eyebrow>
        <h2 className="mt-6 max-w-2xl font-display text-[40px] font-light leading-[1.05] tracking-[-0.028em] text-ink sm:text-[56px]">
          Four steps. Zero new mental model.
        </h2>
        <p className="mt-6 max-w-2xl text-lede text-ink-2">
          Ferryte does not ask you to migrate your memory layer or wrap your
          agent. It instruments what you already run, and tells you the truth
          about what survives a delete.
        </p>

        <ol className="mt-20 grid gap-x-12 gap-y-16 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s) => (
            <li key={s.n} className="ui-rise flex flex-col gap-5">
              <div className="font-mono text-[13px] tracking-[0.14em] text-royal">
                {s.n}
              </div>
              <h3 className="font-display text-[26px] font-medium leading-[1.1] tracking-[-0.022em] text-ink">
                {s.title}
              </h3>
              <p className="text-body text-ink-2">{s.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

/* ----------------------------------------------- What it catches -- */

function Before() {
  return (
    <section className="border-t border-rule/70 bg-black">
      <div className="mx-auto max-w-6xl px-8 py-28">
        <Eyebrow>What it catches</Eyebrow>
        <h2 className="mt-6 max-w-2xl font-display text-[40px] font-light leading-[1.05] tracking-[-0.028em] text-ink sm:text-[56px]">
          The leak you can&rsquo;t see, in two columns.
        </h2>

        <div className="mt-16 grid gap-6 lg:grid-cols-2">
          <CodePanel
            tone="issue"
            title="Without Ferryte"
            sublabel="silent leak"
          >
            <CodeLine prompt>{`store.delete_by_source("acme-doc-1")`}</CodeLine>
            <CodeLine muted>{`# returns 1 — primary record removed`}</CodeLine>
            <CodeLine prompt>{`agent.ask("acme", "what is the launch code?")`}</CodeLine>
            <CodeLine emphasis="issue">
              Based on what I remember: the launch code is ORION-DELTA-77.
            </CodeLine>
            <CodeLine muted>
              # the per-tenant summary absorbed it. nothing flagged.
            </CodeLine>
          </CodePanel>

          <CodePanel
            tone="ok"
            title="With Ferryte"
            sublabel="caught in CI"
          >
            <CodeLine prompt>{`ferryte test --scenario source-revocation`}</CodeLine>
            <CodeLine muted>{`source-revocation       FAIL    3 findings`}</CodeLine>
            <CodeLine emphasis="issue">
              FAIL revoked_marker_in_probe
            </CodeLine>
            <CodeLine muted>
              {`Revoked source 'acme-doc-1' still surfaces marker`}
              <br />
              {`'ORION-DELTA-77' via retrieval on tenant 'acme'`}
              <br />
              {`(artifact kind=summary, id=27dea877…).`}
            </CodeLine>
            <CodeLine emphasis="ok">{`exit code 1 — build break`}</CodeLine>
          </CodePanel>
        </div>
      </div>
    </section>
  );
}

function CodePanel({
  tone,
  title,
  sublabel,
  children,
}: {
  tone: "ok" | "issue";
  title: string;
  sublabel: string;
  children: React.ReactNode;
}) {
  return (
    <div className="overflow-hidden rounded-lg border border-rule bg-surface">
      <div className="flex items-center justify-between border-b border-rule px-5 py-3.5">
        <div className="flex items-center gap-3">
          <Dot tone={tone} />
          <span className="font-mono text-[12.5px] text-ink">{title}</span>
        </div>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-ink-3">
          {sublabel}
        </span>
      </div>
      <pre className="overflow-x-auto px-5 py-5 font-mono text-[12.5px] leading-[1.7]">
        <code>{children}</code>
      </pre>
    </div>
  );
}

function CodeLine({
  children,
  prompt = false,
  muted = false,
  emphasis,
}: {
  children: React.ReactNode;
  prompt?: boolean;
  muted?: boolean;
  emphasis?: "ok" | "issue";
}) {
  const color = emphasis === "issue"
    ? "text-issue"
    : emphasis === "ok"
      ? "text-ok"
      : muted
        ? "text-ink-3"
        : "text-ink";
  return (
    <span className={`block ${color}`}>
      {prompt ? <span className="text-royal">› </span> : null}
      {children}
    </span>
  );
}

/* ---------------------------------------------------------- Built for -- */

function BuiltFor() {
  return (
    <section className="border-t border-rule/70">
      <div className="mx-auto max-w-6xl px-8 py-28">
        <Eyebrow>Built for</Eyebrow>
        <h2 className="mt-6 max-w-2xl font-display text-[40px] font-light leading-[1.05] tracking-[-0.028em] text-ink sm:text-[56px]">
          Three buyers. One artifact.
        </h2>

        <div className="mt-16 grid gap-x-12 gap-y-12 lg:grid-cols-3">
          <Persona
            tag="engineering"
            title="The lead who owns the agent."
            body="Drop ferryte test into CI. The build breaks the moment a revoked source re-enters retrieval. Catch the leak in pre-prod, not in a Slack thread on Sunday."
          />
          <Persona
            tag="appsec"
            title="The reviewer who unblocks the deal."
            body="Replace 'we delete the row, trust us' with a regenerated forgetting-test report, an explicit blind-spot map, and a coverage number. Security review goes from weeks to days."
          />
          <Persona
            tag="compliance"
            title="The team that signs the receipt."
            body="GDPR and CCPA right-to-be-forgotten don't end at the row. Ferryte gives you transitive deletion evidence across raw stores, summaries, embeddings, and retrievals — and (in Enterprise) signed attestations."
          />
        </div>
      </div>
    </section>
  );
}

function Persona({
  tag,
  title,
  body,
}: {
  tag: string;
  title: string;
  body: string;
}) {
  return (
    <article className="ui-rise flex flex-col gap-5 border-t border-rule pt-8">
      <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
        {tag}
      </span>
      <h3 className="font-display text-[24px] font-medium leading-[1.15] tracking-[-0.022em] text-ink">
        {title}
      </h3>
      <p className="text-body text-ink-2">{body}</p>
    </article>
  );
}

/* ---------------------------------------------------------- Open core -- */

interface Tier {
  name: string;
  price: string;
  tagline: string;
  features: string[];
  cta: { label: string; href: string; primary?: boolean };
  available: boolean;
}

const TIERS: Tier[] = [
  {
    name: "Core",
    price: "MIT · free",
    tagline: "The library, the CLI, and the four scenarios. Ship it in your CI today.",
    features: [
      "ferryte.instrument() one-line auto-patch",
      "source-revocation, cross-tenant-isolation, stale-fact, memory-poisoning",
      "Lineage graph + blast radius (SQLite)",
      "Mem0 + generic vector adapters",
      "JSON + HTML coverage reports",
      "Local Next.js dashboard",
      "CI gate: non-zero exit on leak",
    ],
    cta: { label: "pip install ferryte", href: "https://pypi.org/project/ferryte", primary: false },
    available: true,
  },
  {
    name: "Cloud",
    price: "Design-partner waitlist",
    tagline: "The hosted oracle. Continuous verification, regression alerts, full history.",
    features: [
      "Everything in Core",
      "Hosted continuous verification",
      "Historical reports + regression alerts",
      "Slack, PagerDuty, Linear integrations",
      "Multi-environment management",
      "Per-tenant blast-radius dashboards",
      "Public status badges for the repo",
    ],
    cta: { label: "Join waitlist", href: "#waitlist", primary: true },
    available: false,
  },
  {
    name: "Enterprise",
    price: "Annual · contact us",
    tagline: "Self-hosted, hardened, and the place compliance receipts and runtime enforcement live.",
    features: [
      "Everything in Cloud",
      "Self-hosted with SSO + RBAC",
      "Audit logs + SOC2-ready posture",
      "Signed compliance attestations (GDPR / CCPA)",
      "Premium adapters: AgentCore, Zep, GovCloud",
      "Runtime retrieval enforcement (v2)",
      "Support SLA + dedicated channel",
    ],
    cta: { label: "Talk to us", href: "mailto:hello@ferryte.dev?subject=Ferryte%20Enterprise", primary: false },
    available: false,
  },
];

function OpenCore() {
  return (
    <section id="open-core" className="border-t border-rule/70 bg-black">
      <div className="mx-auto max-w-6xl px-8 py-28">
        <Eyebrow>Open core</Eyebrow>
        <h2 className="mt-6 max-w-3xl font-display text-[40px] font-light leading-[1.05] tracking-[-0.028em] text-ink sm:text-[56px]">
          Free where developers live.
          <br />
          <span className="text-ink-3">Paid where security teams pay.</span>
        </h2>
        <p className="mt-6 max-w-2xl text-lede text-ink-2">
          Same model as Sentry, PostHog, Supabase. The detection engine is MIT
          because nobody adopts un-auditable security tooling. The trust plane —
          hosted, hardened, attested — is where the revenue lives.
        </p>

        <div className="mt-16 grid gap-6 lg:grid-cols-3">
          {TIERS.map((t) => (
            <TierCard key={t.name} tier={t} />
          ))}
        </div>

        <p className="mt-12 max-w-2xl text-caption text-ink-3">
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
          in the repo for the exact open-core boundary, contributor policy, and
          commercial-tier scope.
        </p>
      </div>
    </section>
  );
}

function TierCard({ tier }: { tier: Tier }) {
  return (
    <div
      className={[
        "ui-rise flex flex-col gap-6 rounded-lg border p-7",
        tier.cta.primary
          ? "border-royal/50 bg-royal/[0.04]"
          : "border-rule bg-surface",
      ].join(" ")}
    >
      <div className="flex items-center justify-between">
        <h3 className="font-display text-[22px] font-medium tracking-[-0.022em] text-ink">
          {tier.name}
        </h3>
        {tier.available ? (
          <span className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.18em] text-ok">
            <Dot tone="ok" />
            Available
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.18em] text-pending">
            <Dot tone="pending" />
            Beta
          </span>
        )}
      </div>

      <div className="font-mono text-[12.5px] uppercase tracking-[0.14em] text-ink-3">
        {tier.price}
      </div>

      <p className="text-body text-ink-2">{tier.tagline}</p>

      <ul className="flex flex-col gap-2.5 border-t border-rule pt-5">
        {tier.features.map((f) => (
          <li key={f} className="flex items-start gap-2.5 text-[13.5px] text-ink-2">
            <span className="mt-[7px] h-[3px] w-[3px] shrink-0 rounded-full bg-ink-3" />
            <span>{f}</span>
          </li>
        ))}
      </ul>

      <div className="pt-2">
        {tier.cta.href.startsWith("http") || tier.cta.href.startsWith("mailto") ? (
          <a
            href={tier.cta.href}
            className={[
              "inline-flex items-center justify-center rounded-full px-4 py-2 text-[13px] font-medium transition-colors duration-fast ease-out",
              tier.cta.primary
                ? "bg-royal text-white hover:bg-royal-2"
                : "border border-rule text-ink-2 hover:border-rule-2 hover:text-ink",
            ].join(" ")}
          >
            {tier.cta.label}
          </a>
        ) : (
          <Link
            href={tier.cta.href}
            className={[
              "inline-flex items-center justify-center rounded-full px-4 py-2 text-[13px] font-medium transition-colors duration-fast ease-out",
              tier.cta.primary
                ? "bg-royal text-white hover:bg-royal-2"
                : "border border-rule text-ink-2 hover:border-rule-2 hover:text-ink",
            ].join(" ")}
          >
            {tier.cta.label}
          </Link>
        )}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------- Waitlist -- */

function Waitlist() {
  return (
    <section
      id="waitlist"
      className="border-t border-rule/70 brand-hairline relative"
    >
      <div className="mx-auto max-w-6xl px-8 py-28">
        <Eyebrow>Design partners</Eyebrow>
        <h2 className="mt-6 max-w-3xl font-display text-[44px] font-light leading-[1.04] tracking-[-0.028em] text-ink sm:text-[64px]">
          Ship the leak test
          <br />
          <span className="text-ink-3">before your customer does.</span>
        </h2>

        <div className="mt-14 grid gap-12 lg:grid-cols-2">
          <div className="flex flex-col gap-6">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
              Run it yourself
            </span>
            <p className="text-lede text-ink-2">
              Open-source. MIT. Zero account needed. Clone, install, and the
              demo runs against a self-contained leaky vector store in under
              thirty seconds.
            </p>
            <div className="flex flex-col gap-3">
              <CopyableCommand command="pip install ferryte" />
              <CopyableCommand command="ferryte test --scenario source-revocation" />
              <CopyableCommand command="python demo/multi_tenant_leak.py" />
            </div>
          </div>

          <div className="flex flex-col gap-6 rounded-lg border border-royal/40 bg-royal/[0.04] p-8">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-royal">
              Get the hosted version
            </span>
            <p className="text-lede text-ink-2">
              Ferryte Cloud goes private beta with five design partners running
              multi-tenant memory in production. We pair an engineer with your
              team and wire up the first integration in a day.
            </p>
            <a
              href="mailto:hello@ferryte.dev?subject=Ferryte%20design%20partner&body=Stack%3A%20%0ATenants%3A%20%0AMemory%20backend(s)%3A%20%0ALeak%20you%E2%80%99re%20worried%20about%3A%20"
              className="inline-flex items-center justify-center rounded-full bg-royal px-5 py-2.5 text-[14px] font-medium text-white transition-colors duration-fast ease-out hover:bg-royal-2"
            >
              Email hello@ferryte.dev →
            </a>
            <p className="text-caption text-ink-3">
              We reply within 24 hours. We say no to most. The few we say yes
              to get the first six months free and shape the roadmap.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------- bits -- */

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <span className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-ink-3">
      {children}
    </span>
  );
}
