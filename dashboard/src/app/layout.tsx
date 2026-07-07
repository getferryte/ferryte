import type { Metadata } from "next";

import { sans, mono } from "./fonts";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://ferryte.dev";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Ferryte — memory debugging for AI agents",
    template: "%s · Ferryte",
  },
  description:
    "See why your AI agent said that. Ferryte traces any wrong, stale, or leaked answer back to the exact memory that caused it — where it came from, what it contaminated, and proves your fix stuck. Source-available.",
  keywords: [
    "agent memory",
    "AI agents",
    "memory debugging",
    "agent observability",
    "LLM memory",
    "memory attribution",
    "RAG debugging",
    "stale memory",
    "Mem0",
    "Zep",
    "AWS Bedrock AgentCore",
    "OWASP ASI06",
    "AI incident",
  ],
  authors: [{ name: "Ferryte" }],
  creator: "Ferryte",
  applicationName: "Ferryte",
  openGraph: {
    type: "website",
    url: siteUrl,
    siteName: "Ferryte",
    title: "Ferryte — memory debugging for AI agents",
    description:
      "When your agent gets something wrong, Ferryte shows which memory caused it, where it came from, and proves the fix stuck. Source-available. BSL 1.1 engine.",
    images: [
      {
        url: "/og",
        width: 1200,
        height: 630,
        alt: "Ferryte — memory debugging for AI agents",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Ferryte — memory debugging for AI agents",
    description:
      "See why your AI agent said that. Trace any wrong answer back to the memory that caused it.",
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
    <html
      lang="en"
      className={`${sans.variable} ${mono.variable} scroll-smooth`}
    >
      <body className="min-h-screen bg-black font-sans text-ink antialiased">
        {children}
      </body>
    </html>
  );
}
