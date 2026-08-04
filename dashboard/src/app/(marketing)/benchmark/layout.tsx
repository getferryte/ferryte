import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Agent Memory Security Benchmark",
  description:
    "The Memory Report is Ferryte's open, reproducible benchmark for AI agent memory security: deletion, stale facts, cross-tenant isolation, and memory poisoning across real memory stacks.",
  openGraph: {
    title: "The Memory Report — Ferryte",
    description:
      "An open benchmark of whether AI agent memory stacks actually forget revoked data.",
    type: "article",
    url: "/benchmark",
    images: [
      {
        url: "/og",
        width: 1200,
        height: 630,
        alt: "The Memory Report — Ferryte",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "The Memory Report — Ferryte",
    description:
      "An open benchmark of whether AI agent memory stacks actually forget revoked data.",
    images: ["/og"],
  },
  alternates: { canonical: "/benchmark" },
};

export default function BenchmarkLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
