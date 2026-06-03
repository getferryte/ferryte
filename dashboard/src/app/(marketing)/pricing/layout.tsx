import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Open core · Pricing",
  description:
    "Ferryte is open-core: MIT engine, hosted Cloud (private beta), self-hosted Enterprise. Same model as Sentry, PostHog, Supabase.",
  openGraph: {
    title: "Open core — Ferryte",
    description:
      "Free where developers live. Paid where security teams pay.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Open core — Ferryte",
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
