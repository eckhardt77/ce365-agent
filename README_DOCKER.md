# CE365 Agent - Docker Deployment

> 🔧 AI-powered IT-Wartungsassistent für Windows & macOS
>
> **Docker-basierte Team-Lösung** mit flexiblen Netzwerkoptionen

## Quick Start

```bash
# 1. Repository klonen
git clone https://github.com/your-repo/ce365-agent.git
cd ce365-agent

# 2. Installer ausführen
bash install.sh

# 3. Fertig! 🎉
```

Der Installer führt dich durch die komplette Konfiguration in **5-10 Minuten**.

## Netzwerkzugriff-Optionen

CE365 bietet **4 Deployment-Methoden**:

### 1. Cloudflare Tunnel (Empfohlen) ⭐

```
✅ Kein VPN nötig
✅ Automatisches SSL
✅ Zero Trust Security
✅ DDoS Protection
✅ €0/Monat (Free Tier)
```

**Setup**: 10 Minuten | **Komplexität**: ⭐⭐☆☆☆

📖 **[Vollständiger Guide →](docs/DEPLOYMENT_CLOUDFLARE.md)**

---

### 2. Tailscale Mesh VPN

```
✅ Peer-to-Peer Verschlüsselung
✅ Schnellste Performance
✅ Mobile-freundlich
✅ WireGuard-basiert
✅ €0/Monat (Personal Tier)
```

**Setup**: 5 Minuten | **Komplexität**: ⭐☆☆☆☆

📖 **[Vollständiger Guide →](docs/DEPLOYMENT_TAILSCALE.md)**

---

### 3. Vorhandenes VPN nutzen

```
✅ Nutzt bestehendes VPN
✅ On-Premise
✅ Compliance-ready
✅ Keine Cloud-Abhängigkeit
✅ €0 (VPN vorhanden)
```

**Setup**: 30-60 Minuten | **Komplexität**: ⭐⭐⭐⭐☆

📖 **[Vollständiger Guide →](docs/DEPLOYMENT_VPN.md)**

---

### 4. Nur Lokal (Tests/Demo)

```
✅ Einfachstes Setup
✅ Kein Fernzugriff nötig
✅ Ideal für Tests
✅ €0
```

**Setup**: 5 Minuten | **Komplexität**: ⭐☆☆☆☆

---

## Welche Option ist die richtige?

| Ich möchte... | Empfehlung |
|--------------|------------|
| **Schnellstes Setup** | → Tailscale |
| **Automatisches SSL** | → Cloudflare |
| **On-Premise bleiben** | → VPN |
| **Nur testen** | → Lokal |
| **Beste mobile Experience** | → Cloudflare |
| **Schnellste Performance** | → Tailscale |

📖 **[Detaillierter Vergleich →](docs/DEPLOYMENT_OVERVIEW.md)**

## Systemanforderungen

### Server (wo Docker läuft)

**Minimum:**
- CPU: 2 Cores
- RAM: 4 GB
- Disk: 20 GB
- OS: Linux, macOS, Windows Server

**Empfohlen:**
- CPU: 4 Cores
- RAM: 8 GB
- Disk: 50 GB SSD
- OS: Ubuntu 22.04 LTS

### Unterstützte Plattformen

✅ Linux (Ubuntu, Debian, CentOS, RHEL, Fedora, etc.)
✅ macOS 11+ (Intel & Apple Silicon)
✅ Windows 10/11 + WSL2
✅ Windows Server 2019+
✅ Synology NAS (x86)
✅ QNAP NAS (x86)
✅ Raspberry Pi 4 (4GB+)

## Architektur

```
┌─────────────────────────────────────────┐
│         CE365 Docker Stack           │
├─────────────────────────────────────────┤
│                                         │
│  Web (Next.js) → Nginx → Cloudflared   │
│       ↓                                 │
│  API (FastAPI) → PostgreSQL             │
│       ↓                                 │
│  Redis (Cache)                          │
│                                         │
│  Optional: Tailscale, Watchtower        │
│                                         │
└─────────────────────────────────────────┘
```

**Services:**
- `web` - Next.js Frontend
- `api` - FastAPI Backend
- `postgres` - Shared Learning Database
- `redis` - Session & Cache
- `nginx` - Reverse Proxy
- `cloudflared` - Cloudflare Tunnel (optional)
- `tailscale` - Mesh VPN (optional)
- `watchtower` - Auto-Updates (optional)

## Installation

### Methode 1: Interaktiver Installer (Empfohlen)

```bash
bash install.sh
```

Beantworte die Fragen:
1. Lizenzschlüssel (oder leer für Community)
2. Netzwerkzugriff (1-4)
3. Spezifische Konfiguration
4. Anthropic API Key
5. Auto-Updates (ja/nein)

### Methode 2: Manuelle Konfiguration

```bash
# 1. .env Datei erstellen
cp .env.docker.example .env
nano .env  # Werte ausfüllen

# 2. Docker Stack starten
docker-compose up -d

# 3. Logs prüfen
docker-compose logs -f
```

## Verwaltung

### Status prüfen

```bash
docker-compose ps
```

