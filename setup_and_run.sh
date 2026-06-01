#!/bin/bash
# ============================================================
# QueryMind — One-Shot Setup & Run Script
# ============================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${CYAN}[QueryMind]${NC} $*"; }
ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
fail() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

echo -e "\n${BOLD}╔═══════════════════════════════════════╗${NC}"
echo -e "${BOLD}║        QueryMind — Setup & Run        ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════╝${NC}\n"

# ── Step 1: Install Docker Desktop ────────────────────────────────────────────
if [ -d "/Applications/Docker.app" ]; then
    ok "Docker Desktop already installed"
else
    log "Installing Docker Desktop via Homebrew..."
    brew install --cask docker --no-quarantine 2>&1 | grep -E "(Downloading|Installing|Installed|Error|already)" || true
    
    if [ ! -d "/Applications/Docker.app" ]; then
        fail "Docker Desktop installation failed. Please download manually from https://www.docker.com/products/docker-desktop/"
    fi
    ok "Docker Desktop installed"
fi

# ── Step 2: Launch Docker Desktop ─────────────────────────────────────────────
log "Launching Docker Desktop..."
open -a Docker

# Wait until Docker daemon is running (up to 120 seconds)
log "Waiting for Docker daemon to start (this takes ~30-60 seconds)..."
WAITED=0
until docker info &>/dev/null; do
    if [ $WAITED -ge 120 ]; then
        fail "Docker didn't start in 120s. Please open Docker Desktop manually and re-run this script."
    fi
    printf "."
    sleep 3
    WAITED=$((WAITED + 3))
done
echo ""
ok "Docker daemon is running!"

# ── Step 3: Verify docker compose is available ────────────────────────────────
docker compose version &>/dev/null || fail "docker compose plugin not found. Reinstall Docker Desktop."
ok "docker compose is ready"

# ── Step 4: Restore the correct .env for Docker mode ─────────────────────────
log "Configuring .env for Docker mode..."
cat > .env << 'ENVEOF'
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=querymind
ENVIRONMENT=development
DEBUG=false
SECRET_KEY=dev-secret-key-change-in-production-32chars
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://querymind:querymind@postgres:5432/querymind
REDIS_URL=redis://redis:6379/0
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
RATE_LIMIT_REQUESTS=30
USE_SQLITE=false
ENVEOF
ok ".env configured"

# ── Step 5: Make init script executable ───────────────────────────────────────
chmod +x scripts/init-db.sh
ok "Database init script is executable"

# ── Step 6: Tear down any previous partial stack ──────────────────────────────
log "Cleaning up any previous containers..."
docker compose down --remove-orphans 2>/dev/null || true

# ── Step 7: Build and run everything ─────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD} Building & starting all services...${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

docker compose up --build

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║         QueryMind is running! 🚀      ║${NC}"
echo -e "${GREEN}${BOLD}╚═══════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}Frontend:${NC}  http://localhost:3000"
echo -e "  ${CYAN}Backend:${NC}   http://localhost:8000/docs"
echo -e "  ${CYAN}pgAdmin:${NC}   http://localhost:5050"
echo ""
