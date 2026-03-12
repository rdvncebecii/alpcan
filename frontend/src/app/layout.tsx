import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/dashboard/sidebar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AlpCAN — Akciğer Kanseri Erken Tespit Platformu",
  description:
    "Yapay Zekâ Tabanlı Akciğer Kanseri Karar Destek Sistemi — ALPISS Intelligent Solution Suite",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <div className="flex h-screen bg-background">
          <Sidebar />
          <main className="flex-1 overflow-auto">
            <div className="p-6">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
