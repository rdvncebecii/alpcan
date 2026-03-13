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

      <div style={{ display: "flex", gap: 14 }}>
        <Link href="/radyolog" style={{ textDecoration: "none", color: "inherit" }}>
          <div className="sp-card">
            <div className="sp-icon">🏥</div>
            <div className="sp-ct">Radyolog Arayüzü</div>
            <div className="sp-cd">
              CXR → BT otomatik geçiş
              <br />
              Isı haritası · Lung-RADS · Raporlama
            </div>
          </div>
        </Link>
        <Link href="/dev" style={{ textDecoration: "none", color: "inherit" }}>
          <div className="sp-card">
            <div className="sp-icon">⚡</div>
            <div className="sp-ct">Geliştirici Paneli</div>
            <div className="sp-cd">
              Ajan eğitimi · GPU izleme
              <br />
              Metrikler · MLflow · Canlı log
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
