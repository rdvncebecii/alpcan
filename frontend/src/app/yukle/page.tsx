"use client";

import { useState, useCallback, useRef } from "react";
import Link from "next/link";
import { uploadDicom, uploadDicomBatch } from "@/lib/api";

export default function YuklePage() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<{ name: string; ok: boolean; msg: string }[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

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
        }}
      >
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
            <div style={{ color: "var(--t2)", fontSize: 12, marginBottom: 8 }}>
              Sonuçlar
            </div>
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
                  {r.ok ? "OK" : "HATA"} — {r.name}
                </span>
                <span style={{ color: "var(--t3)" }}>{r.msg}</span>
              </div>
            ))}
            <Link
              href="/radyolog"
              className="ai-btn"
              style={{ marginTop: 12, display: "block", textAlign: "center", textDecoration: "none" }}
            >
              Radyolog Arayüzüne Git
            </Link>
          </div>
        )}
      </div>
    </>
  );
}
