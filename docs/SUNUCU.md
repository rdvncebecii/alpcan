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
- **Sunucudaki yol:** /root/alpcan
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
| celery     | -                         | ML inference worker          |

## NOT: Caddy YOK — sunucuda nginx reverse proxy kullanılıyor

## Komutlar

### Lokal makineden deploy
```bash
bash deploy/deploy-remote.sh
```

### Sunucuda
```bash
ssh -i ~/.ssh/id_rsa root@45.141.150.46
cd /root/alpcan

# Container durumu
docker compose -f docker-compose.prod.yml ps

# Loglar
docker compose -f docker-compose.prod.yml logs -f backend

# Restart
docker compose -f docker-compose.prod.yml restart

# Migration
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
```

## NOT: AlpISS
- AlpISS projesi aynı sunucuda (/var/www/alpiss)
- AlpCAN kendi PostgreSQL container'ını kullanır
- AlpISS'in DB'sine DOKUNMA
