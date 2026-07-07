import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Manifesto",
  description:
    "Why Ferryte exists: agent memory is a black box. You can see what the agent said, never why it believed it. AWS, Zep, and OWASP already admit memory misbehaves invisibly — we make it traceable.",
  openGraph: {
    title: "Manifesto — Ferryte",
    description:
      "Agent memory is a black box. We make it traceable.",
    type: "article",
  },
  twitter: {
    card: "summary_large_image",
    title: "Manifesto — Ferryte",
    description:
      "Agent memory is a black box. We make it traceable.",
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
