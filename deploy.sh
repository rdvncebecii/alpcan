#!/usr/bin/env bash
# AlpCAN — Production deployment script
# Usage: bash deploy.sh [--build | --up | --down | --logs | --status]

set -euo pipefail

COMPOSE="docker compose -f docker-compose.prod.yml"
ENV_FILE=".env.production"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_env() {
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}HATA: $ENV_FILE bulunamadı${NC}"
        echo "Önce .env.production.example dosyasını kopyalayın:"
        echo "  cp .env.production.example .env.production"
        echo "  # Değerleri düzenleyin (parolalar, secret key vb.)"
        exit 1
    fi

    # Check for default passwords
    if grep -q "CHANGE_THIS" "$ENV_FILE"; then
        echo -e "${RED}HATA: $ENV_FILE içinde varsayılan değerler var${NC}"
        echo "Lütfen tüm CHANGE_THIS değerlerini gerçek değerlerle değiştirin."
        exit 1
    fi
}

generate_secret() {
    python3 -c "import secrets; print(secrets.token_urlsafe(48))" 2>/dev/null || \
    openssl rand -base64 48 2>/dev/null || \
    head -c 48 /dev/urandom | base64
}

case "${1:-help}" in
    --build)
        check_env
        echo -e "${GREEN}Building production images...${NC}"
        $COMPOSE build --no-cache
        echo -e "${GREEN}Build complete.${NC}"
        ;;

    --up)
        check_env
        echo -e "${GREEN}Starting AlpCAN production...${NC}"
        $COMPOSE up -d
        echo -e "${GREEN}Services started. Checking health...${NC}"
        sleep 5
        $COMPOSE ps
        echo ""
        echo -e "${GREEN}AlpCAN is running at https://alpcan.alpiss.net${NC}"
        ;;

    --down)
        echo -e "${YELLOW}Stopping AlpCAN...${NC}"
        $COMPOSE down
        echo -e "${GREEN}Stopped.${NC}"
        ;;

    --logs)
        $COMPOSE logs -f --tail=100 "${2:-}"
        ;;

    --status)
        $COMPOSE ps
        echo ""
        echo "Health check:"
        curl -sf http://localhost:8000/api/v1/health 2>/dev/null && echo "" || echo -e "${RED}Backend not responding${NC}"
        ;;

    --migrate)
        check_env
        echo -e "${GREEN}Running Alembic migrations...${NC}"
        $COMPOSE exec backend alembic upgrade head
        echo -e "${GREEN}Migrations complete.${NC}"
        ;;

    --create-admin)
        check_env
        echo -e "${GREEN}Creating admin user...${NC}"
        $COMPOSE exec backend python3 -c "
import asyncio
from app.core.database import async_session
from app.models.user import User
from app.core.security import get_password_hash

async def create():
    async with async_session() as db:
        user = User(
            email='admin@alpcan.alpiss.net',
            full_name='AlpCAN Admin',
            hashed_password=get_password_hash('$(read -sp "Admin password: " pw && echo "$pw")'),
            role='admin',
        )
        db.add(user)
        await db.commit()
        print(f'Admin user created: {user.email}')

asyncio.run(create())
"
        ;;

    --secret)
        echo "Generated secret key:"
        generate_secret
        ;;

    *)
        echo "AlpCAN Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  --build         Build production Docker images"
        echo "  --up            Start all services"
        echo "  --down          Stop all services"
        echo "  --logs [svc]    View logs (optional: service name)"
        echo "  --status        Show service status"
        echo "  --migrate       Run Alembic database migrations"
        echo "  --create-admin  Create admin user"
        echo "  --secret        Generate a random secret key"
        echo ""
        echo "First-time setup:"
        echo "  1. cp .env.production.example .env.production"
        echo "  2. Edit .env.production with real values"
        echo "  3. bash deploy.sh --build"
        echo "  4. bash deploy.sh --up"
        echo "  5. bash deploy.sh --migrate"
        echo "  6. bash deploy.sh --create-admin"
        ;;
esac
