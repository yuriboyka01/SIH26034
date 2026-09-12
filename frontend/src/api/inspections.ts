/**
 * Inspection and Dashboard API functions.
 */

import client from './client';

export interface InspectionImage {
  id: string;
  original_filename: string;
  stored_filename: string;
  mime_type: string;
  file_size: number;
  image_type: string;
  url: string;
  created_at: string;
}

export interface Inspection {
  id: string;
  inspection_number: string;
  product_name: string;
  brand: string;
  status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  establishment_name?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  images: InspectionImage[];
}

export interface InspectionListItem {
  id: string;
  inspection_number: string;
  product_name: string;
  brand: string;
  status: string;
  compliance_status?: string;
  created_at: string;
  image_count: number;
}

export interface CreateInspectionRequest {
  product_name: string;
  brand: string;
  establishment_name?: string;
  latitude?: number;
  longitude?: number;
}

export interface DashboardStats {
  total: number;
  created: number;
  images_uploaded: number;
  processing: number;
  completed: number;
  needs_review: number;
}

export async function createInspection(data: CreateInspectionRequest): Promise<Inspection> {
  const response = await client.post<Inspection>('/inspections', data);
  return response.data;
}

export interface GetInspectionsParams {
  search?: string;
  status?: string;
  compliance_status?: string;
  date_from?: string;
  date_to?: string;
  skip?: number;
  limit?: number;
}

export interface PaginatedInspections {
  items: InspectionListItem[];
  totalCount: number;
}

export async function getInspections(params?: GetInspectionsParams): Promise<PaginatedInspections> {
  const response = await client.get<InspectionListItem[]>('/inspections', { params });
  return {
    items: response.data,
    totalCount: parseInt(response.headers['x-total-count'] || '0', 10),
  };
}

export async function getInspection(id: string): Promise<Inspection> {
  const response = await client.get<Inspection>(`/inspections/${id}`);
  return response.data;
}

export async function uploadInspectionImage(
  inspectionId: string,
  file: File,
  imageType: string = 'OTHER',
  onProgress?: (progress: number) => void
): Promise<InspectionImage> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('image_type', imageType);

  const response = await client.post<InspectionImage>(
    `/inspections/${inspectionId}/images`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (event.total && onProgress) {
          onProgress(Math.round((event.loaded * 100) / event.total));
        }
      },
    }
  );
  return response.data;
}

export async function deleteInspectionImage(
  inspectionId: string,
  imageId: string
): Promise<void> {
  await client.delete(`/inspections/${inspectionId}/images/${imageId}`);
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await client.get<DashboardStats>('/dashboard/stats');
  return response.data;
}
