"use client";

import Image from "next/image";
import Link from "next/link";

/**
 * The Ferryte mark — the gradient ribbon icon (no wordmark).
 * Always renders the rasterised PNG from /brand/icon-64.png so the
 * gradient is preserved at every size without recolouring tricks.
 */
export function Mark({ size = 22 }: { size?: number }) {
  return (
    <span
      className="inline-flex shrink-0 items-center justify-center"
      style={{ width: size, height: size }}
      aria-hidden
    >
      <Image
        src="/brand/icon-64.png"
        alt=""
        width={64}
        height={64}
        style={{ width: size, height: size, display: "block" }}
        priority
      />
    </span>
  );
}

/**
 * Lockup — mark + "Ferryte" wordmark, matching the supplied logo file.
 * The size prop drives the wordmark font-size; the mark scales with it.
 */
export function Wordmark({ size = 19 }: { size?: number }) {
  return (
    <span
      className="inline-flex items-center gap-2 font-display text-ink"
      style={{ fontSize: size, lineHeight: 1, letterSpacing: "-0.025em" }}
    >
      <Mark size={Math.round(size * 1.22)} />
      <span style={{ fontWeight: 500 }}>Ferryte</span>
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
      className="group inline-flex items-center gap-2 outline-none"
    >
      <Wordmark size={19} />
      {showVersion ? (
        <span className="ml-1 font-mono text-[10px] uppercase tracking-[0.18em] text-ink-3 transition-colors duration-fast group-hover:text-ink-2">
          v0.1
        </span>
      ) : null}
    </Link>
  );
}
