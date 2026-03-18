#!/bin/bash

# AlpCAN — Lokal makineden sunucuya deploy
# Usage: bash deploy/deploy-remote.sh
# NOT: Proje kökünden çalıştırılmalı
#
# !! DİKKAT — KAPSAM KURALLARI !!
# Bu script SADECE alpcan projesi ile ilgilenir.
# Sunucuda 4 farklı proje çalışıyor:
#   - alpiss.net          -> DOKUNMA
#   - alpweb.alpiss.net   -> DOKUNMA
#   - gruweb.alpiss.net   -> DOKUNMA
#   - alpcan.alpiss.net   -> SADECE BU
#
# Portlar (sabit, değiştirme):
#   Backend:  127.0.0.1:8010:8000
#   Frontend: 127.0.0.1:3010:3000
#   Orthanc:  127.0.0.1:8052:8042, 4242:4242

set -e

# Configuration — env değişkenlerinden okunur, varsayılan değer YOKTUR
if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ]; then
    echo "HATA: SERVER_IP ve SERVER_USER env değişkenleri tanımlı olmalı."
    echo "  export SERVER_IP=x.x.x.x"
    echo "  export SERVER_USER=kullanici"
    exit 1
fi
DEPLOY_PATH="${DEPLOY_PATH:-/root/alpcan}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"
COMPOSE_FILE="docker-compose.prod.yml"

# Güvenlik kontrolü: deploy path sadece /root/alpcan olmalı
if [[ "$DEPLOY_PATH" != "/root/alpcan" ]]; then
    echo "HATA: Deploy path sadece /root/alpcan olabilir!"
    echo "  Mevcut: $DEPLOY_PATH"
    echo "  Diğer projelere deploy yapmayın."
    exit 1
fi

echo "======================================"
echo "AlpCAN Remote Deployment"
echo "======================================"
echo "Server: $SERVER_USER@$SERVER_IP"
echo "Deploy Path: $DEPLOY_PATH"
echo ""

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo "HATA: SSH key bulunamadı: $SSH_KEY"
    exit 1
fi

# Test SSH connection
echo "SSH bağlantısı test ediliyor..."
if ! ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$SERVER_USER@$SERVER_IP" exit 2>/dev/null; then
    echo "HATA: Sunucuya SSH ile bağlanılamadı"
    echo "  1. Sunucu açık mı?"
    echo "  2. SSH key ekli mi? ssh-copy-id -i $SSH_KEY $SERVER_USER@$SERVER_IP"
    exit 1
fi
echo "SSH bağlantısı OK"

# Proje kökünü bul
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Arşiv oluştur (macOS resource fork'ları dahil exclude)
echo ""
echo "Kaynak kod arşivi oluşturuluyor..."
COPYFILE_DISABLE=1 tar -czf /tmp/alpcan-deploy.tar.gz \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='.next' \
    --exclude='dist' \
    --exclude='build' \
    --exclude='.turbo' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='*.pyc' \
    --exclude='ml/weights/*.pt' \
    --exclude='ml/weights/*.pth' \
    --exclude='ml/weights/*.onnx' \
    --exclude='ml/weights/*.bin' \
    --exclude='ml/weights/**/*.pt' \
    --exclude='ml/weights/**/*.pth' \
    --exclude='ml/weights/**/*.onnx' \
    --exclude='ml/weights/**/*.bin' \
    --exclude='ml/weights/**/*.safetensors' \
    --exclude='*.dcm' \
    --exclude='*.nii.gz' \
    --exclude='.DS_Store' \
    --exclude='.env' \
    --exclude='.env.production' \
    .
echo "Arşiv oluşturuldu ($(du -h /tmp/alpcan-deploy.tar.gz | cut -f1))"

# Upload
echo ""
echo "Sunucuya yükleniyor..."
scp -i "$SSH_KEY" /tmp/alpcan-deploy.tar.gz "$SERVER_USER@$SERVER_IP:/tmp/"
echo "Yükleme tamamlandı"
rm /tmp/alpcan-deploy.tar.gz

# Deploy on server
echo ""
echo "Sunucuda deploy başlıyor..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" <<ENDSSH
    set -e

    DEPLOY_PATH="$DEPLOY_PATH"
    COMPOSE_FILE="$COMPOSE_FILE"

    echo "======================================"
    echo "Sunucu tarafı deploy"
    echo "======================================"

    mkdir -p \$DEPLOY_PATH
    cd \$DEPLOY_PATH

    # .env yedekle
    if [ -f .env ]; then
        cp .env /tmp/.alpcan-env-bak
        echo ".env yedeklendi"
    fi

    # Container'ları durdur
    if [ -f \$COMPOSE_FILE ]; then
        docker compose -f \$COMPOSE_FILE down --remove-orphans 2>/dev/null || true
    fi

    # Yeni kodu çıkart
    tar -xzf /tmp/alpcan-deploy.tar.gz --overwrite 2>/dev/null
    rm /tmp/alpcan-deploy.tar.gz

    # macOS resource fork'ları temizle
    find . -name '._*' -delete 2>/dev/null || true

    # .env geri yükle
    if [ -f /tmp/.alpcan-env-bak ]; then
        cp /tmp/.alpcan-env-bak .env
        rm /tmp/.alpcan-env-bak
        echo ".env geri yüklendi"
    fi

    # Build
    echo ""
    echo "Docker build..."
    docker compose -f \$COMPOSE_FILE build

    # Start
    echo ""
    echo "Servisler başlatılıyor..."
    docker compose -f \$COMPOSE_FILE up -d

    # DB bekle + migration
    sleep 10
    echo "Migration..."
    docker compose -f \$COMPOSE_FILE exec -T backend find /app -name '._*' -delete 2>/dev/null || true
    docker compose -f \$COMPOSE_FILE exec -T backend alembic upgrade head 2>&1 || echo "Migration atlandı"

    # Temizlik
    docker image prune -f 2>/dev/null || true

    echo ""
    docker compose -f \$COMPOSE_FILE ps
    echo ""
    echo "Deploy tamamlandı!"
ENDSSH

echo ""
echo "======================================"
echo "Deploy başarılı!"
echo "======================================"
echo ""
echo "  Web:  https://alpcan.alpiss.net"
echo "  API:  https://alpcan.alpiss.net/api/v1/health"
echo ""
echo "Loglar: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd $DEPLOY_PATH && docker compose -f $COMPOSE_FILE logs -f'"
echo ""
