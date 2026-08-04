export type JsonLdNode = Record<string, unknown>;

const configuredSiteUrl =
  process.env.NEXT_PUBLIC_SITE_URL || "https://ferryte.dev";

export const SITE_URL = configuredSiteUrl.replace(/\/+$/, "");
export const ORGANIZATION_ID = `${SITE_URL}/#organization`;

export function absoluteUrl(path: string) {
  return new URL(path, `${SITE_URL}/`).toString();
}

export const organizationJsonLd: JsonLdNode = {
  "@type": "Organization",
  "@id": ORGANIZATION_ID,
  name: "Ferryte",
  url: absoluteUrl("/"),
  description: "Memory debugging for AI agents.",
  email: "hello@ferryte.dev",
  logo: {
    "@type": "ImageObject",
    url: absoluteUrl("/icon.png"),
    width: 512,
    height: 512,
  },
  sameAs: [
    "https://github.com/getferryte/ferryte",
    "https://pypi.org/project/ferryte/",
  ],
  knowsAbout: [
    "AI agent memory debugging",
    "memory attribution",
    "memory lineage",
    "counterfactual replay",
    "memory deletion verification",
    "AI agent memory security",
  ],
};

export const websiteJsonLd: JsonLdNode = {
  "@type": "WebSite",
  "@id": `${SITE_URL}/#website`,
  name: "Ferryte",
  alternateName: "ferryte.dev",
  url: absoluteUrl("/"),
  publisher: { "@id": ORGANIZATION_ID },
  inLanguage: "en",
};

export const softwareApplicationJsonLd: JsonLdNode = {
  "@type": "SoftwareApplication",
  "@id": `${SITE_URL}/product#software`,
  name: "Ferryte",
  alternateName: "Ferryte Core",
  url: absoluteUrl("/product"),
  description:
    "Memory debugging for AI agents: trace a wrong answer back to the exact memory that caused it, replay without it, and prove the fix.",
  applicationCategory: "DeveloperApplication",
  operatingSystem: "Any",
  softwareVersion: "0.2.3",
  isAccessibleForFree: true,
  downloadUrl: "https://pypi.org/project/ferryte/",
  codeRepository: "https://github.com/getferryte/ferryte",
  license: "https://github.com/getferryte/ferryte/blob/main/LICENSE",
  publisher: { "@id": ORGANIZATION_ID },
  featureList: [
    "Write-time memory lineage",
    "Answer-to-memory attribution",
    "Counterfactual replay",
    "Fix verification",
    "Local self-hosted memory inspector",
  ],
  offers: {
    "@type": "Offer",
    price: "0",
    priceCurrency: "USD",
    availability: "https://schema.org/InStock",
    url: "https://pypi.org/project/ferryte/",
  },
};

export function faqPageJsonLd(
  path: string,
  items: ReadonlyArray<{ q: string; a: string }>,
): JsonLdNode {
  return {
    "@type": "FAQPage",
    "@id": `${absoluteUrl(path)}#faq`,
    mainEntity: items.map((item) => ({
      "@type": "Question",
      name: item.q,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.a,
      },
    })),
  };
}

export function schemaGraph(...nodes: JsonLdNode[]): JsonLdNode {
  return {
    "@context": "https://schema.org",
    "@graph": nodes,
  };
}
