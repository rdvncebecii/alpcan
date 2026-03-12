export type PipelineType = "ct" | "cxr";

export type StudyStatus = "uploaded" | "queued" | "processing" | "completed" | "error";

export type LungRADSCategory = "1" | "2" | "3" | "4A" | "4B" | "4X";

export const LUNG_RADS_LABELS: Record<string, { label: string; color: string }> = {
  "1": { label: "Negatif", color: "bg-green-500" },
  "2": { label: "Benign", color: "bg-green-400" },
  "3": { label: "Muhtemelen Benign", color: "bg-yellow-500" },
  "4A": { label: "Şüpheli (Düşük)", color: "bg-orange-500" },
  "4B": { label: "Şüpheli (Yüksek)", color: "bg-red-500" },
  "4X": { label: "Ek Bulgular", color: "bg-red-700" },
};

export const STATUS_LABELS: Record<StudyStatus, { label: string; color: string }> = {
  uploaded: { label: "Yüklendi", color: "bg-gray-500" },
  queued: { label: "Kuyrukta", color: "bg-blue-500" },
  processing: { label: "İşleniyor", color: "bg-yellow-500" },
  completed: { label: "Tamamlandı", color: "bg-green-500" },
  error: { label: "Hata", color: "bg-red-500" },
};
