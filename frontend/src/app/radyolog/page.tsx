"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import Link from "next/link";
import { useStudies, useInference, useReport } from "@/lib/hooks";
import type { StudySummary } from "@/lib/types";
import {
  Move, Ruler, ZoomIn, Triangle, RotateCw, FlipHorizontal, RefreshCcw,
  Layers, Thermometer, Trash2, ChevronDown, Monitor,
  FileImage, Box, Stethoscope, Activity,
} from "lucide-react";

/* ── W/L presets ── */
const WL_PRESETS = [
  { name: "Akciğer", w: 1500, l: -600 },
  { name: "Mediastin", w: 350, l: 50 },
  { name: "Kemik", w: 1800, l: 400 },
  { name: "Beyin", w: 80, l: 40 },
  { name: "Varsayılan", w: 2048, l: 0 },
];

/* ── helper: Lung-RADS → UI display ── */
const RADS_META: Record<string, { rc: string; color: string; name: string; act: string }> = {
  "1": { rc: "r1b", color: "var(--r1)", name: "Negatif", act: "Yillik tarama yeterli" },
  "2": { rc: "r2b", color: "var(--r2)", name: "Benign Gorünüm", act: "Yillik tarama yeterli" },
  "3": { rc: "r3b", color: "var(--r3)", name: "Muhtemelen Benign", act: "6 ay sonra DDBT kontrolü" },
  "4A": { rc: "r4ab", color: "var(--r4a)", name: "Süpheli — Düsük Risk", act: "3 ay sonra DDBT kontrolü" },
  "4B": { rc: "r4bb", color: "var(--r4b)", name: "Süpheli — Yüksek Risk", act: "Biyopsi / Cerrahi konsültasyon" },
  "4X": { rc: "r4bb", color: "var(--r4b)", name: "Ek Bulgularla Yüksek Süphe", act: "Ileri tetkik gerekli" },
};

const getRads = (r: string | null) =>
  RADS_META[r || ""] || { rc: "r1b", color: "var(--t3)", name: "Belirsiz", act: "Analiz bekliyor" };

/* ── helper: study status → priority ── */
const statusToPri = (s: StudySummary): "h" | "m" | "l" => {
  const rads = s.lung_rads;
  if (rads === "4A" || rads === "4B" || rads === "4X") return "h";
  if (s.status === "queued" || s.status === "processing" || rads === "3") return "m";
  return "l";
};

const priLabel = (p: "h" | "m" | "l") =>
  p === "h" ? "Acil" : p === "m" ? "Bekliyor" : "Normal";

/* ── pipeline step definitions ── */
const CXR_STEPS = [
  { icon: "🔍", name: "Kalite Kontrol CXR", dur: "< 1s" },
  { icon: "🧠", name: "CXR Ark+ Swin-L", dur: "2.1s" },
  { icon: "📊", name: "TorchXRayVision", dur: "1.8s" },
  { icon: "📡", name: "X-Raydar", dur: "2.3s" },
  { icon: "✂️", name: "MedRAX Segmentasyon", dur: "3.1s" },
  { icon: "📋", name: "Ensemble Karar", dur: "0.5s" },
];

const CT_STEPS = [
  { icon: "⚙️", name: "DICOM Ön İşleme", dur: "30-60s" },
  { icon: "🔍", name: "Kalite Kontrol BT", dur: "< 3s" },
  { icon: "🎯", name: "nnU-Net Nodül Segm.", dur: "45-90s" },
  { icon: "🔬", name: "Malignite Sınıflandırma", dur: "2-5s" },
  { icon: "📈", name: "Büyüme Takibi", dur: "5-15s" },
  { icon: "📝", name: "Türkçe Rapor LLM", dur: "10-30s" },
];

