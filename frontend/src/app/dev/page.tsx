"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { AGENTS, DATASETS } from "@/lib/data";
import type { AgentData, DatasetInfo } from "@/lib/types";

/* ── status helpers ── */
const ST_ICON: Record<string, string> = { ok: "✓", tr: "⟳", id: "◐", wa: "·" };
const ST_CLS: Record<string, string> = { ok: "st-ok", tr: "st-tr", id: "st-id", wa: "st-wa" };

/* ── random helpers ── */
const rnd = (min: number, max: number) => Math.random() * (max - min) + min;
const rndInt = (min: number, max: number) => Math.floor(rnd(min, max));

/* ── log message generator ── */
function genLogMsg(epoch: number): { cls: string; text: string } {
  const dice = rnd(0.82, 0.96).toFixed(4);
  const loss = rnd(0.01, 0.15).toFixed(4);
  const gpu = rndInt(60, 98);
  const templates: { cls: string; text: string }[] = [
    { cls: "li", text: `[Epoch ${epoch}] train_loss=${loss} val_dice=${dice} gpu=${gpu}% lr=1e-4` },
    { cls: "lok", text: `[Epoch ${epoch}] ✓ Val Dice improved → ${dice} — checkpoint saved` },
    { cls: "lt", text: `[Epoch ${epoch}] GPU: ${gpu}% | VRAM: ${rndInt(45, 75)}GB/80GB | Temp: ${rndInt(55, 82)}°C` },
    { cls: "lw", text: `[Epoch ${epoch}] ⚠ Learning rate warmup — cosine annealing step` },
    { cls: "ld", text: `[Epoch ${epoch}] Batch ${rndInt(1, 200)}/${rndInt(200, 400)} — loss=${loss} dice=${dice}` },
    { cls: "li", text: `[Epoch ${epoch}] Augmentation: RandFlip + RandRotate90 + RandGaussianNoise` },
    { cls: "lok", text: `[Epoch ${epoch}] ✓ Best AUC: ${rnd(0.93, 0.98).toFixed(4)} — model exported` },
    { cls: "le", text: `[Epoch ${epoch}] ✗ OOM risk — reducing batch_size 16→12` },
  ];
  return templates[Math.floor(Math.random() * templates.length)];
}

