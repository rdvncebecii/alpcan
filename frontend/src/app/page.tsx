"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";

export default function SplashPage() {
  const [apiOk, setApiOk] = useState<boolean | null>(null);

  useEffect(() => {
    getHealth()
      .then(() => setApiOk(true))
      .catch(() => setApiOk(false));
  }, []);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 28,
        background:
          "radial-gradient(ellipse 90% 70% at 50% 40%, rgba(26,159,168,.07) 0%, var(--ink) 70%)",
      }}
    >
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            fontFamily: "Syne, sans-serif",
            fontSize: 48,
            fontWeight: 800,
            background: "linear-gradient(135deg, #fff, var(--tl))",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            marginBottom: 8,
          }}
        >
          AlpCAN
        </div>
        <div className="sp-sub">Akciğer Kanseri Erken Tespit Platformu</div>
        <div style={{ textAlign: "center" }}>
          <div className="sp-badge">
            TÜSEB 2026-C6 · Giresun Üniversitesi · v1.0.0-beta
          </div>
        </div>
      </div>

      {/* Backend status */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, fontFamily: "JetBrains Mono, monospace" }}>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: apiOk === null ? "var(--t3)" : apiOk ? "var(--ok)" : "var(--err)",
            boxShadow: apiOk ? "0 0 8px var(--ok)" : "none",
            display: "inline-block",
          }}
        />
        <span style={{ color: apiOk === null ? "var(--t3)" : apiOk ? "var(--ok)" : "var(--err)" }}>
          {apiOk === null ? "Backend kontrol ediliyor..." : apiOk ? "API bağlantısı aktif" : "API bağlantısı başarısız"}
        </span>
      </div>

      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", justifyContent: "center" }}>
        <Link href="/radyolog" style={{ textDecoration: "none", color: "inherit" }}>
          <div className="sp-card">
            <div className="sp-icon">🏥</div>
            <div className="sp-ct">Radyolog Arayüzü</div>
            <div className="sp-cd">
              CXR &rarr; BT otomatik geçiş
              <br />
              Isı haritası &middot; Lung-RADS &middot; Raporlama
            </div>
          </div>
        </Link>
        <Link href="/yukle" style={{ textDecoration: "none", color: "inherit" }}>
          <div className="sp-card">
            <div className="sp-icon">📁</div>
            <div className="sp-ct">DICOM Yükle</div>
            <div className="sp-cd">
              DICOM dosyası yükleme
              <br />
              Orthanc PACS entegrasyonu
            </div>
          </div>
        </Link>
        <Link href="/dev" style={{ textDecoration: "none", color: "inherit" }}>
          <div className="sp-card">
            <div className="sp-icon">⚡</div>
            <div className="sp-ct">Geliştirici Paneli</div>
            <div className="sp-cd">
              13 AI ajan &middot; GPU izleme
              <br />
              Metrikler &middot; MLflow &middot; Canlı log
            </div>
          </div>
        </Link>
      </div>

      <div className="sp-foot">
        TÜSEB Proje No: 2026-C6 · Giresun Üniversitesi Mühendislik Fakültesi · KVKK uyumlu
      </div>
    </div>
  );
}
