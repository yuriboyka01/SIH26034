/**
 * Reports API functions for downloading PDF and DOCX reports.
 */

import client from './client';

export const downloadReport = async (inspectionId: string, format: 'pdf' | 'docx') => {
  const response = await client.get(`/inspections/${inspectionId}/compliance/report.${format}`, {
    responseType: 'blob', // Important for downloading files
  });

  // Create a blob URL and trigger download
  const blob = new Blob([response.data], {
    type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  
  // Try to extract filename from content-disposition header if available, otherwise use default
  const contentDisposition = response.headers['content-disposition'];
  let filename = `Compliance_Report_INS_${inspectionId}.${format}`;
  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
    if (filenameMatch && filenameMatch.length === 2) {
      filename = filenameMatch[1];
    }
  }
  
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  
  // Cleanup
  link.parentNode?.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export const downloadShowCause = async (inspectionId: string, format: 'pdf' | 'docx') => {
  const response = await client.get(`/inspections/${inspectionId}/show-cause/report.${format}`, {
    responseType: 'blob', // Important for downloading files
  });

  // Create a blob URL and trigger download
  const blob = new Blob([response.data], {
    type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  
  // Try to extract filename from content-disposition header if available, otherwise use default
  const contentDisposition = response.headers['content-disposition'];
  let filename = `SCN-${inspectionId}.${format}`;
  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
    if (filenameMatch && filenameMatch.length === 2) {
      filename = filenameMatch[1];
    }
  }
  
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  
  // Cleanup
  link.parentNode?.removeChild(link);
  window.URL.revokeObjectURL(url);
};
