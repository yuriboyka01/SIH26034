/**
 * Phase 3: Product Information API client.
 * Wraps the GET /api/inspections/{id}/product-info endpoint.
 */

import client from './client';

export interface FieldEvidence {
  source_text: string;
  confidence: number;
  bbox: [number, number, number, number] | null;
}

export interface ExtractedField {
  field_name: string;
  value: string | null;
  detection_status: 'DETECTED' | 'NOT_DETECTED' | 'UNCERTAIN';
  evidence: FieldEvidence | null;
}

export interface ProductInfo {
  product_name: string | null;
  brand_name: string | null;
  manufacturer: string | null;
  net_quantity: string | null;
  mrp: string | null;
  manufacturing_date: string | null;
  expiry_date: string | null;
  batch_number: string | null;
  country_of_origin: string | null;
  ingredients: string | null;
  license_number: string | null;
  customer_care: string | null;
  warnings: string | null;
  fields: ExtractedField[];
  total_blocks_processed: number | null;
  extraction_version: string | null;
}

export interface ProductInfoResponse {
  inspection_id: string;
  status: string;
  product_info_list: ProductInfo[];
}

/** Fetch structured product info for an inspection (after analysis). */
export async function getProductInfo(inspectionId: string): Promise<ProductInfoResponse> {
  const response = await client.get<ProductInfoResponse>(
    `/api/inspections/${inspectionId}/product-info`
  );
  return response.data;
}
