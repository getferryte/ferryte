import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing · Source-available",
  description:
    "Ferryte is source-available (BSL 1.1, converts to Apache 2.0): free debugging engine, hosted Cloud memory observability (private beta), self-hosted Enterprise. Same model as Sentry and MariaDB.",
  openGraph: {
    title: "Pricing — Ferryte",
    description:
      "Free where developers debug. Paid where teams run in prod.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Pricing — Ferryte",
    description:
      "Free where developers debug. Paid where teams run in prod.",
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
