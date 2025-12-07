const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface MapObject {
  id: number;
  lat: number;
  lon: number;
  pipeline_id?: string;
  status: "unknown" | "clean" | "defect";
  criticality: "normal" | "medium" | "high";
  popup_data: {
    object_name: string;
    object_type: string;
    year?: number;
    material?: string;
    last_check_date?: string;
    method?: string;
    quality_grade?: string;
    ml_label?: string;
    max_depth?: number;
    defect_count: number;
  };
}

export interface MapFilters {
  pipeline_id?: string;
  method?: string;
  date_from?: string;
  date_to?: string;
  param_min?: number;
  param_max?: number;
}

export async function fetchMapObjects(filters: MapFilters = {}): Promise<MapObject[]> {
  const params = new URLSearchParams();
  
  if (filters.pipeline_id) params.append("pipeline_id", filters.pipeline_id);
  if (filters.method) params.append("method", filters.method);
  if (filters.date_from) params.append("date_from", filters.date_from);
  if (filters.date_to) params.append("date_to", filters.date_to);
  if (filters.param_min !== undefined) params.append("param_min", filters.param_min.toString());
  if (filters.param_max !== undefined) params.append("param_max", filters.param_max.toString());

  const url = `${API_BASE_URL}/map-objects?${params.toString()}`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch map objects: ${response.statusText}`);
  }
  
  return response.json();
}

export interface ObjectSearchParams {
  search?: string;
  pipeline_id?: string;
  method?: string;
  defect_type?: string;
  page?: number;
  size?: number;
  sort_by?: "date" | "depth" | "name";
  order?: "asc" | "desc";
}

export interface ObjectTableRow {
  id: number;
  object_name: string;
  pipeline_id?: string;
  object_type: string;
  last_check_date?: string;
  method?: string;
  status: string;
  defect_type?: string;
  max_depth: number;
}

export async function searchObjects(params: ObjectSearchParams = {}): Promise<ObjectTableRow[]> {
  const queryParams = new URLSearchParams();
  
  if (params.search) queryParams.append("search", params.search);
  if (params.pipeline_id) queryParams.append("pipeline_id", params.pipeline_id);
  if (params.method) queryParams.append("method", params.method);
  if (params.defect_type) queryParams.append("defect_type", params.defect_type);
  if (params.page) queryParams.append("page", params.page.toString());
  if (params.size) queryParams.append("size", params.size.toString());
  if (params.sort_by) queryParams.append("sort_by", params.sort_by);
  if (params.order) queryParams.append("order", params.order);

  const url = `${API_BASE_URL}/objects/search?${queryParams.toString()}`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to search objects: ${response.statusText}`);
  }
  
  return response.json();
}

// Dashboard Statistics Types
export interface DefectByMethod {
  method: string;
  count: number;
}

export interface DefectByCriticality {
  criticality: string;
  count: number;
}

export interface TopRisk {
  object_id: number;
  object_name: string;
  pipeline_id?: string;
  criticality?: string;
  defect_count: number;
  max_depth?: number;
}

export interface InspectionsByYear {
  year: number;
  count: number;
}

export interface DashboardStats {
  defects_by_method: DefectByMethod[];
  defects_by_criticality: DefectByCriticality[];
  top_risks: TopRisk[];
  inspections_by_year: InspectionsByYear[];
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const url = `${API_BASE_URL}/dashboard/stats`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard stats: ${response.statusText}`);
  }
  
  return response.json();
}

// File Import History Types
export interface FileImportHistory {
  import_id: number;
  filename: string;
  file_type: string;
  file_size?: number;
  created: number;
  updated: number;
  defects_created: number;
  error_count: number;
  imported_at: string;
}

export async function fetchImportHistory(): Promise<FileImportHistory[]> {
  const url = `${API_BASE_URL}/csv/imports/`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch import history: ${response.statusText}`);
  }
  
  return response.json();
}

// ML Metrics Types
export interface MLMetrics {
  metric_id: number;
  training_accuracy: number;
  test_accuracy: number;
  train_samples: number;
  test_samples: number;
  training_report: {
    [key: string]: any;
  };
  test_report: {
    [key: string]: any;
  };
  label_distribution: {
    [key: string]: number;
  };
  predicted_count: number;
  created_at: string;
}

export async function fetchMLMetrics(): Promise<MLMetrics[]> {
  const url = `${API_BASE_URL}/ml/metrics`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch ML metrics: ${response.statusText}`);
  }
  
  return response.json();
}

export async function fetchLatestMLMetrics(): Promise<MLMetrics> {
  const url = `${API_BASE_URL}/ml/metrics/latest`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch latest ML metrics: ${response.statusText}`);
  }
  
  return response.json();
}

// Reports
export async function downloadPipelineReport(pipelineId: string): Promise<void> {
  const url = `${API_BASE_URL}/reports/${pipelineId}/pdf`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Failed to download report: ${response.statusText}`);
  }
  
  // Get blob and create download link
  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = `Report_${pipelineId}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
}

