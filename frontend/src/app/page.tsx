"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const stats = [
  { label: "Toplam Çalışma", value: "0", description: "BT + CXR" },
  { label: "Bugün Analiz", value: "0", description: "İşlenen görüntü" },
  { label: "Bekleyen", value: "0", description: "Kuyrukta" },
  { label: "Şüpheli Bulgu", value: "0", description: "Takip gerektiren" },
];

const recentAnalyses = [
  {
    id: "demo-001",
    patient: "ANON-001",
    modality: "CT",
    status: "completed",
    lungRads: "3",
    date: "2026-03-12",
  },
  {
    id: "demo-002",
    patient: "ANON-002",
    modality: "CXR",
    status: "processing",
    lungRads: null,
    date: "2026-03-12",
  },
];

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <p className="text-muted-foreground">
          AlpCAN Platform durumu ve son analizler
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="pb-2">
              <CardDescription>{stat.label}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pipeline Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Pipeline 1 — CXR Tarama</CardTitle>
            <CardDescription>
              4 Model Ensemble (Ark+, TorchXRay, X-Raydar, MedRAX)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-green-500" />
              <span className="text-sm">Hazır</span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Ensemble oylama ile otomatik BT yönlendirme
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Pipeline 2 — BT Analiz</CardTitle>
            <CardDescription>
              6 Ajan (QC, Ön İşleme, nnU-Net, Karakterizasyon, Büyüme, Rapor)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-green-500" />
              <span className="text-sm">Hazır</span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Lung-RADS 2022 uyumlu Türkçe rapor
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Analyses */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Son Analizler</CardTitle>
          <CardDescription>En son işlenen çalışmalar</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentAnalyses.map((analysis) => (
              <div
                key={analysis.id}
                className="flex items-center justify-between p-3 rounded-lg border"
              >
                <div className="flex items-center gap-3">
                  <Badge variant="outline">{analysis.modality}</Badge>
                  <div>
                    <p className="text-sm font-medium">{analysis.patient}</p>
                    <p className="text-xs text-muted-foreground">
                      {analysis.date}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {analysis.lungRads && (
                    <Badge variant="secondary">
                      Lung-RADS {analysis.lungRads}
                    </Badge>
                  )}
                  <Badge
                    variant={
                      analysis.status === "completed" ? "default" : "secondary"
                    }
                  >
                    {analysis.status === "completed"
                      ? "Tamamlandı"
                      : "İşleniyor"}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
