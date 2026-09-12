import client from './client';

export type ComplianceStatus = 'PASS' | 'FAIL' | 'REVIEW' | 'NOT_APPLICABLE';
export type RuleSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface RuleResult {
  rule_id: string;
  rule_name: string;
  status: ComplianceStatus;
  severity: RuleSeverity;
  message: string;
  field?: string;
  expected: string;
  actual?: string;
  evidence?: any;
  source_reference: string;
  category?: string;
  confidence?: number;
  remediation?: string;
  /** Which evidence image this specific finding's evidence came from. Set during merge. */
  image_id?: string;
}

export interface ComplianceReport {
  inspection_id: string;
  image_id: string;
  overall_status: ComplianceStatus;
  total_rules_checked: number;
  passed_count: number;
  failed_count: number;
  review_count: number;
  not_applicable_count: number;
  rule_results: RuleResult[];
  category_breakdown?: {
    category: string;
    label: string;
    passed_count: number;
    failed_count: number;
    review_count: number;
    not_applicable_count: number;
    total: number;
  }[];
}

export interface ComplianceResponse {
  inspection_id: string;
  overall_status: ComplianceStatus;
  reports: ComplianceReport[];
}

export const runComplianceAnalysis = async (inspectionId: string): Promise<ComplianceResponse> => {
  const response = await client.post<ComplianceResponse>(`/inspections/${inspectionId}/compliance`);
  return response.data;
};

export const getComplianceReports = async (inspectionId: string): Promise<ComplianceResponse> => {
  const response = await client.get<ComplianceResponse>(`/inspections/${inspectionId}/compliance`);
  return response.data;
};

/**
 * Consolidate the per-image compliance reports into one product-level verdict.
 *
 * The backend evaluates rules separately for each evidence image (one
 * ComplianceReport per photo), because a single photo often can't show every
 * mandatory declaration on the package. Rendering each per-image report
 * on its own produces contradictory-looking results for one physical
 * product — e.g. "Consumer contact: FAIL" from the front-label photo next
 * to "Consumer contact: PASS" from the back-label photo. This merges them
 * by rule_id so each requirement gets one verdict: PASS if satisfied on
 * ANY image, otherwise the least-bad outcome across the images checked.
 */
const STATUS_RANK: Record<ComplianceStatus, number> = {
  PASS: 0,
  NOT_APPLICABLE: 1,
  REVIEW: 2,
  FAIL: 3,
};

export function mergeComplianceReports(reports: ComplianceReport[]): ComplianceReport {
  if (reports.length === 1) return reports[0];

  const byRule = new Map<string, RuleResult>();
  for (const report of reports) {
    for (const result of report.rule_results) {
      const existing = byRule.get(result.rule_id);
      if (!existing || STATUS_RANK[result.status] < STATUS_RANK[existing.status]) {
        byRule.set(result.rule_id, { ...result, image_id: report.image_id });
      }
    }
  }

  const merged = Array.from(byRule.values());
  const counts: Record<ComplianceStatus, number> = { PASS: 0, FAIL: 0, REVIEW: 0, NOT_APPLICABLE: 0 };
  for (const r of merged) counts[r.status]++;

  type CategoryBucket = NonNullable<ComplianceReport['category_breakdown']>[number];
  const categoryMap = new Map<string, CategoryBucket>();
  for (const r of merged) {
    const cat = r.category || 'UNKNOWN';
    if (!categoryMap.has(cat)) {
      categoryMap.set(cat, { category: cat, label: cat, passed_count: 0, failed_count: 0, review_count: 0, not_applicable_count: 0, total: 0 });
    }
    const bucket = categoryMap.get(cat)!;
    bucket.total += 1;
    if (r.status === 'PASS') bucket.passed_count++;
    else if (r.status === 'FAIL') bucket.failed_count++;
    else if (r.status === 'REVIEW') bucket.review_count++;
    else bucket.not_applicable_count++;
  }
  // Carry over the human-readable category labels from whichever source report has them.
  for (const report of reports) {
    for (const cat of report.category_breakdown || []) {
      const bucket = categoryMap.get(cat.category);
      if (bucket) bucket.label = cat.label;
    }
  }

  // Mirrors the backend engine's own overall-status logic (see compliance/engine.py).
  const hasHighCriticalFail = merged.some((r) => r.status === 'FAIL' && (r.severity === 'CRITICAL' || r.severity === 'HIGH'));
  const overall_status: ComplianceStatus = hasHighCriticalFail
    ? 'FAIL'
    : counts.REVIEW > 0 || counts.FAIL > 0
    ? 'REVIEW'
    : 'PASS';

  return {
    inspection_id: reports[0].inspection_id,
    image_id: 'merged',
    overall_status,
    total_rules_checked: merged.length,
    passed_count: counts.PASS,
    failed_count: counts.FAIL,
    review_count: counts.REVIEW,
    not_applicable_count: counts.NOT_APPLICABLE,
    rule_results: merged,
    category_breakdown: Array.from(categoryMap.values()),
  };
}
