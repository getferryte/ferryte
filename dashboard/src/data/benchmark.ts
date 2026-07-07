// The Memory Report — leaderboard data (delete-after-revoke = the phantom-memory class).
//
// Numbers reproducible from `benchmark/run.py`:
//   without Ferryte:  python -m benchmark.run --backends X --scenarios all --embedder openai --summarizer openai
//   with Ferryte:     ... --with-ferryte   (enables lineage-driven cascade delete)
//
// Keep this file in sync with the latest results before publishing.

export type Verdict = "pass" | "warn" | "fail" | "blind" | "pending";

export interface ScenarioDef {
  id: string;
  label: string;
  blurb: string;
}

export interface BackendRow {
  name: string;
  kind: string;
  tested: boolean;
  // Naive baseline (delete the source only, no derived-memory cascade)
  before: { cells: Record<string, Verdict>; score: number | null };
  // With Ferryte lineage-driven cascade enabled
  after: { cells: Record<string, Verdict>; score: number | null };
  note?: string;
}

export const SCENARIOS: ScenarioDef[] = [
  {
    id: "source-revocation",
    label: "Source revocation",
    blurb: "Delete a source via the real API. Can the agent still surface it?",
  },
  {
    id: "cross-tenant-isolation",
    label: "Cross-tenant",
    blurb: "Can tenant A retrieve something only tenant B ever stored?",
  },
  {
    id: "stale-fact",
    label: "Stale fact",
    blurb: "After an overwrite, does the stale value still outrank the fresh one?",
  },
  {
    id: "memory-poisoning",
    label: "Poisoning",
    blurb: "Does injected low-trust content survive into retrieved answers?",
  },
];

// pass = forgot cleanly · fail = leaked · warn = partial · blind = unverifiable
export const RESULTS: BackendRow[] = [
  {
    name: "AWS Bedrock AgentCore",
    kind: "Native framework · semantic long-term memory",
    tested: true,
    before: {
      score: 50,
      cells: {
        "source-revocation": "fail",
        "cross-tenant-isolation": "pass",
        "stale-fact": "fail",
        "memory-poisoning": "pass",
      },
    },
    after: {
      score: 75,
      cells: {
        "source-revocation": "pass",
        "cross-tenant-isolation": "pass",
        "stale-fact": "fail",
        "memory-poisoning": "pass",
      },
    },
    note: "Verified live 2026-06-29 (50% → 75%). Ferryte's cascade fires BatchDeleteMemoryRecords after DeleteEvent — exactly what AWS's own docs recommend — flipping source-revocation FAIL → PASS. stale-fact still FAILs: it needs versioning, not a deletion cascade, so we don't claim to fix it.",
  },
  {
    name: "Vector store + app summary",
    kind: "pgvector · Chroma · Qdrant · in-memory (identical)",
    tested: true,
    before: {
      score: 25,
      cells: {
        "source-revocation": "fail",
        "cross-tenant-isolation": "pass",
        "stale-fact": "warn",
        "memory-poisoning": "fail",
      },
    },
    after: {
      score: 50,
      cells: {
        "source-revocation": "pass",
        "cross-tenant-isolation": "pass",
        "stale-fact": "warn",
        "memory-poisoning": "fail",
      },
    },
    note: "The raw row delete is clean — every store behaves the same. The leak is in the summary layer on top; Ferryte's lineage cascade clears the derived summary in lockstep with the source.",
  },
];

export const META = {
  embedder: "text-embedding-3-small",
  summarizer: "gpt-4o-mini",
  harness: "ferryte benchmark/ (open source)",
  updated: "2026-06-29",
  note: "All scores are reproducible — the 'with Ferryte' column uses the same harness with `--with-ferryte`.",
};
