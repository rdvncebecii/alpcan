# AlpCAN — Claude Code Kuralları

## Kapsam Kuralları (KRİTİK)

### Lokal
- **Sadece** proje klasörü ile çalış
- Başka dizinlere dokunma, başka projelerin dosyalarını değiştirme

### Sunucu
- Sunucu bilgileri lokal konfigürasyonda saklanır
- Sunucuda **sadece** proje dizini ile işlem yap
- Aynı sunucuda birden fazla proje çalışıyor — **sadece alpcan ile ilgilen**

### Portlar
- Backend: 8010:8000 — değiştirme, başka portla karıştırma
- Frontend: 3010:3000 — değiştirme, başka portla karıştırma
- Orthanc: 8052:8042 ve 4242:4242
- Bu portlar diğer projelerle çakışmamak için seçildi, DEĞİŞTİRME

### Nginx
- Sadece alpcan.alpiss.net server bloğunu düzenle
- Diğer subdomain'lerin nginx config'lerine DOKUNMA

### Docker
- Compose dosyası: `docker-compose.prod.yml`
- Container isimleri `alpcan-` prefiksi ile
- Diğer projelerin container'larına dokunma

### Deploy
- Deploy script: `deploy/deploy-remote.sh`
- Sunucuda sadece proje dizini altında işlem yapar
- Diğer dizinlere, servislere, container'lara müdahale etmez

## Teknik Bilgiler

### Stack
- **Backend:** FastAPI + SQLAlchemy (async) + Celery + Redis
- **Frontend:** Next.js 16 + Tailwind CSS
- **DB:** PostgreSQL 16
- **DICOM:** Orthanc
- **ML:** PyTorch modelleri (Kaggle'da eğitiliyor)

### Önemli Env Değişkenleri
- `NEXT_PUBLIC_API_URL`: Build-time değişken, Dockerfile.prod'da ARG olarak verilmeli
- `.env` dosyası sunucuda korunur, deploy sırasında üzerine yazılmaz

### API
- Base URL: `https://alpcan.alpiss.net/api/v1`
- Health: `/api/v1/health`
- Studies: `/api/v1/studies/`
