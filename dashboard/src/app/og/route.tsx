import { ImageResponse } from "next/og";

export const runtime = "edge";

const SIZE = { width: 1200, height: 630 };

/**
 * OG image — what people see when ferryte.dev is shared anywhere.
 *
 * Pure black canvas. Royal-blue accent on the wordmark dot only.
 * next/og only supports a limited CSS subset: every element with children
 * MUST set display: flex (or block / none). No inline-block.
 *
 * Note: route.tsx (Route Handlers) does NOT allow `size` / `contentType`
 * exports — those are for the convention-based opengraph-image.tsx file.
 * We use a local SIZE constant instead.
 */
export async function GET() {
  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
          height: "100%",
          backgroundColor: "#000",
          color: "#fafafa",
          padding: "72px 88px",
          fontFamily:
            "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif",
        }}
      >
        {/* top row — wordmark + status pip */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            color: "#a0a0a0",
            fontSize: 22,
          }}
        >
          <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
            <span style={{ color: "#fafafa", fontWeight: 600, fontSize: 32 }}>
              ferryte
            </span>
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: 999,
                backgroundColor: "#2563eb",
              }}
            />
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              letterSpacing: 2,
              textTransform: "uppercase",
              fontSize: 16,
              color: "#666",
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: 999,
                backgroundColor: "#2563eb",
              }}
            />
            OPEN-CORE · MIT
          </div>
        </div>

        {/* hero — big two-line headline */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            marginTop: 96,
            lineHeight: 0.98,
            letterSpacing: "-0.035em",
            fontWeight: 300,
          }}
        >
          <div style={{ display: "flex", fontSize: 96, color: "#fafafa" }}>
            Your AI deleted the data.
          </div>
          <div style={{ display: "flex", fontSize: 96, color: "#666" }}>
            The derived memories didn&rsquo;t.
          </div>
        </div>

        {/* footer */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: "auto",
            color: "#666",
            fontSize: 22,
            letterSpacing: 1,
            textTransform: "uppercase",
          }}
        >
          <div style={{ display: "flex" }}>Verification for agent forgetting</div>
          <div style={{ display: "flex" }}>ferryte.dev</div>
        </div>
      </div>
    ),
    {
      ...SIZE,
      headers: {
        "Cache-Control": "public, immutable, no-transform, max-age=31536000",
      },
    },
  );
}
