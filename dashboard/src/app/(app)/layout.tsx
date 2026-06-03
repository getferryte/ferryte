import Link from "next/link";

import { BrandLink } from "@/components/Brand";

const NAV: { href: string; label: string }[] = [
  { href: "/app", label: "Overview" },
  { href: "/app/lineage", label: "Lineage" },
  { href: "/app/blindspots", label: "Blind spots" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="sticky top-0 z-30 border-b border-rule/70 bg-black/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-8 py-5">
          <div className="flex items-center gap-10">
            <BrandLink href="/app" />
            <nav className="hidden items-center gap-7 md:flex">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="text-[13.5px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-6">
            <Link
              href="/"
              className="hidden text-[13px] text-ink-3 transition-colors duration-fast ease-out hover:text-ink sm:inline"
            >
              ← Marketing
            </Link>
            <a
              href="https://github.com/getferryte/ferryte"
              className="text-[13px] text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
            >
              GitHub →
            </a>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-8 pb-28 pt-16">{children}</main>

      <footer className="border-t border-rule/70">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-8 py-8 text-caption text-ink-3">
          <span>Ferryte · open-core · MIT</span>
          <span className="font-mono text-[11px] tracking-[0.06em]">
            Designed for catching the leak before your customer does.
          </span>
        </div>
      </footer>
    </>
  );
}
