/**
 * Dashboard API functions for compliance analytics.
 */

import client from './client';

export interface ComplianceKPIs {
  total_inspections: number;
  compliant_count: number;
  non_compliant_count: number;
  review_count: number;
  not_analysed_count: number;
  compliance_rate: number;
}

export interface ViolationSummaryItem {
  rule_id: string;
  rule_name: string;
  count: number;
}

export interface RecentInspectionItem {
  id: string;
  inspection_number: string;
  product_name: string;
  brand: string;
  created_at: string;
  compliance_status: string;
}

export interface DashboardAnalyticsResponse {
  kpis: ComplianceKPIs;
  top_violations: ViolationSummaryItem[];
  recent_inspections: RecentInspectionItem[];
}

export async function getDashboardAnalytics(): Promise<DashboardAnalyticsResponse> {
  const response = await client.get<DashboardAnalyticsResponse>('/dashboard/analytics');
  return response.data;
}
