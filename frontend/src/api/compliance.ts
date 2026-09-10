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
