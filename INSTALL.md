# CE365 Agent - Installationsanleitung

## Inhaltsverzeichnis

- [Voraussetzungen](#voraussetzungen)
- [Option A: Lokale Installation (CLI)](#option-a-lokale-installation-cli)
- [Option B: Docker-Installation (Server/Team)](#option-b-docker-installation-serverteam)
- [Editionen](#editionen)
- [Konfiguration](#konfiguration)
- [Erster Start](#erster-start)
- [CLI-Befehle](#cli-befehle)
- [Updates & Wartung](#updates--wartung)
- [Deinstallation](#deinstallation)
- [Fehlerbehebung](#fehlerbehebung)

---

## Voraussetzungen

### Lokale Installation (CLI)

| Voraussetzung | Version |
|---|---|
| Python | >= 3.9 |
| pip | aktuell |
| Betriebssystem | macOS oder Windows |
| Anthropic API Key | [console.anthropic.com](https://console.anthropic.com) |

### Docker-Installation (Server/Team)

| Voraussetzung | Version |
|---|---|
| Docker | >= 20.10 |
| Docker Compose | >= 2.0 |
| Anthropic API Key | [console.anthropic.com](https://console.anthropic.com) |

---

## Option A: Lokale Installation (CLI)

### 1. Repository klonen

```bash
git clone https://github.com/yourusername/ce365-agent.git
cd ce365-agent
```

### 2. Virtual Environment erstellen

```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# oder
venv\Scripts\activate      # Windows
```

### 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

**Hinweis:** Die PII-Detection (Presidio + spaCy) benötigt ein Sprachmodell:

```bash
python -m spacy download de_core_news_sm
```

### 4. Konfiguration

Beim ersten Start führt ein **Setup-Wizard** durch die Konfiguration. Alternativ manuell:

```bash
cp .env.example .env
```

`.env` bearbeiten und mindestens den API-Key setzen:

```env
ANTHROPIC_API_KEY=sk-ant-dein-key-hier
EDITION=free
```

### 5. Starten

```bash
python -m ce365
```

Der Setup-Wizard fragt beim ersten Start nach:
1. Name & Firma
2. Edition (Free / Pro / Business)
3. Anthropic API Key
4. Lizenzschlüssel (nur Pro/Business)
5. Netzwerk-Konfiguration (nur Business)
6. Datenbank (nur Business)
7. Techniker-Passwort (optional)

### 6. Health-Check

```bash
python -m ce365 --health
```

Prüft Python-Version, Dependencies, API-Verbindung und Konfiguration.

---

## Option B: Docker-Installation (Server/Team)

### Interaktiver Installer (empfohlen)

```bash
curl -O https://raw.githubusercontent.com/yourusername/ce365-agent/main/install.sh
chmod +x install.sh
./install.sh
```

Der Installer führt durch:
1. Editions-Auswahl & Lizenzschlüssel
2. Netzwerkzugriff (Cloudflare / Tailscale / VPN / Lokal)
3. Anthropic API Key
4. Datenbank-Setup (Business)
5. Docker-Stack starten

### Manuelle Docker-Installation

```bash
# 1. Repository klonen
git clone https://github.com/yourusername/ce365-agent.git
cd ce365-agent

# 2. .env erstellen
cp .env.docker.example .env

# 3. .env bearbeiten (mindestens diese Werte setzen):
#    - ANTHROPIC_API_KEY
#    - EDITION (free/pro/business)
#    - POSTGRES_PASSWORD (sicher generieren!)
#    - REDIS_PASSWORD (sicher generieren!)
#    - SECRET_KEY (sicher generieren!)
#    - JWT_SECRET (sicher generieren!)

# 4. Sichere Passwörter generieren
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)
export SECRET_KEY=$(openssl rand -base64 32)
export JWT_SECRET=$(openssl rand -base64 32)

# 5. Docker-Stack starten
docker compose up -d
```

### Docker-Container

| Container | Beschreibung | Port |
|---|---|---|
| `ce365-api` | FastAPI Backend | intern 8000 |
| `ce365-web` | Next.js Frontend | intern 3000 |
| `ce365-nginx` | Reverse Proxy | 80 / 443 |
| `ce365-postgres` | PostgreSQL Datenbank | intern 5432 |
| `ce365-redis` | Redis Cache | intern 6379 |

Optionale Container (via `COMPOSE_PROFILES`):
- `cloudflare` - Cloudflare Tunnel
- `tailscale` - Tailscale VPN
- `autoupdate` - Watchtower Auto-Updates

### Netzwerk-Optionen

```bash
# Cloudflare Tunnel
COMPOSE_PROFILES=cloudflare docker compose up -d

# Tailscale VPN
COMPOSE_PROFILES=tailscale docker compose up -d

# Auto-Updates aktivieren
COMPOSE_PROFILES=autoupdate docker compose up -d

# Kombiniert
COMPOSE_PROFILES=cloudflare,autoupdate docker compose up -d
```

---

## Editionen (per-Seat / pro Techniker)

| | **Free** (0 EUR) | **Pro** (49 EUR/Seat/Mo) | **Business** (99 EUR/Seat/Mo) |
|---|---|---|---|
| Basis-Diagnose (7 Tools) + AI | ✅ | ✅ | ✅ |
| Basis-Remediation (3 Tools) | 5 Runs/Monat | Unbegrenzt | Unbegrenzt |
| Erweiterte Audit & Repair | - | ✅ | ✅ |
| Web-Suche & Root-Cause-Analyse | - | ✅ | ✅ |
| Aktive Systeme / 30 Tage | Unbegrenzt | 10 | Unbegrenzt |
| Gleichzeitige Sessions | 1 | 1 | 1 pro Seat |
| Monitoring-Sensor | - | - | ✅ |
| Team (Policies, Runbooks, Shared Learning) | - | - | ✅ |
| Kommerzielle Nutzung | - | ✅ | ✅ |
| Lizenzschlüssel | Nicht nötig | Erforderlich | Erforderlich |

Siehe [EDITION_FEATURES.md](EDITION_FEATURES.md) für die vollständige Feature-Matrix.

---

## Konfiguration

### Umgebungsvariablen (.env)

#### Pflicht

| Variable | Beschreibung | Beispiel |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API Key | `sk-ant-...` |
| `EDITION` | Edition | `free`, `pro`, `business` |

#### Pro / Business

| Variable | Beschreibung | Beispiel |
|---|---|---|
| `LICENSE_KEY` | Lizenzschlüssel | `CE365-PRO-...` |
| `BACKEND_URL` | Backend-URL | `https://ce365.firma.de` |
| `NETWORK_METHOD` | Verbindungsart | `cloudflare`, `tailscale`, `vpn`, `direct` |

#### Business (Shared Learning)

| Variable | Beschreibung | Beispiel |
|---|---|---|
| `LEARNING_DB_TYPE` | Datenbank-Typ | `sqlite`, `postgresql`, `mysql` |
| `LEARNING_DB_URL` | Datenbank-URL | `postgresql://user:pass@host:5432/db` |

#### Optional

| Variable | Beschreibung | Standard |
|---|---|---|
| `CLAUDE_MODEL` | Claude-Modell | `claude-sonnet-4-5-20250929` |
| `LOG_LEVEL` | Log-Level | `INFO` |
| `PII_DETECTION_ENABLED` | PII-Erkennung | `true` |
| `PII_DETECTION_LEVEL` | PII-Level | `high` |
| `WEB_SEARCH_ENABLED` | Web-Suche | `true` |
| `TECHNICIAN_PASSWORD_HASH` | Passwort (bcrypt) | leer |
| `SESSION_TIMEOUT` | Session-Timeout (Sek.) | `3600` |

### Shared Learning Datenbank (Business)

Für Team-Learning kann eine separate PostgreSQL-Datenbank gestartet werden:

```bash
docker compose -f docker-compose.learning-db.yml up -d
```

Zugehörige `.env`-Einträge:

```env
LEARNING_DB_TYPE=postgresql
LEARNING_DB_URL=postgresql://ce365:password@localhost:5432/ce365_learning
```

pgAdmin ist unter `http://localhost:5050` erreichbar.

---

## Erster Start

### CLI-Modus

```bash
source venv/bin/activate
python -m ce365
```

CE365 führt beim Start automatisch einen System-Statusbericht aus:
- System-Info (OS, CPU, RAM, Disk)
- Backup-Status
- Security-Status (Firewall, Antivirus)

Danach kannst du Probleme beschreiben, z.B.:
```
💬 Wie kann ich dir helfen?
> Mein Windows 11 PC ist langsam geworden
```

### Workflow

```
Audit → Analyse → Plan → GO REPAIR: 1,2,3 → Ausführung → Fertig
```

1. CE365 analysiert das System automatisch
2. Erstellt einen Reparatur-Plan mit nummerierten Schritten
3. Du gibst Schritte frei mit `GO REPAIR: 1,2,3` oder `GO REPAIR: 1-3`
4. CE365 führt nur die freigegebenen Schritte aus

---

## CLI-Befehle

| Befehl | Beschreibung |
|---|---|
| `python -m ce365` | Bot starten |
| `python -m ce365 --health` | Health-Check |
| `python -m ce365 --version` | Version anzeigen |
| `python -m ce365 --set-password` | Techniker-Passwort setzen |
| `python -m ce365 --update` | Auf neueste Version aktualisieren |
| `python -m ce365 --rollback` | Zur letzten Version zurückkehren |
| `python -m ce365 --uninstall` | Deinstallation (löscht Daten) |

### Im Bot

| Eingabe | Beschreibung |
|---|---|
| `stats` | Learning-Statistiken anzeigen |
| `GO REPAIR: 1,2,3` | Reparatur-Schritte freigeben |
| `exit` / `quit` / `q` | Bot beenden |

---

## Updates & Wartung

### CLI (pip)

```bash
source venv/bin/activate
python -m ce365 --update
```

Oder manuell:

```bash
git pull
pip install -r requirements.txt
```

### Docker

```bash
docker compose pull
docker compose up -d
```

Mit Watchtower (automatisch, täglich):

```bash
COMPOSE_PROFILES=autoupdate docker compose up -d
```

### Rollback

```bash
python -m ce365 --rollback
```

---

## Deinstallation

### CLI

```bash
python -m ce365 --uninstall
```

Löscht:
- `.env` (Konfiguration)
- `data/` (Sessions, Changelogs, Cases)
- `~/.ce365/` (User-Config, Cache)

Danach optional:

```bash
pip uninstall ce365
deactivate
rm -rf venv
```

### Docker

```bash
docker compose down -v   # Container + Volumes löschen
rm -rf .env nginx/
```

---

## Fehlerbehebung

### API Key funktioniert nicht

```
❌ API Key Test fehlgeschlagen
```

- Prüfe ob Key mit `sk-ant-` beginnt
- Prüfe auf [console.anthropic.com](https://console.anthropic.com) ob Key aktiv ist
- Prüfe Guthaben/Credits

### PII Detection nicht verfügbar

```
⚠️ PII Detection nicht verfügbar
```

```bash
pip install presidio-analyzer presidio-anonymizer
python -m spacy download de_core_news_sm
```

### Lizenz ungültig

```
❌ Ungültige Lizenz
```

- Prüfe ob Key mit `CE365-` beginnt
- Prüfe ob `BACKEND_URL` erreichbar ist
- Offline-Cache ist 24h gültig, danach muss Online-Validierung erfolgen

### Docker-Container starten nicht

```bash
# Logs prüfen
docker compose logs api
docker compose logs postgres

# Neustart
docker compose down
docker compose up -d
```

### Tests ausführen

```bash
source venv/bin/activate
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

**Version:** 1.0.0 | **Stand:** Februar 2026
