# AlpCAN Sunucu Bilgileri

## SSH Erişimi
- **IP:** (lokal .env dosyasında)
- **Kullanıcı:** (lokal .env dosyasında)
- **SSH Key:** (lokal makinede)

## Domain
- **Domain:** alpcan.alpiss.net
- **SSL:** Sunucudaki nginx reverse proxy üzerinden
- **Cloudflare:** Domain Cloudflare üzerinden proxy ediliyor

## Deploy Dizini
- **Sunucudaki yol:** Lokal konfigürasyonda belirtilmiştir
- **Compose dosyası:** docker-compose.prod.yml
- **Env dosyası:** Sunucuda korunur

## Servisler (docker-compose.prod.yml)
| Servis     | Port (internal)           | Açıklama                     |
|------------|---------------------------|------------------------------|
| backend    | 8000                     | FastAPI (uvicorn)            |
| frontend   | 3000                     | Next.js (standalone)         |
| db         | 5432                     | PostgreSQL 16                |
| redis      | 6379                     | Redis 7                      |
| orthanc    | 8042, 4242               | DICOM sunucusu               |
| celery     | -                        | ML inference worker          |

## Önemli Komutlar

### Deploy (lokal makineden)
```bash
bash deploy/deploy-remote.sh
```

### Sunucuda doğrudan
```bash
# Container durumu
docker compose -f docker-compose.prod.yml ps

# Loglar
docker compose -f docker-compose.prod.yml logs -f

# Restart
docker compose -f docker-compose.prod.yml restart

# Migration
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
```
