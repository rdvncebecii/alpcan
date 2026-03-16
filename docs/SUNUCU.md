# AlpCAN Sunucu Bilgileri

## SSH Erişimi
- **IP:** 45.141.150.46
- **Kullanıcı:** root
- **SSH Key:** ~/.ssh/id_rsa
- **Bağlantı:** `ssh -i ~/.ssh/id_rsa root@45.141.150.46`

## Domain
- **Domain:** alpcan.alpiss.net
- **SSL:** Sunucudaki nginx reverse proxy üzerinden
- **Cloudflare:** Domain Cloudflare üzerinden proxy ediliyor

## Deploy Dizini
- **Sunucudaki yol:** /root/alpcan (NOT: /alpcan değil!)
- **Compose dosyası:** docker-compose.prod.yml
- **Env dosyası:** /root/alpcan/.env

## Servisler (docker-compose.prod.yml)
| Servis     | Port (exposed)            | Açıklama                     |
|------------|---------------------------|------------------------------|
| backend    | 127.0.0.1:8010 → 8000    | FastAPI (uvicorn)            |
| frontend   | 127.0.0.1:3010 → 3000    | Next.js (standalone)         |
| db         | 5432 (internal)           | PostgreSQL 16                |
| redis      | 6379 (internal)           | Redis 7                      |
| orthanc    | 127.0.0.1:8052, 4242     | DICOM sunucusu               |
| celery     | -                        | ML inference worker          |

## NOT: Caddy YOK — sunucuda nginx reverse proxy kullanılıyor

## Önemli Komutlar

### Deploy (lokal makineden)
```bash
cd ~/Desktop/alpcan
bash deploy.sh
```

### Sunucuda doğrudan
```bash
ssh -i ~/.ssh/id_rsa root@45.141.150.46

# Container durumu
cd /root/alpcan && docker compose -f docker-compose.prod.yml ps

# Loglar
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend

# Restart
docker compose -f docker-compose.prod.yml restart

# Migration
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

# Admin oluştur
docker compose -f docker-compose.prod.yml exec -T backend python -c "
from app.core.security import get_password_hash
print(get_password_hash('SIFRE_BURAYA'))
"
```

## NOT: PostgreSQL
- AlpISS projesi aynı sunucuda çalışıyor
- AlpCAN kendi PostgreSQL container'ını kullanır (docker-compose.prod.yml içinde)
- AlpISS'in DB'sine DOKUNMA
