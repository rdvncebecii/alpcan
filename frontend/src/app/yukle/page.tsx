"use client";

import { useState, useCallback, useRef } from "react";
import Link from "next/link";
import { uploadDicom, seedDemo, clearDemo } from "@/lib/api";

export default function YuklePage() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<{ name: string; ok: boolean; msg: string }[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [toast, setToast] = useState("");
  const [toastVisible, setToastVisible] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((msg: string) => {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast(msg);
    setToastVisible(true);
    toastTimer.current = setTimeout(() => setToastVisible(false), 3000);
  }, []);

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const arr = Array.from(newFiles).filter(
      (f) => f.name.endsWith(".dcm") || f.name.endsWith(".dicom") || f.type === "application/dicom"
    );
    if (arr.length === 0) {
      setResults((r) => [...r, { name: "-", ok: false, msg: "Sadece .dcm dosyaları kabul edilir" }]);
      return;
    }
    setFiles((prev) => [...prev, ...arr]);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      addFiles(e.dataTransfer.files);
    },
    [addFiles]
  );

  const handleUpload = useCallback(async () => {
    if (files.length === 0) return;
    setUploading(true);
    setResults([]);

    for (const file of files) {
      try {
        const res = await uploadDicom(file);
        setResults((r) => [
          ...r,
          { name: file.name, ok: true, msg: `Study: ${res.study_id.slice(0, 8)}...` },
        ]);
      } catch (err) {
        setResults((r) => [
          ...r,
          { name: file.name, ok: false, msg: err instanceof Error ? err.message : "Hata" },
        ]);
      }
    }

    setUploading(false);
    setFiles([]);
  }, [files]);

  const handleSeedDemo = useCallback(async () => {
    setDemoLoading(true);
    try {
      const res = await seedDemo();
      showToast(`${res.created} demo çalışma yüklendi`);
      setResults([{ name: "Demo", ok: true, msg: res.message }]);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Demo yüklenemedi");
      setResults([{ name: "Demo", ok: false, msg: err instanceof Error ? err.message : "Hata" }]);
    } finally {
      setDemoLoading(false);
    }
  }, [showToast]);

  const handleClearDemo = useCallback(async () => {
    setDemoLoading(true);
    try {
      const res = await clearDemo();
      showToast(`${res.deleted} çalışma silindi`);
      setResults([{ name: "Temizlik", ok: true, msg: res.message }]);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Temizleme başarısız");
      setResults([{ name: "Temizlik", ok: false, msg: err instanceof Error ? err.message : "Hata" }]);
    } finally {
      setDemoLoading(false);
    }
  }, [showToast]);

  const removeFile = useCallback((idx: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  }, []);

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
          <div className="hbadge">DICOM Yükle</div>
          <nav className="hnav">
            <Link href="/radyolog" className="hnp">Radyolog</Link>
            <Link href="/dev" className="hnp">Dev</Link>
          </nav>
        </div>
      </header>

      <div
        style={{
          maxWidth: 640,
          margin: "40px auto",
          padding: "0 20px",
          overflowY: "auto",
          height: "calc(100vh - 90px)",
        }}
      >
        {/* Demo section */}
        <div
          style={{
            background: "var(--s2)",
            border: "1px solid var(--b2)",
            borderRadius: 12,
            padding: "18px 20px",
            marginBottom: 24,
          }}
        >
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--tm)", marginBottom: 4, fontFamily: "Syne, sans-serif" }}>
            Demo Veri
          </div>
          <div style={{ fontSize: 11, color: "var(--t3)", marginBottom: 14, lineHeight: 1.6 }}>
            Sistemi test etmek için 12 adet gerçekçi hasta çalışması yükleyin.
            Tüm Lung-RADS kategorileri (1–4X) ve çeşitli modaliteler (CXR, BT) içerir.
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              className="ai-btn"
              onClick={handleSeedDemo}
              disabled={demoLoading}
              style={{ flex: 1 }}
            >
              {demoLoading ? "Yükleniyor..." : "Demo Veri Yükle"}
            </button>
            <button
              className="pbtn"
              onClick={handleClearDemo}
              disabled={demoLoading}
              style={{ whiteSpace: "nowrap", padding: "7px 14px" }}
            >
              {demoLoading ? "..." : "Tümünü Sil"}
            </button>
          </div>
        </div>

        {/* Divider */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
          <div style={{ flex: 1, height: 1, background: "var(--b1)" }} />
          <span style={{ fontSize: 10, color: "var(--t3)", fontFamily: "JetBrains Mono, monospace" }}>
            VEYA DICOM YÜKLE
          </span>
          <div style={{ flex: 1, height: 1, background: "var(--b1)" }} />
        </div>

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          style={{
            border: `2px dashed ${dragOver ? "var(--tl)" : "rgba(26,159,168,.25)"}`,
            borderRadius: 12,
            padding: "48px 24px",
            textAlign: "center",
            cursor: "pointer",
            background: dragOver ? "rgba(26,159,168,.05)" : "transparent",
            transition: "all .2s",
          }}
        >
          <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.5 }}>📁</div>
          <div style={{ color: "var(--t1)", fontSize: 14, marginBottom: 6 }}>
            DICOM dosyalarını sürükleyin veya tıklayın
          </div>
          <div style={{ color: "var(--t3)", fontSize: 11 }}>
            .dcm uzantılı dosyalar kabul edilir
          </div>
          <input
            ref={inputRef}
            type="file"
            accept=".dcm,.dicom,application/dicom"
            multiple
            style={{ display: "none" }}
            onChange={(e) => e.target.files && addFiles(e.target.files)}
          />
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div style={{ marginTop: 20 }}>
            <div style={{ color: "var(--t2)", fontSize: 12, marginBottom: 8 }}>
              {files.length} dosya seçildi
            </div>
            {files.map((f, i) => (
              <div
                key={`${f.name}-${i}`}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "6px 10px",
                  borderRadius: 6,
                  background: "var(--s2)",
                  marginBottom: 4,
                  fontSize: 11,
                }}
              >
                <span style={{ color: "var(--t1)" }}>{f.name}</span>
                <span
                  style={{ color: "var(--t3)", cursor: "pointer" }}
                  onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                >
                  &times;
                </span>
              </div>
            ))}
            <button
              className="ai-btn"
              onClick={handleUpload}
              disabled={uploading}
              style={{ marginTop: 12, width: "100%" }}
            >
              {uploading ? "Yükleniyor..." : `${files.length} dosya yükle`}
            </button>
          </div>
        )}

        {/* Results */}
        {results.length > 0 && (
          <div style={{ marginTop: 20 }}>
            <div style={{ color: "var(--t2)", fontSize: 12, marginBottom: 8 }}>Sonuçlar</div>
            {results.map((r, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "6px 10px",
                  borderRadius: 6,
                  background: r.ok ? "rgba(45,216,138,.08)" : "rgba(232,69,95,.08)",
                  marginBottom: 4,
                  fontSize: 11,
                }}
              >
                <span style={{ color: r.ok ? "var(--ok)" : "var(--err)" }}>
                  {r.ok ? "✓" : "✗"} — {r.name}
                </span>
                <span style={{ color: "var(--t3)" }}>{r.msg}</span>
              </div>
            ))}
            <Link
              href="/radyolog"
              className="ai-btn"
              style={{ marginTop: 12, display: "block", textAlign: "center", textDecoration: "none" }}
            >
              Radyolog Arayüzüne Git →
            </Link>
          </div>
        )}
      </div>

      {/* Toast */}
      <div className={`toast${toastVisible ? " show" : ""}`}>{toast}</div>
    </>
  );
}
