import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Product",
  description:
    "How Ferryte works: one line to instrument, deterministic canary probes, your real delete API, deep store + retrieval verification. Fails CI on any surviving marker.",
  openGraph: {
    title: "Product — Ferryte",
    description:
      "Four steps from install to a broken build. One line, zero new mental model.",
    type: "article",
  },
  twitter: {
    card: "summary_large_image",
    title: "Product — Ferryte",
    description:
      "Four steps from install to a broken build.",
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
