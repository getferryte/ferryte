import { ImageResponse } from "next/og";

export const runtime = "edge";

const SIZE = { width: 1200, height: 630 };

/**
 * OG image — what people see when ferryte.dev is shared.
 *
 * Pure black canvas. The brand teal-steel gradient is reused as both:
 *   1. The colour applied to the second line of the headline.
 *   2. A thin top hairline acting as a brand stripe.
 *
 * The mark itself is fetched as a static asset from the same origin and
 * embedded as an <img>. next/og supports inline <img> with absolute URLs.
 */
export async function GET(req: Request) {
  const origin = new URL(req.url).origin;
  const markUrl = `${origin}/brand/icon-64.png`;

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
          position: "relative",
        }}
      >
        {/* brand hairline at top */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: 2,
            backgroundImage:
              "linear-gradient(90deg, rgba(13,61,78,0) 0%, #0d3d4e 22%, #5a8a96 50%, #bfd1ce 65%, #5a8a96 78%, rgba(13,61,78,0) 100%)",
            display: "flex",
          }}
        />

        {/* top row — mark + wordmark, status pip on right */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            color: "#a0a0a0",
            fontSize: 22,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={markUrl}
              alt=""
              width={56}
              height={56}
              style={{ display: "flex" }}
            />
            <span
              style={{
                color: "#fafafa",
                fontWeight: 500,
                fontSize: 34,
                letterSpacing: "-0.02em",
              }}
            >
              Ferryte
            </span>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              letterSpacing: 2,
              textTransform: "uppercase",
              fontSize: 16,
              color: "#9bb8b8",
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: 999,
                backgroundColor: "#5a8a96",
                display: "flex",
              }}
            />
            SOURCE-AVAILABLE · BSL 1.1
          </div>
        </div>

        {/* hero — two-line headline; second line wears the brand gradient */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            marginTop: 72,
            lineHeight: 1.04,
            letterSpacing: "-0.035em",
            fontWeight: 300,
            gap: 4,
          }}
        >
          <div
            style={{
              display: "flex",
              fontSize: 76,
              color: "#fafafa",
              whiteSpace: "nowrap",
            }}
          >
            Your AI deleted the data.
          </div>
          <div
            style={{
              display: "flex",
              fontSize: 76,
              whiteSpace: "nowrap",
              backgroundImage:
                "linear-gradient(135deg, #0d3d4e 0%, #5a8a96 45%, #bfd1ce 100%)",
              backgroundClip: "text",
              color: "transparent",
            }}
          >
            The derived memories didn’t.
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
