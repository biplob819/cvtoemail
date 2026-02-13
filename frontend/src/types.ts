export interface PersonalInfo {
  name: string;
  email: string;
  phone: string;
  location: string;
  linkedin?: string;
  website?: string;
}

export interface WorkExperience {
  title: string;
  company: string;
  duration: string;
  achievements: string[];
}

export interface Education {
  degree: string;
  institution: string;
  year: string;
  details?: string;
}

export interface Certification {
  name: string;
  issuer?: string;
  year?: string;
}

export interface CVData {
  id?: number;
  personal_info: PersonalInfo;
  summary: string;
  work_experience: WorkExperience[];
  education: Education[];
  skills: string[];
  certifications: Certification[];
  raw_text?: string;
  updated_at?: string;
}

// ---------------------------------------------------------------------------
// Job Sources (Milestone 2)
// ---------------------------------------------------------------------------

export interface JobSource {
  id: number;
  url: string;
  portal_name: string;
  filters_description: string;
  is_active: boolean;
  last_checked: string | null;
  created_at: string | null;
  jobs_found: number;
}

export interface JobSourceCreate {
  url: string;
  portal_name: string;
  filters_description?: string;
}

export interface JobSourceUpdate {
  url?: string;
  portal_name?: string;
  filters_description?: string;
  is_active?: boolean;
}

export interface URLCheckResult {
  reachable: boolean;
  status_code: number | null;
  message: string;
}

export interface ScanResult {
  source_id: number;
  jobs_found: number;
  new_jobs: number;
  message: string;
}

// ---------------------------------------------------------------------------
// Jobs (Milestone 2 model, full UI in Milestone 3)
// ---------------------------------------------------------------------------

export interface Job {
  id: number;
  source_id: number;
  source_name?: string;
  title: string;
  company: string;
  location: string;
  description: string;
  url: string;
  status: "New" | "Viewed" | "CV Generated" | "CV Sent" | "Skipped";
  is_new: boolean;
  discovered_at: string;
  cv_pdf_path?: string;
  cv_generated_at?: string;
}

export interface JobStats {
  total_jobs: number;
  new_jobs_24h: number;
  new_jobs_7d: number;
  by_status: Record<string, number>;
}

export interface JobFilters {
  source_id?: number;
  status?: string;
  date_from?: string;
  date_to?: string;
}

export interface JobUpdateRequest {
  status?: "New" | "Viewed" | "CV Generated" | "CV Sent" | "Skipped";
  is_new?: boolean;
}
