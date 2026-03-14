# AlpCAN GitHub Bilgileri

## Repository
- **URL:** https://github.com/rdvncebecii/alpcan
- **Branch:** main

## CI/CD Pipeline (.github/workflows/ci.yml)
1. **backend-lint:** ruff ile Python linting
2. **backend-test:** pytest ile testler (SQLite in-memory)
3. **frontend-build:** npm ci && npm run build
4. **deploy:** (vars.DEPLOY_ENABLED == 'true' ise) SSH ile auto-deploy

## GitHub Secrets & Variables

### Secrets (Settings > Secrets > Actions)
```bash
gh secret set SERVER_HOST --body "45.141.150.46"
gh secret set SERVER_USER --body "root"
gh secret set SERVER_SSH_KEY < ~/.ssh/id_rsa
```

### Variables (Settings > Variables > Actions)
```bash
gh variable set DEPLOY_ENABLED --body "true"
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
│   ├── agents/       # 10 AI agent
│   ├── preprocessing/
│   ├── evaluation/   # Metrikler + Lung-RADS scoring
│   └── configs/
├── notebooks/        # Kaggle notebook'ları + outputs/
├── deploy/           # Deploy scriptleri
├── docs/             # Proje dokümantasyonu
└── docker-compose.prod.yml
```
