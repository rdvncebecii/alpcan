# AlpCAN GitHub Bilgileri

## Repository
- **URL:** https://github.com/rdvncebecii/alpcan
- **Branch:** main

## CI/CD Pipeline (.github/workflows/ci.yml)
1. **backend-lint:** ruff ile Python linting
2. **backend-test:** pytest ile testler (SQLite in-memory)
3. **frontend-build:** npm ci && npm run build
4. **deploy:** (main branch push) SSH ile sunucuya auto-deploy

## GitHub Secrets (Settings > Secrets > Actions)
Aşağıdaki secret'lar CI/CD deploy için gerekli:
- `SERVER_HOST`
- `SERVER_USER`
- `SERVER_SSH_KEY`

Not: Secret değerleri GitHub Settings > Secrets > Actions üzerinden eklenir. Gerçek değerler repo'da saklanmaz.

## Proje Yapısı
```
alpcan/
├── backend/          # FastAPI + SQLAlchemy + Celery
│   ├── app/          # Ana uygulama
│   ├── alembic/      # DB migration'ları
│   └── tests/        # Pytest testleri
├── frontend/         # Next.js 16 App Router
│   └── src/app/      # Sayfalar (radyolog, yukle, dev)
├── ml/               # ML inference modülleri
│   ├── agents/       # 10 AI agent (nodule, cxr, medsam, vit, lung_rads...)
│   ├── preprocessing/# DICOM/NIfTI preprocessing
│   ├── evaluation/   # Metrikler + Lung-RADS scoring
│   └── configs/      # Model konfigürasyonları
├── notebooks/        # Kaggle notebook'ları + çıktıları
├── deploy/           # Sunucu kurulum scriptleri
├── docker-compose.prod.yml
└── deploy.sh
```