### Logs anzeigen

```bash
# Alle Logs (live)
docker-compose logs -f

# Nur API
docker-compose logs -f api

# Letzte 100 Zeilen
docker-compose logs --tail=100
```

### Stoppen & Starten

```bash
# Stoppen
docker-compose stop

# Starten
docker-compose start

# Neu starten
docker-compose restart

# Herunterfahren (Container löschen)
docker-compose down
```

### Updates

```bash
# Automatisch (wenn aktiviert)
# Watchtower prüft täglich

# Manuell
docker-compose pull
docker-compose up -d
```

### Backup

```bash
# Datenbank Backup
docker-compose exec postgres pg_dump -U ce365 ce365 > backup.sql

# Restore
cat backup.sql | docker-compose exec -T postgres psql -U ce365 ce365
```

## Editionen & Preise

| Edition | Preis | Features |
|---------|-------|----------|
| **Community** | €0 | Max 10 Reparaturen/Monat, lokale DB |
| **Pro** | €49/Monat | Unbegrenzt, 1 System, PostgreSQL |
| **Pro Business** | €99/Monat | Unbegrenzt, ∞ Systeme, Shared Learning |
| **Enterprise** | ab €149/Seat | Team, zentrale Wissensdatenbank, SLA |

**Volumenrabatte (Enterprise):**
- 6-9 Lizenzen: €139/Seat
- 10-24 Lizenzen: €129/Seat
- 25+ Lizenzen: €119/Seat

📖 **[Detaillierter Vergleich →](docs/EDITION_VERGLEICH.md)**

## Sicherheit

### Best Practices

✅ **Starke Passwörter** - Installer generiert automatisch
✅ **Rate Limiting** - Nginx limitiert Requests
✅ **Auto-Updates** - Security Patches automatisch
✅ **Encrypted Secrets** - API Keys verschlüsselt
✅ **Audit Logs** - Alle Aktionen geloggt

### Compliance

- ✅ DSGVO-konform (EU)
- ✅ HIPAA-ready (Healthcare)
- ✅ ISO 27001-kompatibel

## Troubleshooting

### Service läuft nicht

```bash
# Status prüfen
docker-compose ps

# Logs prüfen
docker-compose logs api

# Neu starten
docker-compose restart api
```

### "Connection refused"

```bash
# Prüfe ob Port offen
curl http://localhost/health

# Prüfe Firewall
sudo ufw status

# Prüfe Container Network
docker network inspect ce365-agent_ce365-external
```

### Datenbank-Fehler

```bash
# PostgreSQL Logs
docker-compose logs postgres

# In Container Shell
docker-compose exec postgres psql -U ce365

# Datenbank neu initialisieren (⚠️ DATEN GEHEN VERLOREN!)
docker-compose down -v
docker-compose up -d
```

### Performance-Probleme

```bash
# Resource Usage prüfen
docker stats

# Logs nach Fehlern durchsuchen
docker-compose logs | grep ERROR

# Container neu starten
docker-compose restart
```

## Migration von CLI

Falls du bereits die CLI-Version nutzt:

```bash
# 1. CLI-Daten exportieren
cp ~/.ce365/data/cases.db ~/backup/

# 2. Docker installieren
bash install.sh

# 3. Daten importieren (Script in Entwicklung)
python3 tools/migrate_cli_to_docker.py ~/backup/cases.db
```

## Entwicklung

### Lokales Development Setup

```bash
# API (Backend)
cd api/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Web (Frontend)
cd web/
npm install
npm run dev
```

### Docker Images bauen

```bash
# API Image
docker build -t ce365-api:dev -f Dockerfile.api .

# Web Image
docker build -t ce365-web:dev -f Dockerfile.web .

# Mit Custom Images starten
DOCKER_REGISTRY= VERSION=dev docker-compose up -d
```

## Support & Community

### Dokumentation

- 📖 [Deployment Übersicht](docs/DEPLOYMENT_OVERVIEW.md)
- 📖 [Cloudflare Guide](docs/DEPLOYMENT_CLOUDFLARE.md)
- 📖 [Tailscale Guide](docs/DEPLOYMENT_TAILSCALE.md)
- 📖 [VPN Guide](docs/DEPLOYMENT_VPN.md)
- 📖 [Edition Vergleich](docs/EDITION_VERGLEICH.md)

### Community

- 💬 **GitHub Issues**: https://github.com/your-repo/ce365-agent/issues
- 📧 **Email**: support@ce365.local
- 📚 **Docs**: https://docs.ce365.local
- 💡 **Feature Requests**: https://feedback.ce365.local

### Enterprise Support

Für Enterprise-Kunden:
- 🚨 24/7 Priority Support
- 📞 Telefon Hotline
- 👨‍💼 Dedicated Account Manager
- 🎓 Onboarding & Training

## Lizenz

CE365 Agent ist proprietäre Software.

- **Community Edition**: Kostenlos für max 10 Reparaturen/Monat
- **Paid Editions**: Kommerzielle Lizenzen erforderlich

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing

---

**Viel Erfolg mit CE365 Agent! 🔧**

*Made with ❤️ in Germany*
