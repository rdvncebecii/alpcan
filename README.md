# AlpCAN — AI-Powered Lung Cancer Early Detection Platform

**Radyolojik Görüntülerden Akciğer Kanseri Erken Tespiti İçin Yapay Zekâ Tabanlı Karar Destek Platformu**

An AI-powered clinical decision support platform for early detection of lung cancer from radiological images, integrating 13 specialized deep learning agents across two clinical pipelines.

**Live Demo:** https://alpcan.alpiss.net

## Architecture

### Pipeline 1 — CXR (Chest X-ray Screening)
| Agent | Model | Performance |
|-------|-------|-------------|
| A-QC-1 | EfficientNet-B0 | Quality Control — 96.2% Acc |
| A-CXR-1 | Swin Transformer-L (Ark+) | Zero-shot — Nodule AUC 0.843, Mass AUC 0.896 |
| A-CXR-2 | DenseNet-121 (TorchXRayVision) | 18 pathologies — AUC 0.887 |
| A-CXR-3 | ResNet-50 + Transformer (X-Raydar) | 37 findings — AUC 0.904 |
| A-CXR-4 | MedSAM2 + SwinV2 | Segmentation — Dice 0.891 |

### Pipeline 2 — CT (Diagnostic)
| Agent | Model | Performance |
|-------|-------|-------------|
| A-BT-1 | SimpleITK + pydicom | DICOM Preprocessing — 100% KVKK |
| A-QC-2 | EfficientNet-B0 | CT Quality Control — 93.8% Acc |
| A-BT-2 | nnU-Net v2.5.1 ResEnc-L | Nodule Segmentation — Dice 0.942 |
| A-BT-6 | U-Net (ResNet-34 enc.) | Nodule Segmentation — Dice 0.622 |
| A-BT-7 | ResNet-50 + CBAM | Characterization — AUC 0.977 |
| A-BT-3 | 3D ResNet-50 + CBAM | Malignancy Classification — AUC 0.973 |
| A-BT-4 | Siamese 3D CNN + VoxelMorph | Growth Tracking — VDT Error <15% |
| A-BT-5 | Phi-3.5-mini LoRA | Turkish Report Generation |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + PostgreSQL 16 + Celery + Redis |
| Frontend | Next.js 16 + Tailwind CSS |
| DICOM | Orthanc PACS |
| ML | PyTorch 2.3.1 + MONAI + nnU-Net v2 |
| Deploy | Docker Compose + Nginx |

## Quick Start

```bash
git clone https://github.com/rdvncebecii/alpcan.git
cd alpcan
cp .env.example .env
docker compose up -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1
- API Docs: http://localhost:8000/docs
- Orthanc: http://localhost:8042

## Training Notebooks

All models are trained on Kaggle with publicly reproducible notebooks:

| # | Notebook | Status |
|---|---------|--------|
| 01 | LIDC-IDRI Exploration | Complete |
| 02 | CXR TorchXRayVision Baseline | Complete |
| 03 | CXR ResNet-50 | Complete |
| 04 | CXR MedSAM Segmentation | Complete |
| 05 | CXR Ark+ Zero-Shot | Complete |
| 06 | CT Nodule Segmentation (U-Net) | Complete — Dice 0.622 |
| 07 | CT Nodule Characterization | Complete — AUC 0.977 |
| 08 | CXR Ensemble Pipeline | Complete |
| 09 | CT Pipeline Integration | Complete |
| 10 | System Performance Report | Complete |
| 11 | nnU-Net Nodule Segmentation | Training |
| 12 | Turkish Radiology Report LLM | Complete |
| 13 | CT Malignancy Classification | Training |
| 14 | Reporting Engine | Complete |

## Datasets

| Dataset | Size | Source |
|---------|------|--------|
| LIDC-IDRI | 1018 CT, 7371 lesions | PhysioNet (CC BY) |
| NIH CXR-14 | 112,120 CXR, 14 labels | NIH (MIT) |
| CheXpert | 224,316 CXR, 14 labels | Stanford |
| MIMIC-CXR | 377,110 CXR + 227K reports | PhysioNet (credentialed) |
| LUNA16 | 888 CT, 1186 nodules | Grand Challenge (MIT) |

## Project Structure

```
alpcan/
├── backend/          # FastAPI + SQLAlchemy + Celery
│   ├── app/
│   │   ├── agents/   # 13 AI agents
│   │   ├── api/v1/   # REST endpoints
│   │   ├── models/   # SQLAlchemy models
│   │   └── services/ # Pipeline orchestration
│   └── tests/
├── frontend/         # Next.js 16 App Router
│   └── src/
│       ├── app/      # Pages (radyolog, dev, yukle)
│       └── lib/      # API client, hooks, types
├── ml/               # ML inference modules
│   ├── agents/       # Agent implementations
│   ├── inference/    # Model inference
│   ├── evaluation/   # Metrics + Lung-RADS scoring
│   └── preprocessing/# DICOM/NIfTI processing
├── notebooks/        # Kaggle training notebooks + outputs
├── deploy/           # Deployment scripts
├── orthanc/          # DICOM server config
├── docker-compose.yml
└── docker-compose.prod.yml
```

## Authors

- **Rıdvan Cebeci** — Giresun University, Dept. of Database, Network Design and Management
- **Figen Çiçek** — Giresun University, Dept. of Medical Services and Techniques

## License

MIT License
