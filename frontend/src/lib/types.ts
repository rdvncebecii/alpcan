export type Screen = "splash" | "radyolog" | "gelistirici";

// ── Backend API Response Types ──

export interface StudySummary {
  id: string;
  patient_id: string;
  patient_name: string;
  modality: string;
  study_date: string;
  description: string | null;
  status: string;
  nodule_count: number | null;
  lung_rads: string | null;
}

export interface NoduleFinding {
  id: string;
  location: string | null;
  size_mm: number;
  volume_mm3: number | null;
  density: string | null;
  lung_rads: string | null;
  malignancy_score: number | null;
  recommendation: string | null;
}

export interface LungRADSReport {
  study_id: string;
  patient_id: string;
  report_date: string;
  overall_lung_rads: string;
  nodules: NoduleFinding[];
  cxr_ensemble_score: number | null;
  cxr_recommendation: string | null;
  summary_tr: string | null;
  recommendation_tr: string | null;
  full_report_tr: string | null;
  total_processing_seconds: number | null;
  edited: boolean;
}

export interface ReportUpdate {
  summary_tr?: string;
  recommendation_tr?: string;
  full_report_tr?: string;
}

export interface AgentResult {
  agent_name: string;
  status: string;
  confidence: number | null;
  findings: Record<string, unknown> | null;
  duration_seconds: number | null;
}

export interface InferenceResponse {
  task_id: string;
  study_id: string;
  pipeline: "cxr" | "ct";
  status: string;
  agents: AgentResult[];
}

export interface InferenceStatus {
  task_id: string;
  status: string;
  progress?: {
    current_agent: string;
    step: number;
    total_steps: number;
    percent?: number;
  };
  result?: unknown;
}

// ── Auth Types ──

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// ── UI-only Types (used by dev page) ──

export interface PatientAgent {
  n: string;
  v: string;
  p: number;
  c: string;
}

export interface NoduleInfo {
  sz: string;
  loc: string;
  mal: number;
  c: string;
}

export interface HistoryItem {
  d: string;
  t: string;
  r: string;
  rc: string;
}

export interface PatientData {
  id: string;
  name: string;
  age: number;
  g: string;
  pri: "h" | "m" | "l";
  cxr: { tk: string; ci: string; rs: string };
  ct: { tk: string; ci: string; rs: string } | null;
  rads: string;
  rc: string;
  rcolor: string;
  rname: string;
  ract: string;
  cdec: string;
  agents: PatientAgent[];
  nods: NoduleInfo[];
  hx: HistoryItem[];
  trend: string;
}

// ── Agent Data (used by dev page) ──
export interface AgentData {
  code: string;
  name: string;
  icon: string;
  pip: 1 | 2;
  st: "ok" | "tr" | "id" | "wa";
  model: string;
  fw: string;
  dev: string;
  data: string;
  acc: string;
  spd: string;
  p: Record<string, string | number>;
  desc: string;
}

export interface DatasetInfo {
  n: string;
  d: string;
  tags: string[];
}
