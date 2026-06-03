import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Manifesto",
  description:
    "Why Ferryte exists: AWS, Zep, and OWASP have already admitted that AI agent memory does not propagate deletes. Almost nobody tests for it in CI.",
  openGraph: {
    title: "Manifesto — Ferryte",
    description:
      "The platforms said it themselves. We made it testable.",
    type: "article",
  },
  twitter: {
    card: "summary_large_image",
    title: "Manifesto — Ferryte",
    description:
      "The platforms said it themselves. We made it testable.",
  },
  alternates: { canonical: "/manifesto" },
};

export default function ManifestoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
