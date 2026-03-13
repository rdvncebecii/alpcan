export type Screen = "splash" | "radyolog" | "gelistirici";

// ── Patient Data (matches demo + backend) ──
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

// ── Agent Data (matches demo) ──
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
