#!/usr/bin/env bash
#
# CE365 Agent - Docker Update mit Rollback
#
# Kontrolliertes Update der Docker-Container:
# 1. Aktuelle Image-Tags speichern
# 2. Neue Images pullen
# 3. Container neu starten
# 4. Health-Check (max 60s)
# 5. Bei Fehler: Rollback zu gespeicherten Images
#
# Usage: ./scripts/update.sh [docker-compose.yml Pfad]
#

set -euo pipefail

COMPOSE_FILE="${1:-docker-compose.yml}"
HEALTH_TIMEOUT=60
HEALTH_INTERVAL=5
HEALTH_ENDPOINT="http://localhost:80/health"
BACKUP_FILE="/tmp/ce365-update-backup.env"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Docker-Befehl finden (Synology hat Docker nicht im PATH)
DOCKER_CMD="docker"
if ! command -v docker &>/dev/null; then
    if [ -x "/usr/local/bin/docker" ]; then
        DOCKER_CMD="/usr/local/bin/docker"
    else
        log_error "Docker nicht gefunden"
        exit 1
    fi
fi

COMPOSE_CMD="$DOCKER_CMD compose"
if ! $COMPOSE_CMD version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
    if ! command -v docker-compose &>/dev/null; then
        log_error "Docker Compose nicht gefunden"
        exit 1
    fi
fi

echo ""
echo -e "${CYAN}🔄 CE365 Docker Update${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Prüfe ob Compose-File existiert
if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Compose-File nicht gefunden: $COMPOSE_FILE"
    exit 1
fi

# ─── Phase 1: Aktuelle Images sichern ───
log_info "Speichere aktuelle Image-Tags..."

API_IMAGE=$($DOCKER_CMD inspect ce365-api --format '{{.Config.Image}}' 2>/dev/null || echo "")
WEB_IMAGE=$($DOCKER_CMD inspect ce365-web --format '{{.Config.Image}}' 2>/dev/null || echo "")

if [ -z "$API_IMAGE" ] && [ -z "$WEB_IMAGE" ]; then
    log_warn "Keine laufenden CE365-Container gefunden (Erst-Installation?)"
fi

# Backup speichern
cat > "$BACKUP_FILE" <<EOF
API_IMAGE=${API_IMAGE}
WEB_IMAGE=${WEB_IMAGE}
TIMESTAMP=$(date -Iseconds)
EOF

log_ok "Image-Backup: API=${API_IMAGE:-none}, Web=${WEB_IMAGE:-none}"

# ─── Phase 2: Neue Images pullen ───
log_info "Lade neue Images..."

if ! $COMPOSE_CMD -f "$COMPOSE_FILE" pull api web 2>&1; then
    log_error "Image-Pull fehlgeschlagen"
    exit 1
fi

log_ok "Neue Images geladen"

# ─── Phase 3: Container neu starten ───
log_info "Starte Container neu..."

$COMPOSE_CMD -f "$COMPOSE_FILE" up -d --remove-orphans 2>&1

log_ok "Container gestartet"

# ─── Phase 4: Health-Check ───
log_info "Warte auf Health-Check (max ${HEALTH_TIMEOUT}s)..."

elapsed=0
healthy=false

while [ $elapsed -lt $HEALTH_TIMEOUT ]; do
    # API Health-Check
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        healthy=true
        break
    fi

    # Auch über nginx probieren
    if curl -sf "$HEALTH_ENDPOINT" >/dev/null 2>&1; then
        healthy=true
        break
    fi

    sleep $HEALTH_INTERVAL
    elapsed=$((elapsed + HEALTH_INTERVAL))
    echo -n "."
done
echo ""

# ─── Phase 5: Ergebnis ───
if [ "$healthy" = true ]; then
    log_ok "Health-Check bestanden nach ${elapsed}s"
    echo ""
    echo -e "${GREEN}✅ Update erfolgreich!${NC}"
    echo ""

    # Alte Images aufräumen
    log_info "Räume alte Images auf..."
    $DOCKER_CMD image prune -f >/dev/null 2>&1 || true
    log_ok "Cleanup abgeschlossen"
else
    log_error "Health-Check fehlgeschlagen nach ${HEALTH_TIMEOUT}s"
    echo ""
    echo -e "${RED}❌ Rollback wird durchgeführt...${NC}"
    echo ""

    # Rollback
    if [ -f "$BACKUP_FILE" ]; then
        source "$BACKUP_FILE"

        if [ -n "$API_IMAGE" ] || [ -n "$WEB_IMAGE" ]; then
            log_info "Stoppe fehlerhaften Container..."
            $COMPOSE_CMD -f "$COMPOSE_FILE" down 2>&1

            # Alte Images taggen (falls nötig)
            log_info "Stelle vorherige Version wieder her..."
            $COMPOSE_CMD -f "$COMPOSE_FILE" up -d 2>&1

            # Erneuter Health-Check
            sleep 10
            if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
                log_ok "Rollback erfolgreich - System läuft wieder"
            else
                log_error "Rollback-Health-Check fehlgeschlagen!"
                log_error "Manuelle Intervention erforderlich"
                exit 2
            fi
        else
            log_error "Keine Backup-Images vorhanden, Rollback nicht möglich"
            exit 2
        fi
    else
        log_error "Backup-Datei nicht gefunden"
        exit 2
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
