# AlpCAN — Cancer Analysis Network

**Radyolojik Görüntülerden Akciğer Kanseri Erken Tespiti İçin Yapay Zekâ Tabanlı Karar Destek Platformu**

ALPISS Intelligent Solution Suite — AlpCAN Modülü

## Mimari

- **Pipeline 1 (CXR):** 4 model ensemble ile akciğer röntgeni otomatik tarama
- **Pipeline 2 (BT):** 6 ajanlı derin analiz — nodül tespiti, karakterizasyon, büyüme takibi, Lung-RADS rapor

## Tech Stack

| Katman | Teknoloji |
|--------|-----------|
| Backend | FastAPI + PostgreSQL + Celery + Redis |
| Frontend | Next.js + shadcn/ui + Tailwind CSS |
| DICOM | Orthanc + OHIF Viewer v3 |
| ML | PyTorch + MONAI + nnU-Net v2 |
| Deploy | Docker Compose + Nginx |

## Hızlı Başlangıç

```bash
cp .env.example .env
docker-compose up -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1
- API Docs: http://localhost:8000/docs
- Orthanc: http://localhost:8042

## Proje Yapısı

```
alpcan/
├── backend/          # FastAPI API + YZ Ajanları
├── frontend/         # Next.js Klinik Arayüz
├── ml/               # Model tanımları + inference
├── notebooks/        # Eğitim notebook'ları (RunPod/Colab)
├── orthanc/          # DICOM sunucu config
└── docs/             # Dokümantasyon
```

## Lisans

Proprietary — ALPISS Intelligent Solution Suite
