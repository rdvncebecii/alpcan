# AlpCAN — Claude Code Kuralları

## Kapsam Kuralları (KRİTİK)

### Lokal
- **Sadece** `/Users/rdvncebeci/alpcan` klasörü ile çalış
- Başka dizinlere dokunma, başka projelerin dosyalarını değiştirme

### Sunucu
- Sunucu: `45.141.150.46`
- Sunucuda **sadece** `/root/alpcan` dizini ile işlem yap
- Aynı sunucuda 4 farklı proje çalışıyor — **sadece alpcan ile ilgilen:**
  - `alpiss.net` — DOKUNMA
  - `alpweb.alpiss.net` — DOKUNMA
  - `gruweb.alpiss.net` — DOKUNMA
  - **`alpcan.alpiss.net`** — SADECE BU

### Portlar
- Backend: `127.0.0.1:8010:8000` — değiştirme, başka portla karıştırma
- Frontend: `127.0.0.1:3010:3000` — değiştirme, başka portla karıştırma
- Orthanc: `127.0.0.1:8052:8042` ve `4242:4242`
- Bu portlar diğer projelerle çakışmamak için seçildi, DEĞİŞTİRME

### Nginx
- Sadece `alpcan.alpiss.net` server bloğunu düzenle
- Diğer subdomain'lerin nginx config'lerine DOKUNMA
- Nginx config yolu: `/etc/nginx/sites-available/alpcan.alpiss.net`

### Docker
- Compose dosyası: `docker-compose.prod.yml`
- Container isimleri `alpcan-` prefiksi ile
- Diğer projelerin container'larına dokunma

### Deploy
- Deploy script: `deploy/deploy-remote.sh`
- Sunucuda sadece `/root/alpcan` altında işlem yapar
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