export default function DevPage() {
  /* ── state ── */
  const [selAgent, setSelAgent] = useState(4); // A-CXR-4 MedRAX (index 4)
  const [rightTab, setRightTab] = useState(0); // 0=Ajan, 1=GPU, 2=Veri Seti
  const [epoch, setEpoch] = useState(62);
  const [valDice, setValDice] = useState("0.8910");
  const [trainLoss, setTrainLoss] = useState("0.0987");
  const [gpuMem, setGpuMem] = useState("62.4 GB");
  const [eta, setEta] = useState("4s 12dk");
  const [logLines, setLogLines] = useState<{ cls: string; text: string }[]>([
    { cls: "lt", text: "[System] AlpCAN Model Lab v3.0 — A100 80GB bağlandı" },
    { cls: "lok", text: "[System] ✓ CUDA 12.4 | cuDNN 9.1 | PyTorch 2.3.1" },
    { cls: "li", text: "[System] MedRAX Segm. eğitimi başlatıldı — Epoch 62/300" },
  ]);
  const [isRunning, setIsRunning] = useState(true);
  const [isStopped, setIsStopped] = useState(false);
  const [toastMsg, setToastMsg] = useState("");
  const [toastVisible, setToastVisible] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalTitle, setModalTitle] = useState("");
  const [modalSub, setModalSub] = useState("");
  const [modalBody, setModalBody] = useState("");

  /* GPU stats */
  const [gpuUsage, setGpuUsage] = useState(78);
  const [gpuMemPct, setGpuMemPct] = useState(78);
  const [gpuTemp, setGpuTemp] = useState(72);
  const [cpuUsage, setCpuUsage] = useState(34);
  const [ramUsage, setRamUsage] = useState(45);

  const logRef = useRef<HTMLDivElement>(null);
  const lossCanvasRef = useRef<HTMLCanvasElement>(null);
  const metricCanvasRef = useRef<HTMLCanvasElement>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const gpuIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /* ── toast ── */
  const showToast = useCallback((msg: string) => {
    setToastMsg(msg);
    setToastVisible(true);
    setTimeout(() => setToastVisible(false), 2200);
  }, []);

  /* ── select agent ── */
  const selectAjan = useCallback(
    (i: number) => {
      setSelAgent(i);
      setRightTab(0);
      showToast(`${AGENTS[i].icon} ${AGENTS[i].name} seçildi`);
    },
    [showToast]
  );

  /* ── training controls ── */
  const toggleTraining = useCallback(() => {
    if (isStopped) return;
    setIsRunning((prev) => {
      const next = !prev;
      showToast(next ? "▶ Eğitim devam ediyor" : "⏸ Eğitim duraklatıldı");
      return next;
    });
  }, [isStopped, showToast]);

  const resetTraining = useCallback(() => {
    setEpoch(0);
    setValDice("0.0000");
    setTrainLoss("1.0000");
    setLogLines([{ cls: "lw", text: "[System] ⚠ Eğitim sıfırlandı — Epoch 0" }]);
    setIsRunning(true);
    setIsStopped(false);
    showToast("↺ Eğitim sıfırlandı");
  }, [showToast]);

  const stopTraining = useCallback(() => {
    setIsRunning(false);
    setIsStopped(true);
    setLogLines((prev) => [...prev, { cls: "le", text: "[System] ■ Eğitim durduruldu" }]);
    showToast("■ Eğitim durduruldu");
  }, [showToast]);

  /* ── draw charts ── */
  const drawChart = useCallback(
    (canvas: HTMLCanvasElement | null, type: "loss" | "metric") => {
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const W = canvas.width;
      const H = canvas.height;
      ctx.clearRect(0, 0, W, H);

      // grid
      ctx.strokeStyle = "rgba(255,255,255,.04)";
      ctx.lineWidth = 1;
      for (let y = 0; y < H; y += H / 5) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(W, y);
        ctx.stroke();
      }

      const pts = 50;
      if (type === "loss") {
        // train loss curve
        ctx.strokeStyle = "rgba(232,69,95,.7)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        for (let i = 0; i < pts; i++) {
          const x = (i / (pts - 1)) * W;
          const base = 0.8 * Math.exp(-i * 0.06) + 0.05;
          const y = H - base * H * 0.9 + rnd(-3, 3);
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.stroke();

        // val loss curve
        ctx.strokeStyle = "rgba(34,188,198,.7)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        for (let i = 0; i < pts; i++) {
          const x = (i / (pts - 1)) * W;
          const base = 0.75 * Math.exp(-i * 0.055) + 0.08;
          const y = H - base * H * 0.9 + rnd(-4, 4);
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.stroke();
      } else {
        // Dice curve
        ctx.strokeStyle = "rgba(45,216,138,.7)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        for (let i = 0; i < pts; i++) {
          const x = (i / (pts - 1)) * W;
          const base = 1 - 0.9 * Math.exp(-i * 0.08);
          const y = H - base * H * 0.85 + rnd(-3, 3);
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.stroke();

        // AUC curve
        ctx.strokeStyle = "rgba(245,162,32,.7)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        for (let i = 0; i < pts; i++) {
          const x = (i / (pts - 1)) * W;
          const base = 1 - 0.85 * Math.exp(-i * 0.07);
          const y = H - base * H * 0.85 + rnd(-4, 4);
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
    },
    []
  );

  /* ── effects ── */

  // draw charts on mount
  useEffect(() => {
    drawChart(lossCanvasRef.current, "loss");
    drawChart(metricCanvasRef.current, "metric");
  }, [drawChart]);

  // training log interval
  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (isRunning && !isStopped) {
      intervalRef.current = setInterval(() => {
        setEpoch((prev) => {
          const next = prev + 1;
          const newDice = rnd(0.88, 0.96).toFixed(4);
          const newLoss = rnd(0.01, 0.12).toFixed(4);
          setValDice(newDice);
          setTrainLoss(newLoss);
          setGpuMem(`${rnd(58, 74).toFixed(1)} GB`);
          setEta(`${rndInt(1, 8)}s ${rndInt(5, 30)}dk`);
          const msg = genLogMsg(next);
          setLogLines((prev) => [...prev.slice(-150), msg]);
          drawChart(lossCanvasRef.current, "loss");
          drawChart(metricCanvasRef.current, "metric");
          return next;
        });
      }, 1600);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isRunning, isStopped, drawChart]);

  // GPU monitoring
  useEffect(() => {
    gpuIntervalRef.current = setInterval(() => {
      setGpuUsage(rndInt(65, 98));
      setGpuMemPct(rndInt(60, 92));
      setGpuTemp(rndInt(58, 85));
      setCpuUsage(rndInt(20, 55));
      setRamUsage(rndInt(35, 65));
    }, 2000);
    return () => {
      if (gpuIntervalRef.current) clearInterval(gpuIntervalRef.current);
    };
  }, []);

  // auto scroll log
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logLines]);

  /* ── modal helpers ── */
  const openModal = (title: string, sub: string, body: string) => {
    setModalTitle(title);
    setModalSub(sub);
    setModalBody(body);
    setModalOpen(true);
  };

  /* ── derived ── */
  const agent: AgentData = AGENTS[selAgent];
  const pip1 = AGENTS.filter((a) => a.pip === 1);
  const pip2 = AGENTS.filter((a) => a.pip === 2);

  return (
    <>
      {/* ── HEADER ── */}
      <header className="hdr">
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <Link href="/" className="hlogo">
            <span className="hlogotext">AlpCAN</span>
            <span className="hlogosub">Model Lab</span>
            <span className="hbadge">Gelistirici</span>
          </Link>
          <nav className="hnav">
            <span className="hnp on">Model Egitimi</span>
            <span
              className="hnp"
              onClick={() =>
                openModal(
                  "MLflow Experiment Tracking",
                  "mlflow.alpcan.local:5000",
                  "MLflow, AlpCAN pipeline ajanlarinin egitim metriklerini, model versiyonlarini ve artifact'leri takip eder.\n\n• Experiment: alpcan-medrax-segm\n• Run ID: a3f8c1d2e4b6\n• Registered Models: 11\n• Total Runs: 847\n\nTum ajanlar MLflow uzerinden versiyon kontrol altindadir."
                )
              }
            >
              MLflow
            </span>
            <span
              className="hnp"
              onClick={() =>
                openModal(
                  "Google Colab Entegrasyonu",
                  "colab.research.google.com",
                  "AlpCAN notebook'lari Colab uzerinden GPU/TPU destekli calistirilabilir.\n\n• alpcan_train_medrax.ipynb — A100 egitim\n• alpcan_eval_pipeline.ipynb — Pipeline degerlendirme\n• alpcan_data_prep.ipynb — Veri hazirlama\n\nColab Pro+ ile A100 80GB erisimi saglanmaktadir."
                )
              }
            >
              Colab
            </span>
            <Link href="/radyolog" className="hnp">
              🏥 Radyolog
            </Link>
          </nav>
        </div>
        <div className="hright">
          <div className="live">
            <span className="ldot" />
            Egitim devam ediyor
          </div>
          <div className="uchip">
            <div className="uav">GE</div>
            Gelistirici
          </div>
        </div>
      </header>

      {/* ── 3-COLUMN LAYOUT ── */}
      <div className="glayout">
        {/* ── LEFT SIDEBAR ── */}
        <aside className="gsidebar">
          <div className="gsh">
            <div className="gslbl">Pipeline Ajanlari ({AGENTS.length})</div>
          </div>
          <div className="gsec">
            {/* Pipeline 1 */}
            <div className="gsec-t">Pipeline 1 — CXR ({pip1.length} ajan)</div>
            {AGENTS.map((a, i) =>
              a.pip === 1 ? (
                <div
                  key={a.code}
                  className={`gi${i === selAgent ? " sel" : ""}`}
                  onClick={() => selectAjan(i)}
                >
                  <div className="gi-ic">{a.icon}</div>
                  <div>
                    <div className="gi-n">{a.name}</div>
                    <div className="gi-c">{a.code}</div>
                  </div>
                  <span className={`gi-s ${ST_CLS[a.st]}`}>{ST_ICON[a.st]}</span>
                </div>
              ) : null
            )}

            {/* Pipeline 2 */}
            <div className="gsec-t">Pipeline 2 — BT ({pip2.length} ajan)</div>
            {AGENTS.map((a, i) =>
              a.pip === 2 ? (
                <div
                  key={a.code}
                  className={`gi${i === selAgent ? " sel" : ""}`}
                  onClick={() => selectAjan(i)}
                >
                  <div className="gi-ic">{a.icon}</div>
                  <div>
                    <div className="gi-n">{a.name}</div>
                    <div className="gi-c">{a.code}</div>
                  </div>
                  <span className={`gi-s ${ST_CLS[a.st]}`}>{ST_ICON[a.st]}</span>
                </div>
              ) : null
            )}
          </div>
        </aside>

        {/* ── CENTER PANEL ── */}
        <main className="gmain">
          {/* Metrics Grid */}
          <div className="gmetrics">
            <div className="gmc">
              <div className="gmc-l">Epoch</div>
              <div className="gmc-v">{epoch}</div>
              <div className="gmc-d">/ 300 hedef</div>
            </div>
            <div className="gmc">
              <div className="gmc-l">Val Dice</div>
              <div className="gmc-v" style={{ color: "var(--ok)" }}>
                {valDice}
              </div>
              <div className="gmc-d">hedef: 0.95+</div>
            </div>
            <div className="gmc">
              <div className="gmc-l">Train Loss</div>
              <div className="gmc-v" style={{ color: "var(--err)" }}>
                {trainLoss}
              </div>
              <div className="gmc-d">cross-entropy</div>
            </div>
            <div className="gmc">
              <div className="gmc-l">GPU Memory</div>
              <div className="gmc-v" style={{ color: "var(--tl)" }}>
                {gpuMem}
              </div>
              <div className="gmc-d">/ 80 GB A100</div>
            </div>
            <div className="gmc">
              <div className="gmc-l">ETA</div>
              <div className="gmc-v">{eta}</div>
              <div className="gmc-d">tahmini kalan</div>
            </div>
          </div>

          {/* Charts */}
          <div className="gcharts">
            <div className="gchart">
              <div className="gchart-t">Egitim / Dogrulama Kaybi</div>
              <canvas
                ref={lossCanvasRef}
                width={400}
                height={75}
                style={{ width: "100%", height: "calc(100% - 18px)" }}
              />
            </div>
            <div className="gchart">
              <div className="gchart-t">Metrik Trendi (Dice / AUC)</div>
              <canvas
                ref={metricCanvasRef}
                width={400}
                height={75}
                style={{ width: "100%", height: "calc(100% - 18px)" }}
              />
            </div>
          </div>

          {/* Training Log */}
          <div className="glog-wrap">
            <div className="glog-head">
              <div className="glog-title">Egitim Logu — Canli</div>
              <div className="glog-btns">
                <button
                  className={`gbtn${!isRunning && !isStopped ? " on" : ""}`}
                  onClick={toggleTraining}
                >
                  {isRunning ? "⏸ Duraklat" : "▶ Devam"}
                </button>
                <button className="gbtn" onClick={resetTraining}>
                  ↺ Sifirla
                </button>
                <button
                  className="gbtn"
                  onClick={() => showToast("📦 Log exported → training_log.jsonl")}
                >
                  📦 Export
                </button>
                <button className="gbtn danger" onClick={stopTraining}>
                  ■ Durdur
                </button>
              </div>
            </div>
            <div className="glog" ref={logRef}>
              {logLines.map((line, i) => (
                <div key={i} className={line.cls}>
                  {line.text}
                </div>
              ))}
            </div>
          </div>
        </main>

        {/* ── RIGHT PANEL ── */}
        <aside className="gright">
          <div className="grtabs">
            {["Ajan", "GPU", "Veri Seti"].map((label, i) => (
              <div
                key={label}
                className={`grtab${rightTab === i ? " on" : ""}`}
                onClick={() => setRightTab(i)}
              >
                {label}
              </div>
            ))}
          </div>
          <div className="grcont">
            {/* ── Tab 0: Ajan ── */}
            <div className={`gtc${rightTab === 0 ? " on" : ""}`}>
              <div className="adet">
                <div className="adet-n">
                  {agent.icon} {agent.name}
                </div>
                <div className="adet-c">{agent.code}</div>
                <div className="adet-g">
                  {Object.entries(agent.p).map(([k, v]) => (
                    <div key={k}>
                      <div className="adic">{k.replace(/_/g, " ")}</div>
                      <div className="adiv">{String(v)}</div>
                    </div>
                  ))}
                </div>
                <div className="adet-row">
                  <span className="adet-k">Model</span>
                  <span className="adet-v">{agent.model}</span>
                </div>
                <div className="adet-row">
                  <span className="adet-k">Framework</span>
                  <span className="adet-v">{agent.fw}</span>
                </div>
                <div className="adet-row">
                  <span className="adet-k">Cihaz</span>
                  <span className="adet-v">{agent.dev}</span>
                </div>
                <div className="adet-row">
                  <span className="adet-k">Veri Seti</span>
                  <span className="adet-v">{agent.data}</span>
                </div>
                <div className="adet-row">
                  <span className="adet-k">Dogruluk</span>
                  <span className="adet-v" style={{ color: "var(--ok)" }}>
                    {agent.acc}
                  </span>
                </div>
                <div className="adet-row">
                  <span className="adet-k">Hiz</span>
                  <span className="adet-v">{agent.spd}</span>
                </div>
                <div
                  style={{
                    fontSize: 10,
                    color: "var(--t2)",
                    marginTop: 8,
                    lineHeight: 1.6,
                  }}
                >
                  {agent.desc}
                </div>
              </div>
              <button
                className="gbtn"
                style={{ width: "100%", marginBottom: 5 }}
                onClick={() =>
                  openModal(
                    `MLflow — ${agent.code}`,
                    "mlflow.alpcan.local:5000",
                    `Experiment: alpcan-${agent.code.toLowerCase()}\nRun Count: ${rndInt(50, 300)}\nBest Metric: ${agent.acc}\nArtifacts: model.pt, config.yaml, metrics.json\n\nSon calistirma: ${rndInt(1, 12)} saat once`
                  )
                }
              >
                📊 MLflow Deneyleri
              </button>
              <button
                className="gbtn"
                style={{ width: "100%", marginBottom: 5 }}
                onClick={() => showToast(`📥 ${agent.code} weights indiriliyor...`)}
              >
                📥 Weights Indir
              </button>
              <button
                className="gbtn"
                style={{ width: "100%", marginBottom: 5 }}
                onClick={() => showToast(`🧪 ${agent.code} test pipeline baslatildi`)}
              >
                🧪 Test Pipeline
              </button>
            </div>

            {/* ── Tab 1: GPU ── */}
            <div className={`gtc${rightTab === 1 ? " on" : ""}`}>
              <div className="gpucard">
                <div className="gpun">NVIDIA A100 80GB SXM</div>
                <div className="gbar-info">
                  <span>GPU Kullanim</span>
                  <span>{gpuUsage}%</span>
                </div>
                <div className="gbar">
                  <div
                    className="gbar-fill gbf-u"
                    style={{ width: `${gpuUsage}%` }}
                  />
                </div>
                <div className="gbar-info" style={{ marginTop: 6 }}>
                  <span>VRAM</span>
                  <span>
                    {((gpuMemPct / 100) * 80).toFixed(1)} GB / 80 GB
                  </span>
                </div>
                <div className="gbar">
                  <div
                    className="gbar-fill gbf-m"
                    style={{ width: `${gpuMemPct}%` }}
                  />
                </div>
                <div className="gbar-info" style={{ marginTop: 6 }}>
                  <span>Sicaklik</span>
                  <span>{gpuTemp}°C</span>
                </div>
                <div className="gbar">
                  <div
                    className="gbar-fill gbf-t"
                    style={{ width: `${gpuTemp}%` }}
                  />
                </div>
              </div>

              <div className="gpucard">
                <div className="gpun">CPU — AMD EPYC 7763 64-Core</div>
                <div className="gbar-info">
                  <span>CPU Kullanim</span>
                  <span>{cpuUsage}%</span>
                </div>
                <div className="gbar">
                  <div
                    className="gbar-fill gbf-u"
                    style={{ width: `${cpuUsage}%` }}
                  />
                </div>
                <div className="gbar-info" style={{ marginTop: 6 }}>
                  <span>RAM</span>
                  <span>
                    {((ramUsage / 100) * 256).toFixed(0)} GB / 256 GB
                  </span>
                </div>
                <div className="gbar">
                  <div
                    className="gbar-fill gbf-m"
                    style={{ width: `${ramUsage}%` }}
                  />
                </div>
              </div>

              <div className="gpucard">
                <div className="gpun">Sistem Bilgisi</div>
                <div className="adet-row">
                  <span className="adet-k">CUDA</span>
                  <span className="adet-v">12.4</span>
                </div>
                <div className="adet-row">
                  <span className="adet-k">cuDNN</span>
                  <span className="adet-v">9.1.0</span>
                </div>
                <div className="adet-row">
                  <span className="adet-k">PyTorch</span>
                  <span className="adet-v">2.3.1+cu124</span>
                </div>
                <div className="adet-row">
                  <span className="adet-k">MONAI</span>
                  <span className="adet-v">1.3.0</span>
                </div>
                <div className="adet-row">
                  <span className="adet-k">Python</span>
                  <span className="adet-v">3.11.8</span>
                </div>
                <div className="adet-row">
                  <span className="adet-k">OS</span>
                  <span className="adet-v">Ubuntu 22.04</span>
                </div>
              </div>
            </div>

            {/* ── Tab 2: Veri Seti ── */}
            <div className={`gtc${rightTab === 2 ? " on" : ""}`}>
              {DATASETS.map((ds: DatasetInfo) => (
                <div key={ds.n} className="dset">
                  <div className="dset-n">{ds.n}</div>
                  <div className="dset-d">{ds.d}</div>
                  <div className="dset-s">
                    {ds.tags.map((t) => (
                      <span
                        key={t}
                        className="dst"
                        style={{
                          background: "rgba(26,159,168,.08)",
                          color: "var(--tl)",
                        }}
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>

      {/* ── TOAST ── */}
      <div className={`toast${toastVisible ? " show" : ""}`}>{toastMsg}</div>

      {/* ── MODAL ── */}
      <div
        className={`moverlay${modalOpen ? " open" : ""}`}
        onClick={() => setModalOpen(false)}
      >
        <div className="mbox" onClick={(e) => e.stopPropagation()}>
          <button className="mcls" onClick={() => setModalOpen(false)}>
            ✕
          </button>
          <div className="mt">{modalTitle}</div>
          <div className="ms">{modalSub}</div>
          <div className="mb" style={{ whiteSpace: "pre-line" }}>
            {modalBody}
          </div>
          <button className="mbtn-p" onClick={() => setModalOpen(false)}>
            Tamam
          </button>
        </div>
      </div>
    </>
  );
}
