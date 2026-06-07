import { NextResponse } from "next/server";

/**
 * Waitlist intake for Ferryte Cloud / Enterprise.
 *
 * Zero-infra by design: there is no database. Each submission is
 *   1. validated,
 *   2. logged (visible in Vercel function logs), and
 *   3. forwarded to WAITLIST_WEBHOOK_URL if set.
 *
 * WAITLIST_WEBHOOK_URL can be a Slack incoming webhook, a Zapier/Make hook,
 * a Formspree endpoint, or any URL that accepts JSON. Until it's set,
 * submissions still succeed and are captured in the logs, so nothing is lost.
 */

export const runtime = "nodejs";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type Payload = {
  email?: unknown;
  company?: unknown;
  stack?: unknown;
  concern?: unknown;
  tier?: unknown;
};

function asString(v: unknown, max = 500): string {
  return typeof v === "string" ? v.trim().slice(0, max) : "";
}

export async function POST(request: Request) {
  let body: Payload;
  try {
    body = (await request.json()) as Payload;
  } catch {
    return NextResponse.json({ ok: false, error: "invalid_json" }, { status: 400 });
  }

  const email = asString(body.email, 254).toLowerCase();
  if (!EMAIL_RE.test(email)) {
    return NextResponse.json({ ok: false, error: "invalid_email" }, { status: 422 });
  }

  const entry = {
    source: "ferryte-cloud-waitlist",
    email,
    company: asString(body.company, 120),
    stack: asString(body.stack, 200),
    concern: asString(body.concern, 1000),
    tier: asString(body.tier, 40) || "cloud",
    submittedAt: new Date().toISOString(),
  };

  // Always log — captured in Vercel logs even before a webhook is configured.
  console.log("[waitlist]", JSON.stringify(entry));

  const webhook = process.env.WAITLIST_WEBHOOK_URL;
  if (webhook) {
    try {
      await fetch(webhook, {
        method: "POST",
        headers: { "content-type": "application/json" },
        // Slack-friendly `text` plus the structured entry for everything else.
        body: JSON.stringify({
          text:
            `New Ferryte ${entry.tier} waitlist signup\n` +
            `• ${entry.email}` +
            (entry.company ? ` (${entry.company})` : "") +
            (entry.stack ? `\n• stack: ${entry.stack}` : "") +
            (entry.concern ? `\n• concern: ${entry.concern}` : ""),
          ...entry,
        }),
      });
    } catch (err) {
      // Never fail the user's submission because the webhook is down.
      console.error("[waitlist] webhook forward failed", err);
    }
  }

  return NextResponse.json({ ok: true });
}
