#!/bin/bash
#
# TechCare Bot - Interaktiver Docker Installer
# Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
#

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Header
clear
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║               🔧  TechCare Bot Installer                  ║"
echo "║                                                            ║"
echo "║         AI-powered IT-Wartungsassistent                    ║"
echo "║         Docker-basierte Team-Lösung                        ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Prüfe ob Docker installiert ist
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker ist nicht installiert!${NC}"
    echo ""
    echo "Bitte installiere Docker:"
    echo "  macOS/Windows: https://www.docker.com/products/docker-desktop"
    echo "  Linux: https://docs.docker.com/engine/install/"
    echo ""
    exit 1
fi

# Prüfe ob Docker Compose installiert ist
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose ist nicht installiert!${NC}"
    echo ""
    echo "Bitte installiere Docker Compose:"
    echo "  https://docs.docker.com/compose/install/"
    echo ""
    exit 1
fi

# Docker Compose Command ermitteln
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo -e "${GREEN}✓ Docker und Docker Compose gefunden${NC}"
echo ""

# .env Datei vorbereiten
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  .env Datei existiert bereits${NC}"
    read -p "Überschreiben? (j/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Jj]$ ]]; then
        echo "Installation abgebrochen."
        exit 0
    fi
fi

# 1. LIZENZSCHLÜSSEL
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}1. LIZENZSCHLÜSSEL${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "TechCare Editionen:"
echo "  • Free (kostenlos) - Basis-Tools, 5 Reparaturen/Monat"
echo "  • Pro (€49/Monat) - alle Tools, 1 System"
echo "  • Business (€99/Monat) - ∞ Systeme, Monitoring, Team-Learning"
echo ""
read -p "Lizenzschlüssel (leer für Free): " LICENSE_KEY
echo ""

if [ -z "$LICENSE_KEY" ]; then
    EDITION="free"
    echo -e "${GREEN}✓ Free Edition aktiviert${NC}"
else
    EDITION="pro"  # Wird vom License Server validiert
    echo -e "${GREEN}✓ Lizenz wird beim Start validiert${NC}"
fi
echo ""

# 2. NETZWERKZUGRIFF
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}2. NETZWERKZUGRIFF KONFIGURIEREN${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Wie möchten Sie auf TechCare zugreifen?"
echo ""
echo "  1) Cloudflare Tunnel (empfohlen)"
echo "     → Kein VPN nötig, automatisches SSL, Zero Trust"
echo "     → Sicher von überall zugreifen"
echo ""
echo "  2) Tailscale Mesh VPN"
echo "     → Peer-to-peer Verbindung, keine öffentliche IP"
echo "     → Einfaches Setup, verschlüsselt"
echo ""
echo "  3) Vorhandenes VPN nutzen"
echo "     → Nutzen Sie Ihr WireGuard/OpenVPN/Cisco VPN"
echo "     → Keine zusätzliche Software nötig"
echo ""
echo "  4) Nur lokal (localhost)"
echo "     → Kein Fernzugriff, nur am Server"
echo "     → Für Tests oder Einzelplatz"
echo ""
read -p "Ihre Wahl (1-4): " NETWORK_CHOICE
echo ""

COMPOSE_PROFILES=""
CLOUDFLARE_TUNNEL_TOKEN=""
TAILSCALE_AUTH_KEY=""
TAILSCALE_HOSTNAME=""
API_URL=""

case $NETWORK_CHOICE in
    1)
        echo -e "${BLUE}Cloudflare Tunnel Setup${NC}"
        echo ""
        echo "1. Gehe zu: https://one.dash.cloudflare.com/"
        echo "2. Navigiere zu: Zero Trust → Networks → Tunnels"
        echo "3. Erstelle neuen Tunnel und kopiere das Token"
        echo ""
        read -p "Cloudflare Tunnel Token: " CLOUDFLARE_TUNNEL_TOKEN
        read -p "Ihre Cloudflare Domain (z.B. techcare.ihrefirma.de): " DOMAIN
        COMPOSE_PROFILES="cloudflare"
        API_URL="https://${DOMAIN}"
        echo ""
        echo -e "${GREEN}✓ Cloudflare Tunnel wird konfiguriert${NC}"
        echo -e "${YELLOW}ℹ️  Nach dem Start: Tunnel in Cloudflare Dashboard mit Domain verknüpfen${NC}"
        ;;
    2)
        echo -e "${BLUE}Tailscale Setup${NC}"
        echo ""
        echo "1. Gehe zu: https://login.tailscale.com/admin/settings/keys"
        echo "2. Erstelle einen neuen Auth Key (einmalig verwendbar)"
        echo ""
        read -p "Tailscale Auth Key: " TAILSCALE_AUTH_KEY
        read -p "Hostname für Tailscale (z.B. techcare): " TAILSCALE_HOSTNAME
        COMPOSE_PROFILES="tailscale"
        API_URL="http://${TAILSCALE_HOSTNAME}:80"
        echo ""
        echo -e "${GREEN}✓ Tailscale wird konfiguriert${NC}"
        echo -e "${YELLOW}ℹ️  Nach dem Start: Verbinden Sie sich über http://${TAILSCALE_HOSTNAME}${NC}"
        ;;
    3)
        echo -e "${BLUE}Vorhandenes VPN${NC}"
        echo ""
        read -p "Interne IP-Adresse dieses Servers: " SERVER_IP
        API_URL="http://${SERVER_IP}:80"
        echo ""
        echo -e "${GREEN}✓ Konfiguriert für VPN-Zugriff${NC}"
        echo -e "${YELLOW}ℹ️  Zugriff über VPN: http://${SERVER_IP}${NC}"
        ;;
    4)
        echo -e "${BLUE}Nur lokaler Zugriff${NC}"
        API_URL="http://localhost:80"
        echo ""
        echo -e "${GREEN}✓ Konfiguriert für localhost${NC}"
        echo -e "${YELLOW}ℹ️  Zugriff: http://localhost${NC}"
        ;;
    *)
        echo -e "${RED}Ungültige Auswahl${NC}"
        exit 1
        ;;
