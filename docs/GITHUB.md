# AlpCAN GitHub Bilgileri

## Repository
- **URL:** https://github.com/rdvncebecii/alpcan
- **Branch:** main
- **Visibility:** Public (veya Private — kontrol et)

## Lokal Proje Yolu
- **Proje dizini:** /Users/rdvncebeci/alpcan
- **Git remote:** origin → https://github.com/rdvncebecii/alpcan.git

## Push Komutu
```bash
cd /Users/rdvncebeci/alpcan
git add .
git commit -m "mesaj"
git push origin main
```

## CI/CD Pipeline (.github/workflows/ci.yml)
1. **backend-lint:** ruff ile Python linting
2. **backend-test:** pytest ile testler (SQLite in-memory)
3. **frontend-build:** npm ci && npm run build
4. **deploy:** (main branch push) SSH ile sunucuya auto-deploy

## GitHub Secrets (Settings > Secrets > Actions)
Aşağıdaki secret'lar CI/CD deploy için gerekli:
- `SERVER_HOST` → 45.141.150.46
- `SERVER_USER` → root
- `SERVER_SSH_KEY` → ~/.ssh/id_rsa içeriği (private key)

### Secret Ekleme
```bash
# GitHub CLI ile
gh secret set SERVER_HOST --body "45.141.150.46"
gh secret set SERVER_USER --body "root"
gh secret set SERVER_SSH_KEY < ~/.ssh/id_rsa
```

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
├── Caddyfile
└── deploy.sh
```
