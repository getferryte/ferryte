import { META, RESULTS, SCENARIOS } from "@/data/benchmark";

export const dynamic = "force-static";

export function GET() {
  return Response.json(
    {
      meta: META,
      scenarios: SCENARIOS,
      results: RESULTS,
    },
    {
      headers: {
        "Cache-Control": "public, max-age=3600, s-maxage=86400",
        "X-Robots-Tag": "noindex",
      },
    },
  );
}