esac
echo ""

# 3. ANTHROPIC API KEY
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}3. ANTHROPIC API KONFIGURATION${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "TechCare nutzt Claude AI für intelligente Diagnose."
echo "Erstellen Sie einen API Key: https://console.anthropic.com"
echo ""
read -p "Anthropic API Key: " ANTHROPIC_API_KEY
echo ""

if [[ ! $ANTHROPIC_API_KEY =~ ^sk-ant- ]]; then
    echo -e "${YELLOW}⚠️  Warnung: API Key hat ungewöhnliches Format${NC}"
    echo ""
fi

# 4. DATENBANK (nur Enterprise/Pro Business)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

if [ "$EDITION" == "business" ]; then
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}4. SHARED LEARNING DATENBANK${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Shared Learning ermöglicht Team-Wissensaustausch."
    echo "Die PostgreSQL Datenbank wird automatisch erstellt."
    echo ""
    read -p "Datenbank Name (Standard: techcare): " POSTGRES_DB
    POSTGRES_DB=${POSTGRES_DB:-techcare}
    read -p "Datenbank User (Standard: techcare): " POSTGRES_USER
    POSTGRES_USER=${POSTGRES_USER:-techcare}
    echo ""
    echo -e "${GREEN}✓ Datenbank wird beim Start initialisiert${NC}"
    echo -e "${YELLOW}ℹ️  Passwort: ${POSTGRES_PASSWORD}${NC}"
    echo ""
fi

# 5. SICHERHEIT
SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 32)

# 6. AUTO-UPDATE
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}5. AUTOMATISCHE UPDATES${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
read -p "Automatische Updates aktivieren? (j/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    COMPOSE_PROFILES="${COMPOSE_PROFILES},autoupdate"
    echo -e "${GREEN}✓ Auto-Update aktiviert (täglich)${NC}"
else
    echo -e "${YELLOW}ℹ️  Manuelle Updates: docker-compose pull && docker-compose up -d${NC}"
fi
echo ""

# .env Datei schreiben
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}KONFIGURATION WIRD ERSTELLT...${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

cat > $ENV_FILE <<EOF
# ============================================================================
# TechCare Bot - Docker Deployment Konfiguration
# ============================================================================
# Erstellt: $(date)
# Installer Version: 1.0.0
# ============================================================================

# EDITION & LICENSE
EDITION=${EDITION}
LICENSE_KEY=${LICENSE_KEY}
LICENSE_SERVER_URL=https://license.techcare.local

# DOCKER REGISTRY
DOCKER_REGISTRY=registry.techcare.local
DOCKER_REGISTRY_USER=${LICENSE_KEY}
DOCKER_REGISTRY_PASSWORD=${LICENSE_KEY}
VERSION=latest

# NETWORK
API_URL=${API_URL}
HTTP_PORT=80
HTTPS_PORT=443

# CLOUDFLARE TUNNEL (Optional)
CLOUDFLARE_TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}

# TAILSCALE (Optional)
TAILSCALE_AUTH_KEY=${TAILSCALE_AUTH_KEY}
TAILSCALE_HOSTNAME=${TAILSCALE_HOSTNAME}

# ANTHROPIC API
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# DATABASE
POSTGRES_DB=${POSTGRES_DB:-techcare}
POSTGRES_USER=${POSTGRES_USER:-techcare}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# REDIS
REDIS_PASSWORD=${REDIS_PASSWORD}

