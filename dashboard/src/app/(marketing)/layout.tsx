import Link from "next/link";

import { BrandLink } from "@/components/Brand";
import { MarketingNav } from "@/components/MarketingNav";

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <header className="sticky top-0 z-30 border-b border-rule/40 bg-black/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-8 py-5">
          <BrandLink href="/" showVersion={false} />
          <MarketingNav />
        </div>
      </header>

      {children}

      <footer className="border-t border-rule/70">
        <div className="mx-auto max-w-6xl px-8 py-14">
          <div className="flex flex-wrap items-end justify-between gap-10">
            <div className="max-w-md">
              <BrandLink href="/" showVersion={false} />
              <p className="mt-5 text-body text-ink-3">
                Memory debugging for AI agents. Source-available engine
                (BSL 1.1, converts to Apache 2.0), commercial Cloud +
                Enterprise tiers.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-x-12 gap-y-3 text-[13.5px]">
              <FooterCol title="Product">
                <FooterLink href="/manifesto">Manifesto</FooterLink>
                <FooterLink href="/product">How it works</FooterLink>
                <FooterLink href="/pricing">Pricing</FooterLink>
                <FooterLink href="/app">Dashboard</FooterLink>
              </FooterCol>
              <FooterCol title="Code">
                <FooterLink href="https://github.com/getferryte/ferryte">
                  GitHub
                </FooterLink>
                <FooterLink href="https://pypi.org/project/ferryte/">
                  PyPI
                </FooterLink>
                <FooterLink href="https://github.com/getferryte/ferryte/blob/main/LICENSE">
                  License (BSL 1.1)
                </FooterLink>
              </FooterCol>
            </div>
          </div>

          <div className="mt-14 flex flex-wrap items-center justify-between gap-3 border-t border-rule/70 pt-8 text-caption text-ink-3">
            <span>© {new Date().getFullYear()} Ferryte · source-available core (BSL 1.1)</span>
            <span className="font-mono text-[11px] tracking-[0.06em]">
              Designed for the engineer debugging their agent&rsquo;s memory at 2am.
            </span>
          </div>
        </div>
      </footer>
    </>
  );
}

function FooterCol({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3">
      <span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-ink-3">
        {title}
      </span>
      <div className="flex flex-col gap-2.5">{children}</div>
    </div>
  );
}

function FooterLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  const external = href.startsWith("http");
  if (external) {
    return (
      <a
        href={href}
        className="text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
      >
        {children}
      </a>
    );
  }
  return (
    <Link
      href={href}
      className="text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
    >
      {children}
    </Link>
  );
}
