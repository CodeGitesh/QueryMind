#!/bin/bash
# ============================================================
# QueryMind — One-Shot Setup & Run Script (Colima Version)
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

# ── Step 1: Install Colima and Docker CLI ────────────────────────────────────────────
log "Installing Colima (Docker Engine alternative) and Docker CLI..."
brew install docker docker-compose colima 2>&1 | grep -E "(Downloading|Installing|Installed|Error|already)" || true
ok "Docker tools installed"

# ── Step 2: Launch Colima (Docker daemon) ─────────────────────────────────────────────
log "Starting Docker daemon via Colima (this may take a minute or two on first run)..."
colima start --network-address
ok "Docker daemon is running!"

# ── Step 3: Verify docker compose is available ────────────────────────────────
docker-compose version &>/dev/null || docker compose version &>/dev/null || fail "docker compose plugin not found."
COMPOSE_CMD="docker compose"
if ! command -v docker-compose &> /dev/null && command -v docker compose &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
fi
ok "docker compose is ready ($COMPOSE_CMD)"

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
$COMPOSE_CMD down --remove-orphans 2>/dev/null || true

# ── Step 7: Build and run everything ─────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD} Building & starting all services...${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

$COMPOSE_CMD up --build

echo -e "\n${GREEN}Stack started! Keep this terminal open.${NC}"
