import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Agent Memory Audit · $500, 48 hours",
  description:
    "A fixed-price audit of your AI agent's memory: we instrument it, run the full forgetting battery, trace your worst wrong answers to the memories that caused them, and hand you the evidence. Runs entirely in your infrastructure.",
  openGraph: {
    title: "Agent Memory Audit — Ferryte",
    description:
      "Your agent's memory has bugs you can't see. In 48 hours we'll show you every one we can find — and prove it.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Agent Memory Audit — Ferryte",
    description:
      "Fixed price. 48-hour turnaround. Runs in your infra. Money back if we find nothing actionable.",
  },
  alternates: { canonical: "/audit" },
};

export default function AuditLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
