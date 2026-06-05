import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing · Source-available",
  description:
    "Ferryte is source-available (BSL 1.1, converts to Apache 2.0): free engine, hosted Cloud (private beta), self-hosted Enterprise. Same model as Sentry, CockroachDB, HashiCorp.",
  openGraph: {
    title: "Pricing — Ferryte",
    description:
      "Free where developers live. Paid where security teams pay.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Pricing — Ferryte",
    description:
      "Free where developers live. Paid where security teams pay.",
  },
  alternates: { canonical: "/pricing" },
};

export default function PricingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
