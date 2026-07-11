import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-[70vh] items-center px-8 sm:px-12 lg:px-20">
      <div className="mx-auto w-full max-w-3xl">
        <div className="rounded-lg border border-rule bg-surface p-7 font-mono text-[13px] leading-[1.8]">
          <div className="text-ink">
            <span className="select-none text-royal">› </span>
            ferryte why &quot;this page&quot;
          </div>
          <div className="mt-2 text-issue">
            #1 phantom-memory · conf 1.00
          </div>
          <div className="text-ink-2">
            {"   "}the source was revoked, but you still remember the URL.
          </div>
          <div className="text-ink-3">{"   "}retrieved 1× into context · just now</div>
          <div className="mt-3 text-ok">
            fix: <Link href="/" className="underline decoration-dotted underline-offset-4 hover:text-ink">→ back to ferryte.dev</Link>
          </div>
        </div>

        <p className="mt-6 text-[14px] text-ink-3">
          404 — this page isn&rsquo;t in the lineage graph. Try the{" "}
          <Link href="/" className="text-ink-2 underline-offset-4 hover:text-ink hover:underline">
            homepage
          </Link>
          , the{" "}
          <Link href="/benchmark" className="text-ink-2 underline-offset-4 hover:text-ink hover:underline">
            Memory Report
          </Link>
          , or the{" "}
          <Link href="/audit" className="text-ink-2 underline-offset-4 hover:text-ink hover:underline">
            audit
          </Link>
          .
        </p>
      </div>
    </main>
  );
}
