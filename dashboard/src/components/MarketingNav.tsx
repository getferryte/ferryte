"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/manifesto", label: "Manifesto" },
  { href: "/product", label: "Product" },
  { href: "/pricing", label: "Pricing" },
];

export function MarketingNav() {
  const pathname = usePathname() || "/";

  return (
    <nav className="flex items-center gap-7 text-[13.5px]">
      {ITEMS.map((item) => {
        const active =
          item.href === "/"
            ? pathname === "/"
            : pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={[
              "hidden transition-colors duration-fast ease-out sm:inline",
              active ? "text-ink" : "text-ink-2 hover:text-ink",
            ].join(" ")}
          >
            {item.label}
          </Link>
        );
      })}

      <a
        href="https://github.com/getferryte/ferryte"
        className="text-ink-2 transition-colors duration-fast ease-out hover:text-ink"
      >
        GitHub →
      </a>
      <Link
        href="/app"
        className="rounded-full bg-royal px-4 py-1.5 text-[13px] font-medium text-white transition-colors duration-fast ease-out hover:bg-royal-2"
      >
        Open dashboard
      </Link>
    </nav>
  );
}
