import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Cloud + Enterprise · Join the waitlist",
  description:
    "Ferryte Cloud watches your agent in production and alerts you the moment its memory starts misbehaving; Enterprise hands compliance teams signed GDPR/CCPA deletion attestations. In private development — join the waitlist or book a design-partner call.",
  openGraph: {
    title: "Ferryte Cloud + Enterprise",
    description:
      "You caught it once. We'll watch for the next one. Join the design-partner waitlist.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Ferryte Cloud + Enterprise",
    description:
      "You caught it once. We'll watch for the next one. Join the design-partner waitlist.",
  },
  alternates: { canonical: "/cloud" },
};

export default function CloudLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
