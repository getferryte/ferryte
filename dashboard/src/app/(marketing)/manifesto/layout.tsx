import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Why AI Agent Memory Is a Black Box",
  description:
    "Why Ferryte exists: agent memory is a black box. You can see what the agent said, never why it believed it. AWS, Zep, and OWASP already admit memory misbehaves invisibly — we make it traceable.",
  openGraph: {
    title: "Manifesto — Ferryte",
    description:
      "Agent memory is a black box. We make it traceable.",
    type: "article",
    url: "/manifesto",
    images: [
      {
        url: "/og",
        width: 1200,
        height: 630,
        alt: "Ferryte manifesto on AI agent memory",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Manifesto — Ferryte",
    description:
      "Agent memory is a black box. We make it traceable.",
    images: ["/og"],
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
