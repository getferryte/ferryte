import type { MetadataRoute } from "next";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://ferryte.dev";

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = "2026-08-04";
  return [
    {
      url: `${siteUrl}/`,
      lastModified,
      changeFrequency: "weekly",
      priority: 1.0,
    },
    {
      url: `${siteUrl}/benchmark`,
      lastModified,
      changeFrequency: "weekly",
      priority: 0.95,
    },
    {
      url: `${siteUrl}/manifesto`,
      lastModified,
      changeFrequency: "monthly",
      priority: 0.9,
    },
    {
      url: `${siteUrl}/product`,
      lastModified,
      changeFrequency: "monthly",
      priority: 0.9,
    },
    {
      url: `${siteUrl}/audit`,
      lastModified,
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${siteUrl}/pricing`,
      lastModified,
      changeFrequency: "monthly",
      priority: 0.85,
    },
    {
      url: `${siteUrl}/cloud`,
      lastModified,
      changeFrequency: "weekly",
      priority: 0.92,
    },
    {
      url: `${siteUrl}/sample-audit.html`,
      lastModified,
      changeFrequency: "monthly",
      priority: 0.8,
    },
  ];
}
