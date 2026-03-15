import type { AgentData, DatasetInfo } from "./types";

export const AGENTS: AgentData[] = [
  {
    code: "A-QC-1", name: "Kalite Kontrol CXR", icon: "🔍", pip: 1, st: "ok",
    model: "EfficientNet-B0", fw: "PyTorch 2.3.1", dev: "CPU",
    data: "NIH CXR-14 (112K)", acc: "96.2%", spd: "<1s",
    p: { Epoch: 45, Loss: "0.0312", Val_Acc: "96.2%", Params: "5.3M" },
    desc: "EfficientNet-B0 tabanlı CXR kalite değerlendirme",
  },
  {
    code: "A-CXR-1", name: "CXR Ark+ Swin-L", icon: "🧠", pip: 1, st: "ok",
    model: "Swin Transformer-L", fw: "PyTorch 2.3.1", dev: "GPU T4 16GB",
    data: "NIH CXR-14 (112K)", acc: "AUC 0.878", spd: "2.1s",
    p: { Epoch: "zero-shot", Loss: "N/A", Val_AUC: "0.878", Params: "197M" },
    desc: "14 patoloji zero-shot — Nodule AUC 0.843, Mass AUC 0.896",
  },
  {
    code: "A-CXR-2", name: "TorchXRayVision", icon: "📊", pip: 1, st: "ok",
    model: "DenseNet-121", fw: "PyTorch 2.3.1", dev: "GPU RTX 4090",
    data: "NIH CXR-14 (112K)", acc: "AUC 0.887", spd: "1.8s",
    p: { Epoch: 90, Loss: "0.1876", Val_AUC: "0.887", Params: "7.9M" },
    desc: "18 patoloji — MIT lisanslı açık model",
  },
  {
    code: "A-CXR-3", name: "X-Raydar", icon: "📡", pip: 1, st: "ok",
    model: "ResNet-50 + Transformer", fw: "PyTorch 2.3.1", dev: "GPU RTX 4090",
    data: "CheXpert (224K)", acc: "AUC 0.904", spd: "2.3s",
    p: { Epoch: 85, Loss: "0.1654", Val_AUC: "0.904", Params: "28.4M" },
    desc: "37 bulgu — Lancet Digital Health 2023",
  },
  {
    code: "A-CXR-4", name: "MedRAX Segm.", icon: "✂️", pip: 1, st: "tr",
    model: "MedSAM2 + SwinV2", fw: "PyTorch 2.3.1", dev: "A100 80GB",
    data: "LUNA16 + LIDC-IDRI", acc: "Dice 0.891", spd: "3.1s",
    p: { Epoch: 62, Loss: "0.0987", Val_Dice: "0.891", Params: "312M" },
    desc: "Segmentasyon + lokalizasyon — ICML 2025",
  },
  {
    code: "A-BT-1", name: "DICOM Ön İşleme", icon: "⚙️", pip: 2, st: "ok",
    model: "SimpleITK + pydicom", fw: "Python 3.11", dev: "CPU 32 core",
    data: "Kural tabanlı", acc: "%100 KVKK", spd: "30-60s",
    p: { Dilim: 312, Anon: "%100", HU: "-1024/3071", Format: "DICOM SR" },
    desc: "Anonimleştirme + HU normalizasyon",
  },
  {
    code: "A-BT-2", name: "nnU-Net Nodül Segm.", icon: "🎯", pip: 2, st: "tr",
    model: "nnU-Net v2.5.1 ResEnc-L", fw: "PyTorch + MONAI", dev: "A100 80GB",
    data: "LUNA16 + LIDC-IDRI", acc: "Dice 0.9421", spd: "45-90s",
    p: { Epoch: 247, Loss: "0.0621", Val_Dice: "0.9421", Params: "31.4M" },
    desc: "Nodül segmentasyonu — MedNeurIPS Best Paper 2024",
  },
  {
    code: "A-BT-3", name: "Malignite Sınıf.", icon: "🔬", pip: 2, st: "ok",
    model: "3D ResNet-50 + CBAM", fw: "PyTorch 2.3.1", dev: "A100 80GB",
    data: "LIDC-IDRI + NLST", acc: "AUC 0.9731", spd: "2-5s",
    p: { Epoch: 180, Loss: "0.0834", Val_AUC: "0.9731", Params: "45.2M" },
    desc: "Nodül malignite + Lung-RADS skorlaması",
  },
  {
    code: "A-BT-4", name: "Büyüme Takibi", icon: "📈", pip: 2, st: "ok",
    model: "Siamese 3D CNN + VoxelMorph", fw: "PyTorch 2.3.1", dev: "A100 80GB",
    data: "NLST longitudinal", acc: "VDT Hata <%15", spd: "5-15s",
    p: { Epoch: 95, Loss: "0.1123", MAE: "1.84mm", Params: "28.7M" },
    desc: "Nodül büyüme analizi + VDT hesaplama",
  },
  {
    code: "A-BT-5", name: "Türkçe Rapor LLM", icon: "📝", pip: 2, st: "ok",
    model: "Meta-Llama-3-8B Q4_K_M", fw: "llama.cpp v0.2", dev: "CPU 32 core",
    data: "Türkçe rad. raporu fine-tune", acc: "BLEU 0.84", spd: "10-30s",
    p: { Model: "8B params", Quant: "Q4_K_M", VRAM: "0 CPU", Format: "PDF+FHIR" },
    desc: "Türkçe radyoloji raporu + FHIR R4 + DICOM SR",
  },
  {
    code: "A-QC-2", name: "Kalite Kontrol BT", icon: "🔍", pip: 2, st: "ok",
    model: "EfficientNet-B0", fw: "PyTorch 2.3.1", dev: "CPU",
    data: "RSNA CTP (2800 BT)", acc: "93.8%", spd: "<3s",
    p: { Epoch: 55, Loss: "0.0421", Val_Acc: "93.8%", Params: "5.3M" },
    desc: "BT çalışma kalite değerlendirme",
  },
  {
    code: "A-BT-6", name: "U-Net Nodül Segm.", icon: "🫁", pip: 2, st: "ok",
    model: "U-Net (ResNet-34 enc.)", fw: "PyTorch 2.3.1", dev: "T4 16GB (Kaggle)",
    data: "LIDC-IDRI (1018 BT)", acc: "Dice 0.622", spd: "10-30s",
    p: { Epoch: "50/50", Loss: "DiceBCE", Val_Dice: "0.622", Params: "24.4M" },
    desc: "Nodül segmentasyonu — Notebook 06 (tamamlandı)",
  },
  {
    code: "A-BT-7", name: "Karakterizasyon", icon: "🧬", pip: 2, st: "ok",
    model: "ResNet-50 + CBAM", fw: "PyTorch 2.3.1", dev: "T4 16GB (Kaggle)",
    data: "LIDC-IDRI (1018 BT)", acc: "AUC 0.977", spd: "2-5s",
    p: { Epoch: "14/40", Loss: "Focal+WCE", Val_AUC: "0.9769", Params: "45.2M" },
    desc: "Nodül karakterizasyonu — Suspicious AUC 0.977, Risk Acc 85.1%",
  },
];

export const DATASETS: DatasetInfo[] = [
  { n: "LUNA16", d: "888 düşük doz toraks BT, 1186 nodül anot.", tags: ["888 BT", "MIT", "5.2 GB"] },
  { n: "LIDC-IDRI", d: "1018 BT, 7371 anote lezyon, 4 radyolog", tags: ["1018 BT", "CC BY", "128 GB"] },
  { n: "NIH CXR-14", d: "112,120 PA röntgen, 14 patoloji etiketi", tags: ["112K", "MIT", "42 GB"] },
  { n: "NLST", d: "26,254 düşük doz BT, akciğer kanseri çıktı", tags: ["26K BT", "CC BY 4.0", "2.1 TB"] },
  { n: "CheXpert", d: "224,316 röntgen, Stanford — 14 etiket", tags: ["224K", "Stanford", "91 GB"] },
];
