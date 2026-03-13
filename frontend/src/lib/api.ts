const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export async function getHealth() {
  return request<{ status: string; service: string }>("/health");
}

export interface StudySummary {
  id: string;
  patient_id: string;
  patient_name: string;
  modality: string;
  study_date: string;
  description: string;
  status: string;
  nodule_count: number;
  lung_rads: string | null;
}

export async function getStudies(params?: { modality?: string; status?: string; limit?: number }) {
  const qs = new URLSearchParams();
  if (params?.modality) qs.set("modality", params.modality);
  if (params?.status) qs.set("status", params.status);
  if (params?.limit) qs.set("limit", String(params.limit));
  const q = qs.toString();
  return request<StudySummary[]>(`/studies/${q ? `?${q}` : ""}`);
}

export async function runInference(body: { study_id: string; pipeline: "CXR" | "CT" }) {
  return request<{ task_id: string; status: string }>("/inference/run", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getInferenceStatus(taskId: string) {
  return request<{ status: string; progress: number; current_agent: string }>(
    `/inference/status/${taskId}`
  );
}

export async function getReport(studyId: string) {
  return request<{ overall_lung_rads: string; summary_tr: string; recommendation_tr: string }>(
    `/reports/${studyId}`
  );
}

export async function uploadDicom(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/dicom/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}
