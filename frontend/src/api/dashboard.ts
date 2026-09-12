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

export interface RepeatOffenderItem {
  brand: string;
  total_inspections: number;
  fail_count: number;
  review_count: number;
  top_violation_rule_id: string | null;
  top_violation_rule_name: string | null;
  top_violation_count: number;
  latest_inspection_id: string;
  latest_inspection_number: string;
  latest_inspection_date: string;
}

export interface GeoPointItem {
  inspection_id: string;
  inspection_number: string;
  brand: string;
  product_name: string;
  establishment_name: string | null;
  latitude: number;
  longitude: number;
  compliance_status: string;
}

export interface DashboardAnalyticsResponse {
  kpis: ComplianceKPIs;
  top_violations: ViolationSummaryItem[];
  recent_inspections: RecentInspectionItem[];
  repeat_offenders: RepeatOffenderItem[];
  geo_points: GeoPointItem[];
}

export async function getDashboardAnalytics(): Promise<DashboardAnalyticsResponse> {
  const response = await client.get<DashboardAnalyticsResponse>('/dashboard/analytics');
  return response.data;
}
