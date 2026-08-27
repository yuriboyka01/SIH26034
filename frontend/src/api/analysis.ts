/**
 * Analysis API client — wraps the Phase 2 OCR analysis endpoints.
 * All HTTP calls go through the centralized axios client.
 */

import client from './client';

export interface OCRBlock {
  text: string;
  raw_text: string;
  confidence: number;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
}

export interface OCRData {
  engine: string;
  engine_version: string | null;
  full_text: string;
  processing_time_ms: number | null;
  preprocessing_applied: string[];
  blocks: OCRBlock[];
}

export interface QualityData {
  status: 'GOOD' | 'FAIR' | 'POOR';
  blur_score: number | null;
  brightness_score: number | null;
  issues: string[];
}

export interface ImageAnalysisResult {
  image_id: string;
  status: 'OK' | 'ERROR' | 'NOT_ANALYSED';
  quality: QualityData | null;
  ocr: OCRData | null;
  error?: string;
}

export interface AnalysisResponse {
  inspection_id: string;
  status: string;
  images: ImageAnalysisResult[];
}

/** Trigger OCR analysis on all images of an inspection. */
export async function analyzeInspection(inspectionId: string): Promise<AnalysisResponse> {
  const response = await client.post<AnalysisResponse>(
    `/api/inspections/${inspectionId}/analyze`
  );
  return response.data;
}

/** Get persisted OCR results without re-running analysis. */
export async function getAnalysisResults(inspectionId: string): Promise<AnalysisResponse> {
  const response = await client.get<AnalysisResponse>(
    `/api/inspections/${inspectionId}/analysis`
  );
  return response.data;
}