# SECURITY
SECRET_KEY=${SECRET_KEY}
JWT_SECRET=${JWT_SECRET}

# OPTIONAL FEATURES
PII_DETECTION_ENABLED=true
WEB_SEARCH_ENABLED=true

# LOGGING
LOG_LEVEL=INFO

# WATCHTOWER (Auto-Update)
WATCHTOWER_NOTIFICATIONS=

# DOCKER COMPOSE PROFILES
COMPOSE_PROFILES=${COMPOSE_PROFILES}
EOF

chmod 600 $ENV_FILE
echo -e "${GREEN}✓ .env Datei erstellt und geschützt (chmod 600)${NC}"
echo ""

# Nginx Konfiguration erstellen
mkdir -p nginx/ssl
cat > nginx/nginx.conf <<'NGINX_EOF'
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=web_limit:10m rate=30r/s;

    upstream api_backend {
        server api:8000;
    }

    upstream web_backend {
        server web:3000;
    }

    server {
        listen 80;
        server_name _;

        client_max_body_size 100M;

        # Health Check Endpoint
        location /health {
            access_log off;
            return 200 "OK\n";
            add_header Content-Type text/plain;
        }

        # API Backend
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;

            proxy_pass http://api_backend/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # Frontend
        location / {
            limit_req zone=web_limit burst=50 nodelay;

            proxy_pass http://web_backend/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
NGINX_EOF

echo -e "${GREEN}✓ Nginx Konfiguration erstellt${NC}"
echo ""

# Docker Login (falls Private Registry)
if [ ! -z "$LICENSE_KEY" ]; then
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}DOCKER REGISTRY LOGIN${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Verbinde mit TechCare Registry..."
    echo ""

    if echo "${LICENSE_KEY}" | docker login registry.techcare.local -u "${LICENSE_KEY}" --password-stdin 2>/dev/null; then
        echo -e "${GREEN}✓ Registry Login erfolgreich${NC}"
    else
        echo -e "${YELLOW}⚠️  Registry Login fehlgeschlagen - Images werden später heruntergeladen${NC}"
    fi
    echo ""
fi

# Docker Images pullen
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}DOCKER IMAGES WERDEN HERUNTERGELADEN...${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

if [ ! -z "$COMPOSE_PROFILES" ]; then
    export COMPOSE_PROFILES="${COMPOSE_PROFILES}"
fi

$DOCKER_COMPOSE pull || {
    echo -e "${YELLOW}⚠️  Einige Images konnten nicht heruntergeladen werden${NC}"
    echo -e "${YELLOW}   TechCare wird trotzdem versuchen zu starten${NC}"
    echo ""
}

# Docker Stack starten
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}TECHCARE WIRD GESTARTET...${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

$DOCKER_COMPOSE up -d

echo ""
echo -e "${GREEN}✅ INSTALLATION ABGESCHLOSSEN!${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}ZUGRIFFSINFORMATIONEN${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Zugriffs-URL: ${GREEN}${API_URL}${NC}"
echo ""
echo "  Edition: ${EDITION}"
echo ""

case $NETWORK_CHOICE in
    1)
        echo -e "${YELLOW}WICHTIG: Cloudflare Tunnel Konfiguration${NC}"
        echo ""
        echo "1. Gehe zu: https://one.dash.cloudflare.com/"
        echo "2. Navigiere zu: Zero Trust → Networks → Tunnels"
        echo "3. Wähle deinen Tunnel aus"
        echo "4. Füge Public Hostname hinzu:"
        echo "   • Domain: ${DOMAIN}"
        echo "   • Service: http://nginx:80"
        echo ""
        ;;
    2)
        echo -e "${YELLOW}WICHTIG: Tailscale${NC}"
        echo ""
        echo "Nach dem ersten Start erscheint TechCare in Ihrem Tailscale Admin Panel."
        echo "Verbinden Sie sich über: ${API_URL}"
        echo ""
        ;;
esac

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}NÜTZLICHE BEFEHLE${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Status prüfen:    $DOCKER_COMPOSE ps"
echo "  Logs anzeigen:    $DOCKER_COMPOSE logs -f"
echo "  Stoppen:          $DOCKER_COMPOSE stop"
echo "  Starten:          $DOCKER_COMPOSE start"
echo "  Neustarten:       $DOCKER_COMPOSE restart"
echo "  Herunterfahren:   $DOCKER_COMPOSE down"
echo "  Updates:          $DOCKER_COMPOSE pull && $DOCKER_COMPOSE up -d"
echo ""
echo -e "${GREEN}Viel Erfolg mit TechCare Bot! 🔧${NC}"
echo ""