export default function RadyologPage() {
  /* ── API data ── */
  const { studies, loading: studiesLoading, error: studiesError, refetch } = useStudies({ limit: 100 });
  const cxrInference = useInference();
  const ctInference = useInference();

  /* ── state ── */
  const [selIdx, setSelIdx] = useState(0);
  const [search, setSearch] = useState("");
  const [rightTab, setRightTab] = useState(0);
  const [activePip, setActivePip] = useState(1);

  // pipeline UI states
  const [cxrDone, setCxrDone] = useState(false);
  const [showAgents, setShowAgents] = useState(false);
  const [showCtPrompt, setShowCtPrompt] = useState(false);
  const [ctDone, setCtDone] = useState(false);
  const [showRads, setShowRads] = useState(false);
  const [showPipeSteps, setShowPipeSteps] = useState(false);
  const [showNodules, setShowNodules] = useState(false);

  // toolbar
  const [activeTool, setActiveTool] = useState<"pan" | "ruler" | "zoom" | "angle" | "rotate" | "flip" | "reset">("pan");
  const [aiLayer, setAiLayer] = useState(false);
  const [heatmap, setHeatmap] = useState(false);
  const [wlPreset, setWlPreset] = useState(0); // Akciğer
  const [wlOpen, setWlOpen] = useState(false);

  // toast
  const [toast, setToast] = useState("");
  const [toastVisible, setToastVisible] = useState(false);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // modal
  const [modal, setModal] = useState<null | "stat" | "pacs">(null);

  // pip states
  const [pip1State, setPip1State] = useState<"" | "on" | "done">("");
  const [pip2State, setPip2State] = useState<"" | "ready" | "on" | "done">("");
  const [pipMsg, setPipMsg] = useState("");

  // W/L current values
  const wl = WL_PRESETS[wlPreset];

  // keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      switch (e.key.toLowerCase()) {
        case "p": setActiveTool("pan"); break;
        case "l": setActiveTool("ruler"); break;
        case "z": setActiveTool("zoom"); break;
        case "a": setActiveTool("angle"); break;
        case "r": setActiveTool("rotate"); break;
        case "h": setHeatmap(v => !v); break;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // report
  const selectedStudy = studies[selIdx] || null;
  const { report, fetchReport } = useReport(selectedStudy?.id || null);

  /* ── filtered studies ── */
  const filtered = studies.filter(
    (s) =>
      s.patient_name.toLowerCase().includes(search.toLowerCase()) ||
      s.id.includes(search) ||
      s.patient_id.includes(search)
  );

  /* ── queue stats ── */
  const acil = studies.filter((s) => statusToPri(s) === "h").length;
  const bekliyor = studies.filter((s) => statusToPri(s) === "m").length;
  const tamam = studies.filter((s) => statusToPri(s) === "l").length;

  /* ── toast helper ── */
  const showToast = useCallback((msg: string) => {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast(msg);
    setToastVisible(true);
    toastTimer.current = setTimeout(() => setToastVisible(false), 2800);
  }, []);

  /* ── select study ── */
  const selectPt = useCallback(
    (i: number) => {
      setSelIdx(i);
      cxrInference.reset();
      ctInference.reset();
      setCxrDone(false);
      setShowAgents(false);
      setShowCtPrompt(false);
      setCtDone(false);
      setShowRads(false);
      setShowPipeSteps(false);
      setShowNodules(false);
      setActivePip(1);
      setPip1State("");
      setPip2State("");
      setPipMsg("");
      setRightTab(0);
    },
    [cxrInference, ctInference]
  );

  /* ── Watch CXR inference status ── */
  useEffect(() => {
    if (cxrInference.status === "SUCCESS" || cxrInference.status === "completed") {
      setCxrDone(true);
      setPip1State("done");
      setPipMsg("CXR analizi tamamlandı");
      showToast("CXR Pipeline tamamlandı");
      setShowAgents(true);

      // Fetch report and check if CT is needed
      if (selectedStudy) {
        fetchReport();
      }
    }
  }, [cxrInference.status]);

  /* ── Watch CT inference status ── */
  useEffect(() => {
    if (ctInference.status === "SUCCESS" || ctInference.status === "completed") {
      setCtDone(true);
      setPip2State("done");
      setPipMsg("Tüm pipeline tamamlandı");
      showToast("BT Pipeline tamamlandı — Lung-RADS hesaplandı");
      setShowRads(true);
      setShowPipeSteps(true);
      setShowNodules(true);
      setRightTab(0);

      // Refresh report
      if (selectedStudy) {
        fetchReport();
        refetch();
      }
    }
  }, [ctInference.status]);

  /* ── Check if CT is recommended after CXR report loads ── */
  useEffect(() => {
    if (report && cxrDone && !ctDone) {
      const radsNum = parseInt(report.overall_lung_rads);
      if (radsNum >= 3 && selectedStudy?.modality !== "CR") {
        setShowCtPrompt(true);
        setPip2State("ready");
        setPipMsg("BT yönlendirmesi önerildi — Pipeline 2 hazır");
      }
    }
  }, [report, cxrDone, ctDone, selectedStudy]);

  /* ── run CXR pipeline ── */
  const runCXR = useCallback(() => {
    if (!selectedStudy || cxrInference.status !== "idle") return;
    setPip1State("on");
    setPipMsg("Pipeline 1 çalışıyor...");
    setActivePip(1);
    cxrInference.start(selectedStudy.id, "cxr");
  }, [selectedStudy, cxrInference]);

  /* ── run CT pipeline ── */
  const runCT = useCallback(() => {
    if (!selectedStudy || ctInference.status !== "idle") return;
    setPip2State("on");
    setPipMsg("Pipeline 2 çalışıyor...");
    setActivePip(2);
    setShowCtPrompt(false);
    ctInference.start(selectedStudy.id, "ct");
  }, [selectedStudy, ctInference]);

  /* ── current study display info ── */
  const st = selectedStudy;
  const radsInfo = getRads(report?.overall_lung_rads || st?.lung_rads || null);
  const radsVal = report?.overall_lung_rads || st?.lung_rads || "-";
  const cxrRunning = cxrInference.status === "queued" || cxrInference.status === "PENDING" || cxrInference.status === "STARTED" || cxrInference.status === "PROGRESS" || cxrInference.status === "starting";
  const ctRunning = ctInference.status === "queued" || ctInference.status === "PENDING" || ctInference.status === "STARTED" || ctInference.status === "PROGRESS" || ctInference.status === "starting";

  /* ── build report text ── */
  const reportText = () => {
    if (!report) {
      return (
        <>
          <div className="rs">BULGULAR</div>
          <div className="rtxt">Pipeline henüz çalıştırılmadı. AI Analiz sekmesinden pipeline başlatın.</div>
        </>
      );
    }
    return (
      <>
        <div className="rs">BULGULAR</div>
        <div className="rtxt">
          {report.summary_tr || "Rapor özeti mevcut değil."}
        </div>
        <div className="rs">LUNG-RADS</div>
        <div className="rtxt">
          Lung-RADS <span className="rhl">{report.overall_lung_rads}</span> — {radsInfo.name}
        </div>
        <div className="rs">ÖNERİ</div>
        <div className="rtxt">{report.recommendation_tr || radsInfo.act}</div>
        {report.total_processing_seconds && (
          <>
            <div className="rs">İŞLEM SÜRESİ</div>
            <div className="rtxt">{report.total_processing_seconds.toFixed(1)} saniye</div>
          </>
        )}
      </>
    );
  };

  /* ── Loading / Error states ── */
  if (studiesLoading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "var(--t2)" }}>
        Çalışmalar yükleniyor...
      </div>
    );
  }

  if (studiesError) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100vh", gap: 12 }}>
        <div style={{ color: "var(--err)", fontSize: 14 }}>API Bağlantı Hatası</div>
        <div style={{ color: "var(--t3)", fontSize: 11 }}>{studiesError}</div>
        <button className="ai-btn" onClick={refetch} style={{ marginTop: 8 }}>Tekrar Dene</button>
      </div>
    );
  }

  if (studies.length === 0) {
    return (
      <>
        <header className="hdr">
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <Link href="/" className="hlogo">
              <div>
                <div className="hlogotext">AlpCAN</div>
                <div className="hlogosub">Cancer Analysis Network</div>
              </div>
            </Link>
            <div className="hbadge">Radyolog</div>
          </div>
        </header>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "calc(100vh - 52px)", gap: 16 }}>
          <div style={{ fontSize: 48, opacity: 0.3 }}>📂</div>
          <div style={{ color: "var(--t2)", fontSize: 14 }}>Henüz çalışma yok</div>
          <div style={{ color: "var(--t3)", fontSize: 11 }}>DICOM dosyası yükleyerek başlayın</div>
          <Link href="/yukle" className="ai-btn" style={{ marginTop: 8, textDecoration: "none" }}>
            DICOM Yükle
          </Link>
        </div>
      </>
    );
  }

  return (
    <>
      {/* ── HEADER ── */}
      <header className="hdr">
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <Link href="/" className="hlogo">
            <div>
              <div className="hlogotext">AlpCAN</div>
              <div className="hlogosub">Cancer Analysis Network</div>
            </div>
          </Link>
          <div className="hbadge">Radyolog</div>
          <nav className="hnav">
            <span className="hnp on">İş Listesi</span>
            <span className="hnp" onClick={() => setModal("stat")}>İstatistik</span>
            <span className="hnp" onClick={() => setModal("pacs")}>PACS</span>
            <Link href="/yukle" className="hnp">Yükle</Link>
            <Link href="/dev" className="hnp">Dev</Link>
          </nav>
        </div>
        <div className="hright">
          <div className="live">
            <span className="ldot" />
            {studies.length} çalışma
          </div>
          <div className="uchip">
            <div className="uav">DR</div>
            Dr. Radyolog
          </div>
        </div>
      </header>

      {/* ── 3-COLUMN LAYOUT ── */}
      <div className="rlayout">
        {/* ──────── LEFT PANEL ──────── */}
        <div className="lpanel">
          <div className="lph">
            <div className="lplbl">Çalışma Kuyruğu ({filtered.length})</div>
            <input
              className="lpsrc"
              placeholder="Hasta ara..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="qrow">
            <div className="qcell">
              <div className="qv" style={{ color: "var(--err)" }}>{acil}</div>
              <div className="ql">Acil</div>
            </div>
            <div className="qcell">
              <div className="qv" style={{ color: "var(--warn)" }}>{bekliyor}</div>
              <div className="ql">Bekliyor</div>
            </div>
            <div className="qcell">
              <div className="qv" style={{ color: "var(--ok)" }}>{tamam}</div>
              <div className="ql">Tamam</div>
            </div>
          </div>
          <div className="plist">
            {filtered.length === 0 && (
              <div style={{ padding: 20, textAlign: "center", color: "var(--t3)", fontSize: 11 }}>
                <FileImage size={28} strokeWidth={1} style={{ margin: "0 auto 8px", opacity: 0.3 }} />
                <div>Sonuç bulunamadı</div>
              </div>
            )}
            {filtered.map((s) => {
              const realIdx = studies.indexOf(s);
              const pri = statusToPri(s);
              const sRads = getRads(s.lung_rads);
              return (
                <div
                  key={s.id}
                  className={`pc${realIdx === selIdx ? " sel" : ""}`}
                  onClick={() => selectPt(realIdx)}
                >
                  <div className="pct">
                    <div className="pcn">
                      <span className={`prio p${pri}`} />
                      <span className="pc-mod">
                        {s.modality === "CT" ? <Box size={10} /> : <FileImage size={10} />}
                      </span>
                      {s.patient_name}
                    </div>
                  </div>
                  <div className="pcb">
                    <span className="pc-date">{new Date(s.study_date).toLocaleDateString("tr-TR")}</span>
                    {s.lung_rads && (
                      <span className={`rb ${sRads.rc}`}>RADS-{s.lung_rads}</span>
                    )}
                    {!s.lung_rads && (
                      <span className="pct2" style={{ color: "var(--t3)" }}>{s.status}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ──────── CENTER PANEL ──────── */}
        <div className="center">
          {/* pipeline bar */}
          <div className="pipbar">
            <div
              className={`pip${activePip === 1 ? (pip1State === "done" ? " done" : " on") : pip1State === "done" ? " done" : ""}`}
              onClick={() => setActivePip(1)}
            >
              <span className="pipn">1</span>
              CXR Pipeline
            </div>
            <span className="piparr">&rarr;</span>
            <div
              className={`pip${activePip === 2 ? (pip2State === "done" ? " done" : " on") : pip2State === "done" ? " done" : pip2State === "ready" ? " ready" : ""}`}
              onClick={() => setActivePip(2)}
            >
              <span className="pipn">2</span>
              BT Pipeline
            </div>
            <span className="pipmsg">{pipMsg}</span>
          </div>

          {/* toolbar */}
          <div className="vtbar">
            <button className={`tb-i${activeTool === "pan" ? " active" : ""}`} onClick={() => setActiveTool("pan")} title="Pan (P)">
              <Move /><span className="tb-kbd">P</span>
            </button>
            <button className={`tb-i${activeTool === "ruler" ? " active" : ""}`} onClick={() => setActiveTool("ruler")} title="Ölçüm (L)">
              <Ruler /><span className="tb-kbd">L</span>
            </button>
            <button className={`tb-i${activeTool === "zoom" ? " active" : ""}`} onClick={() => setActiveTool("zoom")} title="Zoom (Z)">
              <ZoomIn /><span className="tb-kbd">Z</span>
            </button>
            <button className={`tb-i${activeTool === "angle" ? " active" : ""}`} onClick={() => setActiveTool("angle")} title="Açı (A)">
              <Triangle /><span className="tb-kbd">A</span>
            </button>
            <span className="tsep" />
            <button className={`tb-i${activeTool === "rotate" ? " active" : ""}`} onClick={() => setActiveTool("rotate")} title="Döndür (R)">
              <RotateCw /><span className="tb-kbd">R</span>
            </button>
            <button className="tb-i" onClick={() => showToast("Yatay çevirme uygulandı")} title="Çevir">
              <FlipHorizontal />
            </button>
            <button className="tb-i" onClick={() => { setActiveTool("pan"); showToast("Görüntü sıfırlandı"); }} title="Sıfırla">
              <RefreshCcw />
            </button>
            <span className="tsep" />
            <button className={`tb-i${aiLayer ? " on" : ""}`} onClick={() => setAiLayer(!aiLayer)} title="AI Katman">
              <Layers />
            </button>
            <button className={`tb-i${heatmap ? " on" : ""}`} onClick={() => setHeatmap(!heatmap)} title="Isı Haritası (H)">
              <Thermometer /><span className="tb-kbd">H</span>
            </button>
            <span className="tsep" />
            <button className="tb-i" onClick={() => { setAiLayer(false); setHeatmap(false); setActiveTool("pan"); }} title="Temizle">
              <Trash2 />
            </button>

            {/* W/L preset dropdown */}
            <div className="wl-wrap">
              <button className="wl-btn" onClick={() => setWlOpen(!wlOpen)}>
                <Monitor size={12} />
                {wl.name} W:{wl.w} L:{wl.l}
                <ChevronDown />
              </button>
              <div className={`wl-dd${wlOpen ? " open" : ""}`}>
                {WL_PRESETS.map((p, i) => (
                  <div
                    key={p.name}
                    className={`wl-opt${wlPreset === i ? " sel" : ""}`}
                    onClick={() => { setWlPreset(i); setWlOpen(false); }}
                  >
                    <span className="wl-opt-n">{p.name}</span>
                    <span className="wl-opt-v">W:{p.w} L:{p.l}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* CXR viewer */}
          {activePip === 1 && (
            <div className="cxr-wrap">
              {/* Corner overlays — OHIF style */}
              <div className="vp-overlay vp-tl">
                <div className="vp-mod">{st?.modality === "CT" ? "CT" : st?.modality === "DX" ? "DX" : "CR"}</div>
                <div>PA AKCİĞER GRAFİSİ</div>
                {st && <div style={{ fontSize: 8, color: "rgba(255,255,255,.3)" }}>{st.description || "Standart projeksiyon"}</div>}
              </div>
              <div className="vp-overlay vp-tr">
                <div style={{ fontWeight: 600, color: "rgba(255,255,255,.55)" }}>{st?.patient_name || "—"}</div>
                <div>ID: {st?.patient_id?.slice(0, 8) || "—"}</div>
                <div>{st ? new Date(st.study_date).toLocaleDateString("tr-TR") : "—"}</div>
              </div>
              <div className="vp-overlay vp-bl">
                <div>W:{wl.w} L:{wl.l}</div>
                <div>{wl.name}</div>
              </div>
              <div className="vp-overlay vp-br">
                <div>1.0x</div>
                <div>2048×2048</div>
              </div>

              {/* Heatmap overlay */}
              <div className={`heatmap-sim${heatmap ? " on" : ""}`} />

              {/* Scan line animation */}
              {(cxrRunning) && <div className="scan" />}

              {/* Center placeholder with medical icon */}
              <div className="vp-center">
                <Stethoscope size={80} strokeWidth={0.5} />
                <div className="vp-center-txt">
                  {cxrRunning ? "Analiz ediliyor..." : cxrDone ? "Analiz tamamlandı" : "Pipeline başlatın"}
                </div>
              </div>
            </div>
          )}

          {/* CT grid */}
          {activePip === 2 && (
            <div className="ct-grid" style={{ flex: 1 }}>
              {([
                { label: "Axial", cls: "vpane-ax", slice: "S:128/256" },
                { label: "Coronal", cls: "vpane-co", slice: "S:256/512" },
                { label: "Sagittal", cls: "vpane-sa", slice: "S:256/512" },
                { label: "3D MIP", cls: "vpane-3d", slice: "" },
              ]).map(({ label, cls, slice }) => (
                <div className={`vpane ${cls}`} key={label}>
                  {/* Corner overlays per pane */}
                  <div className="vp-overlay vp-tl">
                    <div className="vp-mod">{label}</div>
                  </div>
                  <div className="vp-overlay vp-tr" style={{ fontSize: 8 }}>
                    <div>{st?.patient_name || "—"}</div>
                  </div>
                  <div className="vp-overlay vp-bl" style={{ fontSize: 8 }}>
                    <div>W:{wl.w} L:{wl.l}</div>
                  </div>
                  <div className="vp-overlay vp-br" style={{ fontSize: 8 }}>
                    {slice && <div>{slice}</div>}
                  </div>

                  {/* Crosshair lines */}
                  <div className="crosshair-h" />
                  <div className="crosshair-v" />

                  {/* Heatmap */}
                  <div className={`heatmap-sim${heatmap ? " on" : ""}`} />

                  {/* Scan animation on running */}
                  {ctRunning && <div className="scan" />}

                  {/* Center icon */}
                  <div className="vp-center">
                    <Activity size={36} strokeWidth={0.5} />
                    <div className="vp-center-txt" style={{ fontSize: 8 }}>
                      {ctRunning ? "İşleniyor..." : ctDone ? "Tamamlandı" : label}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ──────── RIGHT PANEL ──────── */}
        <div className="rpanel">
          {/* tabs */}
          <div className="rtabs">
            {["AI Analiz", "Rapor", "Geçmiş"].map((t, i) => (
              <div
                key={t}
                className={`rtab${rightTab === i ? " on" : ""}`}
                onClick={() => setRightTab(i)}
              >
                {t}
              </div>
            ))}
          </div>

          {/* tab contents */}
          <div className="rcont">
            {/* ── TAB 0: AI Analiz ── */}
            <div className={`tc${rightTab === 0 ? " on" : ""}`}>
              {/* study info card */}
              {st && (
                <div className="card">
                  <div className="ch">
                    <div>
                      <div className="cn">{st.patient_name}</div>
                      <div className="ci">#{st.id.slice(0, 8)} · {st.modality} · {st.status}</div>
                    </div>
                    {st.lung_rads && (
                      <span className={`rb ${radsInfo.rc}`}>RADS-{radsVal}</span>
                    )}
                  </div>
                  <div className="cgrid">
                    <div>
                      <div className="cl">Modalite</div>
                      <div className="cv">{st.modality}</div>
                    </div>
                    <div>
                      <div className="cl">Tarih</div>
                      <div className="cv">{new Date(st.study_date).toLocaleDateString("tr-TR")}</div>
                    </div>
                    <div>
                      <div className="cl">Durum</div>
                      <div className="cv">{st.status}</div>
                    </div>
                    <div>
                      <div className="cl">Nodül Sayısı</div>
                      <div className="cv">{st.nodule_count ?? "-"}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* CXR start button */}
              {!cxrDone && !cxrRunning && (
                <button className="ai-btn" onClick={runCXR}>
                  Pipeline 1 — CXR Analizi Başlat
                </button>
              )}

              {/* CXR progress bar */}
              {cxrRunning && (
                <div className="pbar-w">
                  <div className="pbar-l">CXR Pipeline İlerlemesi</div>
                  <div className="pbar-tr">
                    <div
                      className="pbar-fl animating"
                      style={{ width: `${cxrInference.progress ? Math.round((cxrInference.progress.step / cxrInference.progress.total_steps) * 100) : 50}%` }}
                    />
                  </div>
                  <div className="pbar-st">
                    {cxrInference.progress?.current_agent || cxrInference.status || "İşleniyor..."}
                    {cxrInference.progress && (
                      <span style={{ float: "right", color: "var(--t3)" }}>
                        %{Math.round((cxrInference.progress.step / cxrInference.progress.total_steps) * 100)}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* CXR Error */}
              {cxrInference.error && (
                <div className="card" style={{ borderColor: "var(--err)" }}>
                  <div style={{ color: "var(--err)", fontSize: 11 }}>{cxrInference.error}</div>
                </div>
              )}

              {/* CXR Ensemble agents — show from report */}
              {showAgents && report && (
                <div className="agents">
                  <div className="plbl">CXR Ensemble Sonuçları</div>
                  {report.cxr_ensemble_score != null && (
                    <div className="arow">
                      <div className="an">Ensemble Skor</div>
                      <div className="abar">
                        <div
                          className="afill"
                          style={{
                            width: `${(report.cxr_ensemble_score * 100).toFixed(0)}%`,
                            background: report.cxr_ensemble_score > 0.5 ? "var(--err)" : "var(--ok)",
                          }}
                        />
                      </div>
                      <div className="av" style={{ color: report.cxr_ensemble_score > 0.5 ? "var(--err)" : "var(--ok)" }}>
                        {(report.cxr_ensemble_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  )}
                  {report.cxr_recommendation && (
                    <div className="adec">{report.cxr_recommendation}</div>
                  )}
                </div>
              )}

              {/* CXR done but no report yet */}
              {showAgents && !report && (
                <div className="agents">
                  <div className="plbl">CXR Analiz Tamamlandı</div>
                  <div className="adec">Rapor yükleniyor...</div>
                </div>
              )}

              {/* CT prompt */}
              {showCtPrompt && (
                <div className="ct-prompt" onClick={runCT}>
                  <div className="ctp-t">BT Analizi Öneriliyor</div>
                  <div className="ctp-s">
                    RADS-{radsVal} &ge; 3 — Düşük doz BT ile ileri değerlendirme önerilmektedir.
                    <br />
                    Pipeline 2&apos;yi başlatmak için tıklayın.
                  </div>
                </div>
              )}

              {/* CT start button */}
              {activePip === 2 && !ctRunning && !ctDone && cxrDone && !showCtPrompt && (
                <button className="ai-btn ct" onClick={runCT}>
                  Pipeline 2 — BT Analizi Başlat
                </button>
              )}

              {/* CT progress bar */}
              {ctRunning && (
                <div className="pbar-w">
                  <div className="pbar-l">BT Pipeline İlerlemesi</div>
                  <div className="pbar-tr">
                    <div
                      className="pbar-fl animating"
                      style={{ width: `${ctInference.progress ? Math.round((ctInference.progress.step / ctInference.progress.total_steps) * 100) : 50}%` }}
                    />
                  </div>
                  <div className="pbar-st">
                    {ctInference.progress?.current_agent || ctInference.status || "İşleniyor..."}
                    {ctInference.progress && (
                      <span style={{ float: "right", color: "var(--t3)" }}>
                        %{Math.round((ctInference.progress.step / ctInference.progress.total_steps) * 100)}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* CT Error */}
              {ctInference.error && (
                <div className="card" style={{ borderColor: "var(--err)" }}>
                  <div style={{ color: "var(--err)", fontSize: 11 }}>{ctInference.error}</div>
                </div>
              )}

              {/* Lung-RADS box */}
              {showRads && report && (
                <div className="rads-box">
                  <div className="rads-l">Lung-RADS Skoru</div>
                  <div className="rads-n" style={{ color: radsInfo.color }}>
                    {report.overall_lung_rads}
                  </div>
                  <div className="rads-nm" style={{ color: radsInfo.color }}>
                    {radsInfo.name}
                  </div>
                  <div
                    className="rads-ac"
                    style={{
                      background: `${radsInfo.color}11`,
                      color: radsInfo.color,
                      border: `1px solid ${radsInfo.color}33`,
                    }}
                  >
                    {radsInfo.act}
                  </div>
                </div>
              )}

              {/* Pipeline steps card */}
              {showPipeSteps && (
                <div className="pipe-card">
                  <div className="plbl">Pipeline Adımları</div>
                  {CXR_STEPS.map((s, i) => (
                    <div className="ps" key={`cxr-${i}`}>
                      <div className="psi pok">{s.icon}</div>
                      <div className="psn">{s.name}</div>
                      <div className="psd">{s.dur}</div>
                      <div className="pst">&check;</div>
                    </div>
                  ))}
                  {CT_STEPS.map((s, i) => (
                    <div className="ps" key={`ct-${i}`}>
                      <div className="psi pok">{s.icon}</div>
                      <div className="psn">{s.name}</div>
                      <div className="psd">{s.dur}</div>
                      <div className="pst">&check;</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Nodule findings */}
              {showNodules && report && report.nodules.length > 0 && (
                <div className="nod-card">
                  <div className="plbl">Nodül Bulguları</div>
                  {report.nodules.map((n, i) => {
                    const malPct = n.malignancy_score != null ? Math.round(n.malignancy_score * 100) : 0;
                    const nColor = malPct > 60 ? "var(--err)" : malPct > 30 ? "var(--r3)" : "var(--ok)";
                    return (
                      <div className="ni" key={n.id}>
                        <div className="nth">
                          <div className="nc" style={{ background: `${nColor}22`, color: nColor }}>
                            {i + 1}
                          </div>
                        </div>
                        <div className="nd">
                          <div className="nsz">{n.size_mm.toFixed(1)} mm</div>
                          <div className="nloc">{n.location || "Konum belirtilmemiş"}</div>
                          <div style={{ marginTop: 3 }}>
                            {n.density && (
                              <span className={`ntag ${n.density === "solid" ? "ntag-solid" : n.density === "part-solid" ? "ntag-ps" : "ntag-ggo"}`}>
                                {n.density === "solid" ? "Solid" : n.density === "part-solid" ? "Part-Solid" : "GGO"}
                              </span>
                            )}
                            {n.lung_rads && (
                              <span className="ntag ntag-rads">RADS-{n.lung_rads}</span>
                            )}
                          </div>
                          <div className="mbar">
                            <div
                              className="mfill"
                              style={{ width: `${malPct}%`, background: nColor }}
                            />
                          </div>
                        </div>
                        <div className="nsco">
                          <div className="nsv" style={{ color: nColor }}>
                            %{malPct}
                          </div>
                          <div className="nsl">malignite</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* ── TAB 1: Rapor ── */}
            <div className={`tc${rightTab === 1 ? " on" : ""}`}>
              <div className="rbox">
                <div className="rh">
                  <div className="rt">Radyoloji Raporu</div>
                  <div style={{ fontSize: 9, color: "var(--t3)" }}>
                    #{st?.id.slice(0, 8)} · {st?.patient_name}
                  </div>
                </div>
                {reportText()}

                {/* Report timestamp */}
                {report && (
                  <div className="r-stamp">
                    Rapor oluşturma: {new Date().toLocaleDateString("tr-TR")} {new Date().toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" })}
                    {report.total_processing_seconds && ` · ${report.total_processing_seconds.toFixed(1)}s`}
                  </div>
                )}

                {/* Doctor signature */}
                <div className="r-sign">
                  <div className="r-sign-av">DR</div>
                  <div className="r-sign-info">
                    <div className="r-sign-name">Dr. Radyolog</div>
                    <div className="r-sign-role">Göğüs Radyolojisi Uzmanı</div>
                  </div>
                </div>

                <div style={{ display: "flex", gap: 5, marginTop: 10 }}>
                  <button className="pbtn" onClick={() => showToast("PDF oluşturuldu")}>
                    PDF
                  </button>
                  <button className="pbtn" onClick={() => showToast("PACS'a gönderildi")}>
                    PACS
                  </button>
                  <button className="pbtn" onClick={() => showToast("FHIR R4 gönderildi")}>
                    FHIR
                  </button>
                  <button className="pbtn" onClick={() => showToast("Kurul listesine eklendi")}>
                    Kurul
                  </button>
                </div>
              </div>
            </div>

            {/* ── TAB 2: Geçmiş ── */}
            <div className={`tc${rightTab === 2 ? " on" : ""}`}>
              <div className="plbl">Çalışma Bilgileri</div>
              {st && (
                <div className="card">
                  <div className="cgrid">
                    <div>
                      <div className="cl">Çalışma ID</div>
                      <div className="cv" style={{ fontSize: 9 }}>{st.id}</div>
                    </div>
                    <div>
                      <div className="cl">Hasta ID</div>
                      <div className="cv" style={{ fontSize: 9 }}>{st.patient_id}</div>
                    </div>
                    <div>
                      <div className="cl">Modalite</div>
                      <div className="cv">{st.modality}</div>
                    </div>
                    <div>
                      <div className="cl">Durum</div>
                      <div className="cv">{st.status}</div>
                    </div>
                    <div>
                      <div className="cl">Tarih</div>
                      <div className="cv">{new Date(st.study_date).toLocaleDateString("tr-TR")}</div>
                    </div>
                    {st.description && (
                      <div>
                        <div className="cl">Açıklama</div>
                        <div className="cv">{st.description}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* bottom actions */}
          <div className="actions">
            <button
              className="btn-p"
              onClick={() => showToast("Rapor onaylandı — PACS'a gönderildi")}
            >
              Onayla ve PACS Gönder
            </button>
            <button
              className="btn-s"
              onClick={() => {
                setRightTab(1);
                showToast("Rapor düzenleme modu açıldı");
              }}
            >
              Raporu Düzenle
            </button>
            <button
              className="btn-d"
              onClick={() => showToast("Acil konsültasyon talebi gönderildi")}
            >
              Acil Konsültasyon
            </button>
          </div>
        </div>
      </div>

      {/* ── TOAST ── */}
      <div className={`toast${toastVisible ? " show" : ""}`}>{toast}</div>

      {/* ── MODAL: İstatistik ── */}
      <div
        className={`moverlay${modal === "stat" ? " open" : ""}`}
        onClick={() => setModal(null)}
      >
        <div className="mbox" onClick={(e) => e.stopPropagation()}>
          <button className="mcls" onClick={() => setModal(null)}>
            &times;
          </button>
          <div className="mt">İstatistik Paneli</div>
          <div className="ms">
            Günlük analiz istatistikleri ve performans metrikleri
          </div>
          <div className="mb">
            Toplam çalışma: <strong>{studies.length}</strong>
            <br />
            Tamamlanan: <strong>{studies.filter((s) => s.status === "completed").length}</strong>
            <br />
            Bekleyen: <strong>{studies.filter((s) => s.status === "uploaded").length}</strong>
            <br />
            RADS &ge; 3: <strong>{studies.filter((s) => parseInt(s.lung_rads || "0") >= 3).length}</strong>
          </div>
          <button className="mbtn-p" onClick={() => setModal(null)}>
            Tamam
          </button>
        </div>
      </div>

      {/* ── MODAL: PACS ── */}
      <div
        className={`moverlay${modal === "pacs" ? " open" : ""}`}
        onClick={() => setModal(null)}
      >
        <div className="mbox" onClick={(e) => e.stopPropagation()}>
          <button className="mcls" onClick={() => setModal(null)}>
            &times;
          </button>
          <div className="mt">PACS Bağlantısı</div>
          <div className="ms">
            Orthanc PACS sunucu durumu ve DICOM bağlantı bilgileri
          </div>
          <div className="mb">
            Sunucu: <strong>Orthanc 1.12.3</strong>
            <br />
            Durum: <strong style={{ color: "var(--ok)" }}>Bağlı</strong>
            <br />
            AE Title: <strong>ALPCAN_PACS</strong>
            <br />
            Port: <strong>4242 (DICOM) / 8042 (REST)</strong>
          </div>
          <button className="mbtn-p" onClick={() => setModal(null)}>
            Tamam
          </button>
        </div>
      </div>
    </>
  );
}
