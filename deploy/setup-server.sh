#!/usr/bin/env bash
# AlpCAN — İlk sunucu kurulumu (bir kez çalıştırılır)
# Usage: bash deploy/setup-server.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== AlpCAN Sunucu Kurulumu ===${NC}"
echo ""

# 1. Sistem güncellemesi
echo -e "${YELLOW}[1/6] Sistem güncelleniyor...${NC}"
apt-get update -qq && apt-get upgrade -y -qq

# 2. Docker kurulumu (yoksa)
if ! command -v docker &>/dev/null; then
    echo -e "${YELLOW}[2/6] Docker kuruluyor...${NC}"
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo -e "${GREEN}[2/6] Docker zaten kurulu: $(docker --version)${NC}"
fi

# Docker Compose plugin kontrolü
if ! docker compose version &>/dev/null; then
    echo -e "${YELLOW}Docker Compose plugin kuruluyor...${NC}"
    apt-get install -y -qq docker-compose-plugin
fi

# 3. Git kurulumu
if ! command -v git &>/dev/null; then
    echo -e "${YELLOW}[3/6] Git kuruluyor...${NC}"
    apt-get install -y -qq git
else
    echo -e "${GREEN}[3/6] Git zaten kurulu${NC}"
fi

# 4. Proje klonlama
DEPLOY_DIR="/alpcan"
if [ -d "$DEPLOY_DIR/.git" ]; then
    echo -e "${GREEN}[4/6] Proje zaten mevcut: $DEPLOY_DIR${NC}"
    cd "$DEPLOY_DIR"
    git pull origin main
else
    echo -e "${YELLOW}[4/6] Proje klonlanıyor...${NC}"
    git clone https://github.com/rdvncebecii/alpcan.git "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
fi

# 5. Production environment dosyası
if [ ! -f "$DEPLOY_DIR/.env.production" ]; then
    echo -e "${YELLOW}[5/6] Production environment oluşturuluyor...${NC}"
    cp "$DEPLOY_DIR/.env.production.example" "$DEPLOY_DIR/.env.production"

    # Secret key üret
    SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))" 2>/dev/null || openssl rand -base64 48)
    DB_PASS=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
    REDIS_PASS=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)

    sed -i "s|CHANGE_THIS_TO_RANDOM_64_CHAR_STRING|${SECRET}|g" "$DEPLOY_DIR/.env.production"
    sed -i "s|CHANGE_THIS_DB_PASSWORD|${DB_PASS}|g" "$DEPLOY_DIR/.env.production"
    sed -i "s|CHANGE_THIS_REDIS_PASSWORD|${REDIS_PASS}|g" "$DEPLOY_DIR/.env.production"

    echo -e "${GREEN}  Secret key, DB password, Redis password otomatik üretildi${NC}"
    echo -e "${YELLOW}  Dosyayı kontrol edin: $DEPLOY_DIR/.env.production${NC}"
else
    echo -e "${GREEN}[5/6] .env.production zaten mevcut${NC}"
fi

# 6. Firewall (ufw)
echo -e "${YELLOW}[6/6] Firewall ayarları...${NC}"
if command -v ufw &>/dev/null; then
    ufw allow 22/tcp    # SSH
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    ufw --force enable
    echo -e "${GREEN}  UFW aktif: SSH, HTTP, HTTPS açık${NC}"
fi

echo ""
echo -e "${GREEN}=== Kurulum Tamamlandı ===${NC}"
echo ""
echo "Sonraki adımlar:"
echo "  cd /alpcan"
echo "  bash deploy.sh --build"
echo "  bash deploy.sh --up"
echo "  bash deploy.sh --migrate"
echo "  bash deploy.sh --create-admin"
echo ""
echo -e "${GREEN}Site: https://alpcan.alpiss.net${NC}"
