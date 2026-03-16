import type {
  StudySummary,
  LungRADSReport,
  InferenceResponse,
  InferenceStatus,
  User,
  LoginResponse,
  ReportUpdate,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("alpcan_token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { ...headers, ...options?.headers },
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

export async function updateStudyStatus(studyId: string, status: string) {
  return request<StudySummary>(`/studies/${studyId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export async function seedDemo() {
  return request<{ created: number; message: string }>("/studies/seed-demo", {
    method: "POST",
  });
}

export async function clearDemo() {
  return request<{ deleted: number; message: string }>("/studies/seed-demo", {
    method: "DELETE",
  });
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

export async function updateReport(studyId: string, body: ReportUpdate) {
  return request<LungRADSReport>(`/reports/${studyId}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export async function downloadReportPdf(studyId: string): Promise<Blob> {
  const token = typeof window !== "undefined" ? localStorage.getItem("alpcan_token") : null;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}/reports/${studyId}/pdf`, { headers });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`PDF ${res.status}: ${body || res.statusText}`);
  }
  return res.blob();
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

export async function login(email: string, password: string): Promise<LoginResponse> {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Giriş başarısız ${res.status}: ${body || res.statusText}`);
  }
  return res.json();
}

export async function getMe(): Promise<User> {
  return request<User>("/auth/me");
}

export async function register(body: {
  email: string;
  full_name: string;
  password: string;
  role?: string;
}): Promise<User> {
  return request<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
