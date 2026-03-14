import type {
  StudySummary,
  LungRADSReport,
  InferenceResponse,
  InferenceStatus,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }
  return res.json();
}

export async function getHealth() {
  return request<{ status: string; service: string }>("/health");
}

export async function getStudies(params?: {
  modality?: string;
  status?: string;
  limit?: number;
  offset?: number;
}) {
  const qs = new URLSearchParams();
  if (params?.modality) qs.set("modality", params.modality);
  if (params?.status) qs.set("status", params.status);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const q = qs.toString();
  return request<StudySummary[]>(`/studies/${q ? `?${q}` : ""}`);
}

export async function getStudy(studyId: string) {
  return request<StudySummary>(`/studies/${studyId}`);
}

export async function getStudyCount(params?: {
  modality?: string;
  status?: string;
}) {
  const qs = new URLSearchParams();
  if (params?.modality) qs.set("modality", params.modality);
  if (params?.status) qs.set("status", params.status);
  const q = qs.toString();
  return request<{ count: number }>(`/studies/count${q ? `?${q}` : ""}`);
}

export async function runInference(body: {
  study_id: string;
  pipeline: "cxr" | "ct";
}) {
  return request<InferenceResponse>("/inference/run", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getInferenceStatus(taskId: string) {
  return request<InferenceStatus>(`/inference/status/${taskId}`);
}

export async function getReport(studyId: string) {
  return request<LungRADSReport>(`/reports/${studyId}`);
}

export async function uploadDicom(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/dicom/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Upload failed ${res.status}: ${body || res.statusText}`);
  }
  return res.json() as Promise<{
    study_uid: string;
    series_count: number;
    instance_count: number;
    patient_id: string;
    study_id: string;
  }>;
}

export async function uploadDicomBatch(files: File[]) {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const res = await fetch(`${API_BASE}/dicom/upload-batch`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Batch upload failed ${res.status}: ${body || res.statusText}`);
  }
  return res.json();
}
