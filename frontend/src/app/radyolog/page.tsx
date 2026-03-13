"use client";

import { useState, useRef, useCallback } from "react";
import Link from "next/link";
import { PATIENTS } from "@/lib/data";
import type { PatientData } from "@/lib/types";

/* ── helper: priority label ── */
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
  /* ── state ── */
  const [selIdx, setSelIdx] = useState(0);
  const [search, setSearch] = useState("");
  const [rightTab, setRightTab] = useState(0); // 0=AI Analiz, 1=Rapor, 2=Geçmiş
  const [activePip, setActivePip] = useState(1); // 1=CXR, 2=BT

  // pipeline progress
  const [cxrRunning, setCxrRunning] = useState(false);
  const [cxrProgress, setCxrProgress] = useState(0);
  const [cxrStep, setCxrStep] = useState("");
  const [cxrDone, setCxrDone] = useState(false);
  const [showAgents, setShowAgents] = useState(false);
  const [showCtPrompt, setShowCtPrompt] = useState(false);

  const [ctRunning, setCtRunning] = useState(false);
  const [ctProgress, setCtProgress] = useState(0);
  const [ctStep, setCtStep] = useState("");
  const [ctDone, setCtDone] = useState(false);
  const [showRads, setShowRads] = useState(false);
  const [showPipeSteps, setShowPipeSteps] = useState(false);
  const [showNodules, setShowNodules] = useState(false);

  // toolbar
  const [aiLayer, setAiLayer] = useState(false);
  const [heatmap, setHeatmap] = useState(false);

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

  const pt: PatientData = PATIENTS[selIdx];

  /* ── filtered patients ── */
  const filtered = PATIENTS.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.id.includes(search)
  );

  /* ── queue stats ── */
  const acil = PATIENTS.filter((p) => p.pri === "h").length;
  const bekliyor = PATIENTS.filter((p) => p.pri === "m").length;
  const tamam = PATIENTS.filter((p) => p.pri === "l").length;

  /* ── toast helper ── */
  const showToast = useCallback((msg: string) => {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast(msg);
    setToastVisible(true);
    toastTimer.current = setTimeout(() => setToastVisible(false), 2800);
  }, []);

  /* ── select patient ── */
  const selectPt = useCallback(
    (i: number) => {
      setSelIdx(i);
      // reset pipeline state
      setCxrRunning(false);
      setCxrProgress(0);
      setCxrStep("");
      setCxrDone(false);
      setShowAgents(false);
      setShowCtPrompt(false);
      setCtRunning(false);
      setCtProgress(0);
      setCtStep("");
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
    []
  );

  /* ── run CXR pipeline ── */
  const runCXR = useCallback(() => {
    if (cxrRunning || cxrDone) return;
    setCxrRunning(true);
    setCxrProgress(0);
    setPip1State("on");
    setPipMsg("Pipeline 1 çalışıyor...");
    setActivePip(1);

    const steps = CXR_STEPS;
    let step = 0;
    const iv = setInterval(() => {
      step++;
      const pct = Math.round((step / steps.length) * 100);
      setCxrProgress(pct);
      setCxrStep(steps[Math.min(step - 1, steps.length - 1)].name);
      if (step >= steps.length) {
        clearInterval(iv);
        setCxrRunning(false);
        setCxrDone(true);
        setPip1State("done");
        setPipMsg("CXR analizi tamamlandı");
        showToast("CXR Pipeline tamamlandı");
        setTimeout(() => showCXRResults(), 400);
      }
    }, 600);
  }, [cxrRunning, cxrDone, showToast]);

  /* ── show CXR results ── */
  const showCXRResults = useCallback(() => {
    setShowAgents(true);
    const radsNum = parseInt(pt.rads);
    if (radsNum >= 3 && pt.ct) {
      setShowCtPrompt(true);
      setPip2State("ready");
      setPipMsg("BT yönlendirmesi önerildi — Pipeline 2 hazır");
    }
  }, [pt]);

  /* ── run CT pipeline ── */
  const runCT = useCallback(() => {
    if (ctRunning || ctDone || !pt.ct) return;
    setCtRunning(true);
    setCtProgress(0);
    setPip2State("on");
    setPipMsg("Pipeline 2 çalışıyor...");
    setActivePip(2);
    setShowCtPrompt(false);

    const steps = CT_STEPS;
    let step = 0;
    const iv = setInterval(() => {
      step++;
      const pct = Math.round((step / steps.length) * 100);
      setCtProgress(pct);
      setCtStep(steps[Math.min(step - 1, steps.length - 1)].name);
      if (step >= steps.length) {
        clearInterval(iv);
        setCtRunning(false);
        setCtDone(true);
        setPip2State("done");
        setPipMsg("Tüm pipeline tamamlandı");
        showToast("BT Pipeline tamamlandı — Lung-RADS hesaplandı");
        setTimeout(() => showFinal(), 400);
      }
    }, 700);
  }, [ctRunning, ctDone, pt, showToast]);

  /* ── show final results ── */
  const showFinal = useCallback(() => {
    setShowRads(true);
    setShowPipeSteps(true);
    setShowNodules(true);
    setRightTab(0);
  }, []);

  /* ── auto-start CT when prompt is shown and clicked ── */
  const handleCtPromptClick = useCallback(() => {
    runCT();
  }, [runCT]);

  /* ── build report text ── */
  const reportText = () => {
    if (!showRads) {
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
          PA akciğer grafisinde <span className="rhl">{pt.agents[0].v.toLowerCase()}</span> saptanmıştır.{" "}
          {pt.ct && (
            <>
              DDBT incelemesinde{" "}
              {pt.nods.map((n, i) => (
                <span key={i}>
                  <span className="rhl">{n.loc}</span> bölgesinde{" "}
                  <span className="rhl">{n.sz}</span> boyutunda nodül
                  {i < pt.nods.length - 1 ? ", " : " "}
                </span>
              ))}
              tespit edilmiştir.
            </>
          )}
        </div>
        <div className="rs">LUNG-RADS</div>
        <div className="rtxt">
          Lung-RADS <span className="rhl">{pt.rads}</span> — {pt.rname}
        </div>
        <div className="rs">ÖNERİ</div>
        <div className="rtxt">{pt.ract}</div>
      </>
    );
  };

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
            <Link href="/dev" className="hnp">⚡ Dev</Link>
          </nav>
        </div>
        <div className="hright">
          <div className="live">
            <span className="ldot" />
            47 analiz
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
            <div className="lplbl">Hasta Kuyruğu</div>
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
            {filtered.map((p, i) => {
              const realIdx = PATIENTS.indexOf(p);
              return (
                <div
                  key={p.id}
                  className={`pc${realIdx === selIdx ? " sel" : ""}`}
                  onClick={() => selectPt(realIdx)}
                >
                  <div className="pct">
                    <div className="pcn">
                      <span className={`prio p${p.pri}`} />
                      {p.name} ({p.age})
                    </div>
                  </div>
                  <div className="pcb">
                    <span className="pct2">{priLabel(p.pri)}</span>
                    <span className={`rb ${p.rc}`}>RADS-{p.rads}</span>
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
            <span className="piparr">→</span>
            <div
              className={`pip${activePip === 2 ? (pip2State === "done" ? " done" : " on") : pip2State === "done" ? " done" : pip2State === "ready" ? " ready" : ""}`}
              onClick={() => pt.ct && setActivePip(2)}
            >
              <span className="pipn">2</span>
              BT Pipeline
            </div>
            <span className="pipmsg">{pipMsg}</span>
          </div>

          {/* toolbar */}
          <div className="vtbar">
            <button className="tb">Pan</button>
            <button className="tb">Ölçüm</button>
            <button className="tb">Zoom</button>
            <button className="tb">Açı</button>
            <span className="tsep" />
            <button
              className={`tb${aiLayer ? " on" : ""}`}
              onClick={() => setAiLayer(!aiLayer)}
            >
              AI Katman
            </button>
            <button
              className={`tb${heatmap ? " on" : ""}`}
              onClick={() => setHeatmap(!heatmap)}
            >
              Isı Haritası
            </button>
            <span className="tsep" />
            <button className="tb" onClick={() => { setAiLayer(false); setHeatmap(false); }}>
              Temizle
            </button>
            <span className="wli">W:2048 L:0</span>
          </div>

          {/* CXR viewer */}
          {activePip === 1 && (
            <div className="cxr-wrap">
              <div className="vlbl">PA AKCİĞER GRAFİSİ</div>
              <div className="vinfo">NIH-CXR14</div>
              <div className="vwl">W:2048 L:0</div>
              <div className="scan" />
              <svg className="ov" />
              {/* placeholder for CXR image */}
              <div
                style={{
                  width: 320,
                  height: 380,
                  border: "1px solid rgba(26,159,168,.15)",
                  borderRadius: 8,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--t3)",
                  fontSize: 11,
                  fontFamily: "JetBrains Mono, monospace",
                }}
              >
                CXR — {pt.name}
              </div>
            </div>
          )}

          {/* CT grid */}
          {activePip === 2 && (
            <div className="ct-grid" style={{ flex: 1 }}>
              {["Axial", "Coronal", "Sagittal", "3D MIP"].map((label) => (
                <div className="vpane" key={label}>
                  <div className="vlbl">{label}</div>
                  <div
                    style={{
                      position: "absolute",
                      inset: 0,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "var(--t3)",
                      fontSize: 10,
                      fontFamily: "JetBrains Mono, monospace",
                    }}
                  >
                    {label} — {pt.name}
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
              {/* patient info card */}
              <div className="card">
                <div className="ch">
                  <div>
                    <div className="cn">{pt.name}</div>
                    <div className="ci">#{pt.id} · {pt.g} · {pt.age} yaş</div>
                  </div>
                  <span className={`rb ${pt.rc}`}>RADS-{pt.rads}</span>
                </div>
                <div className="cgrid">
                  <div>
                    <div className="cl">Tetkik</div>
                    <div className="cv">{pt.cxr.tk}</div>
                  </div>
                  <div>
                    <div className="cl">Tarih</div>
                    <div className="cv">13.03.2026</div>
                  </div>
                  <div>
                    <div className="cl">Cihaz</div>
                    <div className="cv">{pt.cxr.ci}</div>
                  </div>
                  <div>
                    <div className="cl">Çözünürlük</div>
                    <div className="cv">{pt.cxr.rs}</div>
                  </div>
                </div>
              </div>

              {/* CXR start button */}
              {!cxrDone && !cxrRunning && (
                <button className="ai-btn" onClick={runCXR}>
                  ▶ Pipeline 1 — CXR Analizi Başlat
                </button>
              )}

              {/* CXR progress bar */}
              {(cxrRunning || cxrDone) && (
                <div className="pbar-w" style={{ display: cxrRunning ? undefined : "none" }}>
                  <div className="pbar-l">CXR Pipeline İlerlemesi</div>
                  <div className="pbar-tr">
                    <div className="pbar-fl" style={{ width: `${cxrProgress}%` }} />
                  </div>
                  <div className="pbar-st">{cxrStep}</div>
                </div>
              )}

              {/* CXR Ensemble agents */}
              {showAgents && (
                <div className="agents">
                  <div className="plbl">CXR Ensemble Sonuçları</div>
                  {pt.agents.map((a, i) => (
                    <div className="arow" key={i}>
                      <div className="an">{a.n}</div>
                      <div className="abar">
                        <div
                          className="afill"
                          style={{ width: `${a.p}%`, background: a.c }}
                        />
                      </div>
                      <div className="av" style={{ color: a.c }}>
                        {a.p}%
                      </div>
                    </div>
                  ))}
                  <div className="adec">{pt.cdec}</div>
                </div>
              )}

              {/* CT prompt */}
              {showCtPrompt && pt.ct && (
                <div className="ct-prompt" onClick={handleCtPromptClick}>
                  <div className="ctp-t">🔬 BT Analizi Öneriliyor</div>
                  <div className="ctp-s">
                    RADS-{pt.rads} ≥ 3 — Düşük doz BT ile ileri değerlendirme önerilmektedir.
                    <br />
                    Pipeline 2&apos;yi başlatmak için tıklayın.
                  </div>
                </div>
              )}

              {/* CT start button (when on pip 2 but not yet started) */}
              {activePip === 2 && !ctRunning && !ctDone && cxrDone && pt.ct && !showCtPrompt && (
                <button className="ai-btn ct" onClick={runCT}>
                  ▶ Pipeline 2 — BT Analizi Başlat
                </button>
              )}

              {/* CT progress bar */}
              {ctRunning && (
                <div className="pbar-w">
                  <div className="pbar-l">BT Pipeline İlerlemesi</div>
                  <div className="pbar-tr">
                    <div className="pbar-fl" style={{ width: `${ctProgress}%` }} />
                  </div>
                  <div className="pbar-st">{ctStep}</div>
                </div>
              )}

              {/* Lung-RADS box */}
              {showRads && (
                <div className="rads-box">
                  <div className="rads-l">Lung-RADS Skoru</div>
                  <div className="rads-n" style={{ color: pt.rcolor }}>
                    {pt.rads}
                  </div>
                  <div className="rads-nm" style={{ color: pt.rcolor }}>
                    {pt.rname}
                  </div>
                  <div
                    className="rads-ac"
                    style={{
                      background: `${pt.rcolor}11`,
                      color: pt.rcolor,
                      border: `1px solid ${pt.rcolor}33`,
                    }}
                  >
                    {pt.ract}
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
                      <div className="pst">✓</div>
                    </div>
                  ))}
                  {pt.ct &&
                    CT_STEPS.map((s, i) => (
                      <div className="ps" key={`ct-${i}`}>
                        <div className="psi pok">{s.icon}</div>
                        <div className="psn">{s.name}</div>
                        <div className="psd">{s.dur}</div>
                        <div className="pst">✓</div>
                      </div>
                    ))}
                </div>
              )}

              {/* Nodule findings */}
              {showNodules && pt.nods.length > 0 && (
                <div className="nod-card">
                  <div className="plbl">Nodül Bulguları</div>
                  {pt.nods.map((n, i) => (
                    <div className="ni" key={i}>
                      <div className="nth">
                        <div className="nc" style={{ background: `${n.c}22`, color: n.c }}>
                          {i + 1}
                        </div>
                      </div>
                      <div className="nd">
                        <div className="nsz">{n.sz}</div>
                        <div className="nloc">{n.loc}</div>
                        <div className="mbar">
                          <div
                            className="mfill"
                            style={{ width: `${n.mal}%`, background: n.c }}
                          />
                        </div>
                      </div>
                      <div className="nsco">
                        <div className="nsv" style={{ color: n.c }}>
                          %{n.mal}
                        </div>
                        <div className="nsl">malignite</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* ── TAB 1: Rapor ── */}
            <div className={`tc${rightTab === 1 ? " on" : ""}`}>
              <div className="rbox">
                <div className="rh">
                  <div className="rt">Radyoloji Raporu</div>
                  <div style={{ fontSize: 9, color: "var(--t3)" }}>
                    #{pt.id} · {pt.name}
                  </div>
                </div>
                {reportText()}
                <div style={{ display: "flex", gap: 5, marginTop: 10 }}>
                  <button className="pbtn" onClick={() => showToast("PDF oluşturuldu")}>
                    📄 PDF
                  </button>
                  <button className="pbtn" onClick={() => showToast("PACS'a gönderildi")}>
                    🏥 PACS
                  </button>
                  <button className="pbtn" onClick={() => showToast("FHIR R4 gönderildi")}>
                    🔗 FHIR
                  </button>
                  <button className="pbtn" onClick={() => showToast("Kurul listesine eklendi")}>
                    👥 Kurul
                  </button>
                </div>
              </div>
            </div>

            {/* ── TAB 2: Geçmiş ── */}
            <div className={`tc${rightTab === 2 ? " on" : ""}`}>
              <div className="plbl">Geçmiş Tetkikler</div>
              {pt.hx.map((h, i) => (
                <div className="hi" key={i}>
                  <div className="hd">{h.d}</div>
                  <div style={{ flex: 1 }}>
                    <div className="hn">{h.t}</div>
                    <div className="hdt">{h.r}</div>
                  </div>
                  <span className={`rb ${h.rc}`}>{h.r}</span>
                </div>
              ))}
              {pt.trend && (
                <div className="card" style={{ marginTop: 8 }}>
                  <div className="plbl">Trend Analizi</div>
                  <div style={{ fontSize: 11, color: "var(--t2)", lineHeight: 1.7 }}>
                    {pt.trend}
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
            ✕
          </button>
          <div className="mt">İstatistik Paneli</div>
          <div className="ms">
            Günlük analiz istatistikleri ve performans metrikleri
          </div>
          <div className="mb">
            Bugün toplam <strong>47</strong> analiz tamamlandı.
            <br />
            Ortalama pipeline süresi: <strong>4.2 dakika</strong>
            <br />
            RADS ≥ 3 oranı: <strong>%34</strong>
            <br />
            Yanlış pozitif oranı: <strong>%2.1</strong>
            <br />
            Model doğruluk (AUC): <strong>0.921</strong>
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
            ✕
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
            <br />
            Depolama: <strong>2.4 TB / 4 TB</strong>
          </div>
          <button className="mbtn-p" onClick={() => setModal(null)}>
            Tamam
          </button>
        </div>
      </div>
    </>
  );
}
