"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { LUNG_RADS_LABELS, STATUS_LABELS } from "@/lib/types";
import type { StudyStatus } from "@/lib/types";

const demoStudies = [
  {
    id: "study-001",
    patient_id: "ANON-001",
    modality: "CT",
    study_date: "2026-03-12",
    description: "Toraks BT",
    status: "completed" as StudyStatus,
    nodule_count: 2,
    lung_rads: "3",
  },
  {
    id: "study-002",
    patient_id: "ANON-002",
    modality: "CXR",
    study_date: "2026-03-12",
    description: "PA Akciğer Grafisi",
    status: "processing" as StudyStatus,
    nodule_count: null,
    lung_rads: null,
  },
  {
    id: "study-003",
    patient_id: "ANON-003",
    modality: "CT",
    study_date: "2026-03-11",
    description: "Toraks BT (kontrol)",
    status: "uploaded" as StudyStatus,
    nodule_count: null,
    lung_rads: null,
  },
];

export default function StudiesPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Çalışmalar</h2>
          <p className="text-muted-foreground">
            DICOM çalışma listesi ve analiz durumları
          </p>
        </div>
        <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm hover:bg-primary/90">
          DICOM Yükle
        </button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Çalışma Listesi</CardTitle>
          <CardDescription>
            Toplam {demoStudies.length} çalışma
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Hasta ID</TableHead>
                <TableHead>Modalite</TableHead>
                <TableHead>Tarih</TableHead>
                <TableHead>Açıklama</TableHead>
                <TableHead>Durum</TableHead>
                <TableHead>Nodül</TableHead>
                <TableHead>Lung-RADS</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {demoStudies.map((study) => {
                const statusInfo = STATUS_LABELS[study.status];
                const lungRadsInfo = study.lung_rads
                  ? LUNG_RADS_LABELS[study.lung_rads]
                  : null;
                return (
                  <TableRow key={study.id} className="cursor-pointer hover:bg-muted/50">
                    <TableCell className="font-medium">
                      {study.patient_id}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{study.modality}</Badge>
                    </TableCell>
                    <TableCell>{study.study_date}</TableCell>
                    <TableCell>{study.description}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{statusInfo.label}</Badge>
                    </TableCell>
                    <TableCell>
                      {study.nodule_count !== null ? study.nodule_count : "—"}
                    </TableCell>
                    <TableCell>
                      {lungRadsInfo ? (
                        <Badge variant="secondary">
                          {study.lung_rads} — {lungRadsInfo.label}
                        </Badge>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
