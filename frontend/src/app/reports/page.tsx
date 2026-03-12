"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { LUNG_RADS_LABELS } from "@/lib/types";

const demoReport = {
  study_id: "study-001",
  patient_id: "ANON-001",
  report_date: "2026-03-12",
  overall_lung_rads: "3",
  nodules: [
    {
      id: 1,
      location: "Sag ust lob, posterior segment",
      size_mm: 8.2,
      volume_mm3: 288.5,
      density: "Solid",
      lung_rads: "3",
      malignancy_score: 0.35,
      recommendation: "6 ay sonra kontrol BT onerilir",
    },
    {
      id: 2,
      location: "Sol alt lob, bazal segment",
      size_mm: 4.1,
      volume_mm3: 36.1,
      density: "Buzlu cam (GGO)",
      lung_rads: "2",
      malignancy_score: 0.08,
      recommendation: "Yillik DDBT taramasi",
    },
  ],
  summary_tr:
    "Sag ust lobda 8.2 mm solid nodul — Lung-RADS 3. Sol alt lobda 4.1 mm buzlu cam nodul — Lung-RADS 2.",
  recommendation_tr:
    "6 ay sonra kontrol BT onerilir. Yillik DDBT taramasi devam etmelidir.",
};

export default function ReportsPage() {
  const overallInfo = LUNG_RADS_LABELS[demoReport.overall_lung_rads];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Raporlar</h2>
        <p className="text-muted-foreground">
          Lung-RADS 2022 yapılandırılmış raporlar
        </p>
      </div>

      {/* Report Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Lung-RADS Raporu</CardTitle>
              <CardDescription>
                Hasta: {demoReport.patient_id} | Tarih:{" "}
                {demoReport.report_date}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge className={overallInfo?.color}>
                Lung-RADS {demoReport.overall_lung_rads} —{" "}
                {overallInfo?.label}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-1">Ozet</h4>
              <p className="text-sm text-muted-foreground">
                {demoReport.summary_tr}
              </p>
            </div>
            <Separator />
            <div>
              <h4 className="font-medium mb-1">Tavsiye</h4>
              <p className="text-sm text-muted-foreground">
                {demoReport.recommendation_tr}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Nodule Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {demoReport.nodules.map((nodule) => {
          const noduleInfo = LUNG_RADS_LABELS[nodule.lung_rads];
          return (
            <Card key={nodule.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    Nodul #{nodule.id}
                  </CardTitle>
                  <Badge className={noduleInfo?.color}>
                    Lung-RADS {nodule.lung_rads}
                  </Badge>
                </div>
                <CardDescription>{nodule.location}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-muted-foreground">Boyut:</span>
                    <p className="font-medium">{nodule.size_mm} mm</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Hacim:</span>
                    <p className="font-medium">{nodule.volume_mm3} mm3</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Dansite:</span>
                    <p className="font-medium">{nodule.density}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">
                      Malignite Skoru:
                    </span>
                    <p className="font-medium">
                      {(nodule.malignancy_score * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
                <Separator className="my-3" />
                <p className="text-sm text-muted-foreground">
                  {nodule.recommendation}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardContent className="pt-6">
          <p className="text-xs text-muted-foreground text-center">
            Bu rapor AlpCAN yapay zeka destekli on degerlendirmedir. Nihai tani
            karari radyologa aittir.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
