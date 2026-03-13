import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AlpCAN — Akciğer Kanseri Erken Tespit Platformu",
  description: "Yapay Zekâ Tabanlı Akciğer Kanseri Karar Destek Sistemi — ALPISS Intelligent Solution Suite",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  );
}
