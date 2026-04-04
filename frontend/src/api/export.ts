import { API_BASE } from './client';

export type ReportType = 'spaces' | 'doors-windows' | 'walls' | 'slabs' | 'quantities' | 'summary' | 'issues';
export type ExportFormat = 'xlsx' | 'csv' | 'pdf';

export const getExportUrl = (projectId: string, reportType: ReportType, format: ExportFormat) =>
  `${API_BASE}/api/models/${projectId}/export/${reportType}?format=${format}`;

export const getReportData = async (projectId: string, reportType: ReportType) => {
  const res = await fetch(`${API_BASE}/api/models/${projectId}/reports/${reportType}`);
  return res.json();
};
