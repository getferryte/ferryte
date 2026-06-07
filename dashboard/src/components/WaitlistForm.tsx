"use client";

import { useState } from "react";

type Status = "idle" | "submitting" | "ok" | "error";

const FIELD =
  "w-full rounded-lg border border-rule bg-surface px-4 py-3 text-[14px] text-ink " +
  "placeholder:text-ink-4 transition-colors duration-fast ease-out " +
  "hover:border-rule-2 focus:border-royal focus-visible:outline-none";

const LABEL =
  "mb-2 block font-mono text-[10.5px] uppercase tracking-[0.18em] text-ink-3";

export function WaitlistForm({ tier = "cloud" }: { tier?: string }) {
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("submitting");
    setError(null);

    const form = e.currentTarget;
    const data = new FormData(form);
    const payload = {
      email: String(data.get("email") || ""),
      company: String(data.get("company") || ""),
      stack: String(data.get("stack") || ""),
      concern: String(data.get("concern") || ""),
      tier,
    };

    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        throw new Error(body.error || "request_failed");
      }
      setStatus("ok");
      form.reset();
    } catch (err) {
      setStatus("error");
      setError(
        err instanceof Error && err.message === "invalid_email"
          ? "That email doesn't look right — mind checking it?"
          : "Something broke on our end. Email hello@ferryte.dev and we'll add you by hand.",
      );
    }
  }

  if (status === "ok") {
    return (
      <div className="rounded-xl border border-royal/40 bg-surface p-8 shadow-[0_24px_64px_-24px_rgba(90,138,150,0.45)]">
        <div className="flex items-center gap-2.5">
          <span className="dot dot-ok dot-live" />
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-ok">
            You&rsquo;re on the list
          </span>
        </div>
        <p className="mt-5 text-body text-ink-2">
          Thanks — we read every signup by hand. If your stack is a fit for the
          design-partner cohort, you&rsquo;ll hear from the founder directly.
          Want to skip the queue?{" "}
          <a
            className="text-ink underline-offset-4 hover:underline"
            href="#book-a-call"
          >
            Book a call
          </a>
          .
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-xl border border-rule bg-surface p-7 sm:p-8"
    >
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label className={LABEL} htmlFor="wl-email">
            Work email *
          </label>
          <input
            id="wl-email"
            name="email"
            type="email"
            required
            autoComplete="email"
            placeholder="you@company.com"
            className={FIELD}
          />
        </div>

        <div>
          <label className={LABEL} htmlFor="wl-company">
            Company
          </label>
          <input
            id="wl-company"
            name="company"
            type="text"
            placeholder="Acme AI"
            className={FIELD}
          />
        </div>

        <div>
          <label className={LABEL} htmlFor="wl-stack">
            Memory stack
          </label>
          <input
            id="wl-stack"
            name="stack"
            type="text"
            placeholder="Mem0 · pgvector · AgentCore…"
            className={FIELD}
          />
        </div>

        <div className="sm:col-span-2">
          <label className={LABEL} htmlFor="wl-concern">
            What leak worries you?
          </label>
          <textarea
            id="wl-concern"
            name="concern"
            rows={3}
            placeholder="e.g. multi-tenant agent; GDPR deletion requests; not sure derived summaries get cleared."
            className={`${FIELD} resize-none`}
          />
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-4">
        <button
          type="submit"
          disabled={status === "submitting"}
          className="inline-flex items-center gap-1.5 rounded-full bg-royal px-5 py-3 text-[14px] font-medium text-white shadow-[0_8px_36px_-12px_rgba(90,138,150,0.55)] transition-colors duration-fast ease-out hover:bg-royal-2 disabled:opacity-60"
        >
          {status === "submitting" ? "Joining…" : "Join the waitlist"}
          <span aria-hidden>→</span>
        </button>
        <span className="text-caption text-ink-3">
          No spam. We email design-partner fits only.
        </span>
      </div>

      {status === "error" && error && (
        <p className="mt-4 text-[13px] text-issue" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
