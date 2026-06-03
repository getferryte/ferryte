import sample from "../sample-report.json";

export type Severity = "pass" | "warn" | "fail";

export interface Finding {
  severity: Severity;
  code: string;
  summary: string;
  path: string[];
  detail: Record<string, unknown>;
}

export interface ScenarioResultRow {
  scenario: string;
  severity: Severity;
  passed: boolean;
  artifacts_seeded: number;
  artifacts_deleted: number;
  duration_ms: number;
  coverage: Record<string, unknown>;
  findings: Finding[];
  blast: Array<{
    source_id: string;
    artifact_count: number;
    retrieval_count: number;
    min_confidence: number;
    artifacts: Array<{
      artifact_id: string;
      backend: string;
      kind: string;
      tenant_id?: string;
      content?: string;
      confidence?: number;
    }>;
    retrievals: Array<{
      backend: string;
      query: string;
      artifact_id?: string;
      score?: number;
      tenant_id?: string;
      content?: string;
    }>;
    blindspots: Array<{ backend: string; kind: string; detail: string }>;
  }>;
}

export interface CoverageReport {
  summary: {
    scenarios_run: number;
    passed: number;
    warned: number;
    failed: number;
    blindspot_observations: number;
    structural_gaps: number;
    backends_instrumented: string[];
  };
  backends: Array<{
    backend: string;
    adapter: string;
    client_count: number;
    capabilities: string[];
  }>;
  scenarios: ScenarioResultRow[];
  blindspots: Array<{
    backend: string;
    kind: string;
    detail: string;
    observed_at: number;
  }>;
  structural_gaps: Array<{
    backend: string;
    capability: string;
    detail: string;
  }>;
  lineage_counts: Record<string, number>;
}

export interface FullReport {
  generated_at: string;
  coverage: CoverageReport;
  results: ScenarioResultRow[];
}

const API_BASE = process.env.FERRYTE_API_BASE || "http://127.0.0.1:8787";

export async function loadReport(): Promise<FullReport> {
  try {
    const res = await fetch(`${API_BASE}/api/reports/latest`, {
      next: { revalidate: 5 },
    });
    if (res.ok) {
      return (await res.json()) as FullReport;
    }
  } catch {
    /* fall through to sample */
  }
  return sample as FullReport;
}
