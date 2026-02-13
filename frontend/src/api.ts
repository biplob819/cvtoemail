import axios from "axios";
import type {
  CVData,
  JobSource,
  JobSourceCreate,
  JobSourceUpdate,
  URLCheckResult,
  ScanResult,
  Job,
  JobStats,
  JobFilters,
  JobUpdateRequest,
} from "./types";

const api = axios.create({
  baseURL: "",
});

// ---------------------------------------------------------------------------
// CV endpoints
// ---------------------------------------------------------------------------

export async function getCV(): Promise<CVData | null> {
  const { data } = await api.get<CVData | null>("/api/cv");
  return data;
}

export async function updateCV(data: CVData): Promise<CVData> {
  const { data: result } = await api.put<CVData>("/api/cv", data);
  return result;
}

export async function uploadCV(file: File): Promise<CVData> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<CVData>("/api/cv/upload", formData);
  return data;
}

export function getPreviewUrl(): string {
  return "/api/cv/preview";
}

export async function healthCheck(): Promise<{ status: string }> {
  const { data } = await api.get<{ status: string }>("/api/health");
  return data;
}

// ---------------------------------------------------------------------------
// Source endpoints (Milestone 2)
// ---------------------------------------------------------------------------

export async function getSources(): Promise<JobSource[]> {
  const { data } = await api.get<JobSource[]>("/api/sources");
  return data;
}

export async function getSource(id: number): Promise<JobSource> {
  const { data } = await api.get<JobSource>(`/api/sources/${id}`);
  return data;
}

export async function createSource(source: JobSourceCreate): Promise<JobSource> {
  const { data } = await api.post<JobSource>("/api/sources", source);
  return data;
}

export async function updateSource(
  id: number,
  source: JobSourceUpdate
): Promise<JobSource> {
  const { data } = await api.put<JobSource>(`/api/sources/${id}`, source);
  return data;
}

export async function deleteSource(id: number): Promise<void> {
  await api.delete(`/api/sources/${id}`);
}

export async function checkUrl(url: string): Promise<URLCheckResult> {
  const { data } = await api.post<URLCheckResult>("/api/sources/check-url", { url });
  return data;
}

export async function scanSource(id: number): Promise<ScanResult> {
  const { data } = await api.post<ScanResult>(`/api/sources/${id}/scan`);
  return data;
}

// ---------------------------------------------------------------------------
// Job endpoints (Milestone 3)
// ---------------------------------------------------------------------------

export async function getJobs(filters?: JobFilters): Promise<Job[]> {
  const params: Record<string, string> = {};
  if (filters?.source_id) params.source_id = String(filters.source_id);
  if (filters?.status) params.status = filters.status;
  if (filters?.date_from) params.date_from = filters.date_from;
  if (filters?.date_to) params.date_to = filters.date_to;
  
  const { data } = await api.get<Job[]>("/api/jobs", { params });
  return data;
}

export async function getJob(id: number): Promise<Job> {
  const { data } = await api.get<Job>(`/api/jobs/${id}`);
  return data;
}

export async function updateJob(id: number, update: JobUpdateRequest): Promise<Job> {
  const { data } = await api.put<Job>(`/api/jobs/${id}`, update);
  return data;
}

export async function bulkSkipJobs(jobIds: number[]): Promise<{ status: string; updated_count: number }> {
  const { data } = await api.post<{ status: string; updated_count: number }>(
    "/api/jobs/bulk-skip",
    { job_ids: jobIds }
  );
  return data;
}

export async function getJobStats(): Promise<JobStats> {
  const { data } = await api.get<JobStats>("/api/jobs/stats");
  return data;
}

export async function generateCV(jobId: number): Promise<{ status: string; message: string }> {
  const { data } = await api.post<{ status: string; message: string }>(
    `/api/jobs/${jobId}/generate-cv`
  );
  return data;
}

export function downloadCV(jobId: number): string {
  return `/api/jobs/${jobId}/cv`;
}

// ---------------------------------------------------------------------------
// Settings endpoints (Milestone 5)
// ---------------------------------------------------------------------------

export interface Settings {
  id: number;
  notification_email: string | null;
  smtp_host: string | null;
  smtp_port: number | null;
  smtp_user: string | null;
  smtp_password_set: boolean;
  openai_api_key_set: boolean;
  openai_model: string | null;
  scan_frequency: number | null;
  scan_window_start: string | null;
  scan_window_end: string | null;
}

export interface SettingsUpdate {
  notification_email?: string | null;
  smtp_host?: string;
  smtp_port?: number;
  smtp_user?: string | null;
  smtp_password?: string | null;
  openai_api_key?: string | null;
  openai_model?: string;
  scan_frequency?: number;
  scan_window_start?: string | null;
  scan_window_end?: string | null;
}

export async function getSettings(): Promise<Settings> {
  const { data } = await api.get<Settings>("/api/settings");
  return data;
}

export async function updateSettings(update: SettingsUpdate): Promise<Settings> {
  const { data } = await api.put<Settings>("/api/settings", update);
  return data;
}

export async function sendTestEmail(email: string): Promise<{ success: boolean; message: string }> {
  const { data } = await api.post<{ success: boolean; message: string }>(
    "/api/settings/test-email",
    { test_email: email }
  );
  return data;
}

// ---------------------------------------------------------------------------
// Dashboard endpoints (Milestone 6)
// ---------------------------------------------------------------------------

export interface DashboardStats {
  active_sources: number;
  new_jobs_24h: number;
  cvs_sent_7d: number;
  last_scan: string | null;
  total_jobs: number;
  total_applications: number;
}

export interface RecentJob {
  id: number;
  title: string;
  company: string;
  location: string | null;
  status: string;
  discovered_at: string;
  source_name: string;
}

export interface SystemStatus {
  celery_running: boolean;
  next_scan: string | null;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>("/api/dashboard/stats");
  return data;
}

export async function getRecentJobs(limit: number = 10): Promise<RecentJob[]> {
  const { data } = await api.get<RecentJob[]>("/api/dashboard/recent-jobs", { params: { limit } });
  return data;
}

export async function getSystemStatus(): Promise<SystemStatus> {
  const { data } = await api.get<SystemStatus>("/api/dashboard/system-status");
  return data;
}
