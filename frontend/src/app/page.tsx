import Link from "next/link";

export default function SplashPage() {
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
            TÜSEB 2026-C6 · Giresun Üniversitesi · v3.0
          </div>
        </div>
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
              Ajan eğitimi &middot; GPU izleme
              <br />
              Metrikler &middot; MLflow &middot; Canlı log
            </div>
          </div>
        </Link>
      </div>

      <div className="sp-foot">
        Demo — NIH CXR-14 açık veri · KVKK uyumlu yapay veri
      </div>
    </div>
  );
}
