import type { Metadata } from "next";

import { sans, mono } from "./fonts";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://ferryte.dev";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Ferryte — verification for agent forgetting",
    template: "%s · Ferryte",
  },
  description:
    "Open-core forgetting oracle for AI agents. Plant canary memories, call the real delete API, prove the leak is gone — or admit what you can't see.",
  keywords: [
    "agent memory",
    "AI agents",
    "forgetting",
    "memory verification",
    "Mem0",
    "Zep",
    "AWS Bedrock AgentCore",
    "OWASP ASI06",
    "GDPR right to be forgotten",
    "vector store testing",
    "AI security",
    "agentic top 10",
  ],
  authors: [{ name: "Ferryte" }],
  creator: "Ferryte",
  applicationName: "Ferryte",
  openGraph: {
    type: "website",
    url: siteUrl,
    siteName: "Ferryte",
    title: "Ferryte — verification for agent forgetting",
    description:
      "Plant canary memories, call the real delete API, prove the leak is gone. Open-core. MIT engine. Catch the leak before your customer does.",
    images: [
      {
        url: "/og",
        width: 1200,
        height: 630,
        alt: "Ferryte — verification for agent forgetting",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Ferryte — verification for agent forgetting",
    description:
      "Open-core forgetting oracle for AI agents. Catch the leak before your customer does.",
    images: ["/og"],
    creator: "@ferryte",
  },
  // Icons are auto-generated from src/app/icon.png + src/app/apple-icon.png.
  robots: {
    index: true,
    follow: true,
  },
  alternates: {
    canonical: "/",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body className="min-h-screen bg-black font-sans text-ink antialiased">
        {children}
      </body>
    </html>
  );
}
