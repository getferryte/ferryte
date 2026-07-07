import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Product",
  description:
    "How Ferryte works: one line to instrument, write-time lineage for every memory, causal attribution by replay, and a fix-and-verify loop. Trace any answer back to the memory that caused it.",
  openGraph: {
    title: "Product — Ferryte",
    description:
      "Four steps from install to root cause. One line, full memory provenance.",
    type: "article",
  },
  twitter: {
    card: "summary_large_image",
    title: "Product — Ferryte",
    description:
      "Four steps from install to root cause.",
  },
  alternates: { canonical: "/product" },
};

export default function ProductLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
