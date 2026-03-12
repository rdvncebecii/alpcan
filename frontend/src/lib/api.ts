const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export interface StudySummary {
  id: string;
  patient_id: string;
  patient_name: string;
  modality: "CT" | "CXR";
  study_date: string;
  description: string | null;
  status: "uploaded" | "queued" | "processing" | "completed" | "error";
  nodule_count: number | null;
  lung_rads: string | null;
}

export interface NoduleFinding {
  id: number;
  location: string;
  size_mm: number;
  volume_mm3: number | null;
  density: string;
  lung_rads: string;
  malignancy_score: number;
  recommendation: string;
}

export interface LungRADSReport {
  study_id: string;
  patient_id: string;
  report_date: string;
  overall_lung_rads: string;
  nodules: NoduleFinding[];
  cxr_ensemble_score: number | null;
  cxr_recommendation: string | null;
  summary_tr: string;
  recommendation_tr: string;
}

export interface HealthStatus {
  status: string;
  service: string;
}

export const api = {
  health: () => fetchAPI<HealthStatus>("/health"),
  studies: {
    list: (params?: { modality?: string; status?: string }) => {
      const query = new URLSearchParams(params as Record<string, string>).toString();
      return fetchAPI<StudySummary[]>(`/studies${query ? `?${query}` : ""}`);
    },
    get: (id: string) => fetchAPI<StudySummary>(`/studies/${id}`),
  },
  reports: {
    get: (studyId: string) => fetchAPI<LungRADSReport>(`/reports/${studyId}`),
  },
  inference: {
    run: (studyId: string, pipeline: "ct" | "cxr") =>
      fetchAPI("/inference/run", {
        method: "POST",
        body: JSON.stringify({ study_id: studyId, pipeline }),
      }),
    status: (taskId: string) => fetchAPI(`/inference/status/${taskId}`),
  },
};
