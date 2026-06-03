"use client";

import Link from "next/link";

export function Wordmark({ size = 18 }: { size?: number }) {
  return (
    <span
      className="inline-flex items-baseline gap-[3px] font-display text-ink"
      style={{ fontSize: size, lineHeight: 1 }}
    >
      <span>ferryte</span>
      <span
        aria-hidden
        className="dot dot-royal"
        style={{ width: 5, height: 5, transform: "translateY(-1px)" }}
      />
    </span>
  );
}

export function BrandLink({
  href = "/",
  showVersion = true,
}: {
  href?: string;
  showVersion?: boolean;
}) {
  return (
    <Link
      href={href}
      aria-label="Ferryte"
      className="group inline-flex items-baseline gap-2 outline-none"
    >
      <Wordmark size={19} />
      {showVersion ? (
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-3 transition-colors duration-fast group-hover:text-ink-2">
          v0.1
        </span>
      ) : null}
    </Link>
  );
}
