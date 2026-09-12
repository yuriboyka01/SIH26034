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
    `/inspections/${inspectionId}/product-info`
  );
  return response.data;
}

/**
 * Merge product info extracted independently from each uploaded evidence
 * image into a single consolidated view of the physical package.
 *
 * Why this exists: a real package usually needs 2+ photos (front + back) to
 * capture every mandatory declaration. Each photo is OCR'd/extracted on its
 * own, so any single ProductInfo record will show "Not detected" for
 * whatever the OTHER photo happened to show. Picking product_info_list[0]
 * (the previous behaviour) silently threw away every other image's data.
 *
 * Precedence per field: DETECTED > UNCERTAIN > NOT_DETECTED, i.e. if the
 * declaration was confidently read on ANY image of the package, treat it as
 * present on the package.
 */
const DETECTION_RANK: Record<ExtractedField['detection_status'], number> = {
  DETECTED: 0,
  UNCERTAIN: 1,
  NOT_DETECTED: 2,
};

export function mergeProductInfoList(list: ProductInfo[]): ProductInfo | null {
  if (!list.length) return null;
  if (list.length === 1) return list[0];

  const byField = new Map<string, ExtractedField>();
  for (const info of list) {
    for (const field of info.fields || []) {
      const existing = byField.get(field.field_name);
      if (!existing || DETECTION_RANK[field.detection_status] < DETECTION_RANK[existing.detection_status]) {
        byField.set(field.field_name, field);
      }
    }
  }

  const valueOf = (name: string) => byField.get(name)?.value ?? null;

  return {
    product_name: valueOf('product_name'),
    brand_name: valueOf('brand_name'),
    manufacturer: valueOf('manufacturer'),
    net_quantity: valueOf('net_quantity'),
    mrp: valueOf('mrp'),
    manufacturing_date: valueOf('manufacturing_date'),
    expiry_date: valueOf('expiry_date'),
    batch_number: valueOf('batch_number'),
    country_of_origin: valueOf('country_of_origin'),
    ingredients: valueOf('ingredients'),
    license_number: valueOf('license_number'),
    customer_care: valueOf('customer_care'),
    warnings: valueOf('warnings'),
    fields: Array.from(byField.values()),
    total_blocks_processed: list.reduce((sum, i) => sum + (i.total_blocks_processed || 0), 0),
    extraction_version: list.find((i) => i.extraction_version)?.extraction_version ?? null,
  };
}
