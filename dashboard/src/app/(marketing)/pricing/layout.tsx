import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Agent Memory Debugging Pricing",
  description:
    "Ferryte is source-available (BSL 1.1, converts to Apache 2.0): free debugging engine, hosted Cloud memory observability (private beta), self-hosted Enterprise. Same model as Sentry and MariaDB.",
  openGraph: {
    title: "Pricing — Ferryte",
    description:
      "Free where developers debug. Paid where teams run in prod.",
    type: "website",
    url: "/pricing",
    images: [
      {
        url: "/og",
        width: 1200,
        height: 630,
        alt: "Ferryte pricing",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Pricing — Ferryte",
    description:
      "Free where developers debug. Paid where teams run in prod.",
    images: ["/og"],
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
