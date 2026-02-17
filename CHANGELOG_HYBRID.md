# TechCare Bot - Changelog (Hybrid Architecture Update)

## Version 2.0.0 - Hybrid Architecture (2026-02-17)

### 🎯 Hauptänderungen

**Architektur-Shift:** Von reinem CLI-Tool zu **Hybrid Architecture**
- CLI läuft lokal auf Kunden-PC (voller System-Zugriff)
- Zentrale Docker-Services (PostgreSQL, License Server, Redis)
- Netzwerkverbindung via VPN/Cloudflare/Tailscale

---

### ✨ Neue Features

#### 1. **Techniker-Passwort-Schutz** 🔐

**Zweck:** Schützt TechCare vor unbefugtem Zugriff durch Kunden

**Features:**
- Passwort-Eingabe beim Start (3 Versuche)
- bcrypt-Hash-Speicherung (nicht Klartext)
- Session-Timeout konfigurierbar
- Passwort-Änderung via `techcare --set-password`

**Dateien:**
- `techcare/__main__.py`: `verify_technician_password()`, `set_password()`
- `techcare/setup/wizard.py`: `_ask_technician_password()`
- `techcare/config/settings.py`: `technician_password_hash`, `session_timeout`
- `.env.example`: Neue Variablen

**Verwendung:**
```bash
# Setup (beim ersten Start)
techcare
# > Passwort jetzt setzen? [Y/n]

# Passwort ändern
techcare --set-password

# Bei jedem Start
techcare
# > Passwort: ********
```

---

#### 2. **Netzwerkverbindung zu Backend-Services** 🌐

**Zweck:** Verbindung zu zentralen Services (PostgreSQL, License Server)

**Unterstützte Methoden:**
1. **Cloudflare Tunnel** (empfohlen) - HTTPS, DDoS-Schutz
2. **Tailscale** - Zero-Config VPN, WireGuard
3. **VPN** - WireGuard, OpenVPN, etc.
4. **Direkte IP** - LAN oder Port-Forwarding

**Features:**
- Setup-Wizard fragt nach Netzwerk-Methode
- Backend-URL konfigurierbar
- Connection-Timeout Handling
- Offline-Fallback für Lizenz-Cache

**Dateien:**
- `techcare/setup/wizard.py`: `_ask_network_connection()`
- `techcare/config/settings.py`: `backend_url`, `network_method`
- `.env.example`: `BACKEND_URL`, `NETWORK_METHOD`

**Konfiguration:**
```bash
# Cloudflare
BACKEND_URL=https://techcare.deinefirma.de
NETWORK_METHOD=cloudflare

# Tailscale
BACKEND_URL=http://techcare
NETWORK_METHOD=tailscale

# VPN
BACKEND_URL=http://192.168.1.100
NETWORK_METHOD=vpn
```

---

#### 3. **Lizenzvalidierung** 📜

**Zweck:** Lizenzschlüssel-Prüfung beim Start (Pro/Enterprise)

**Features:**
- Online-Validierung via Backend-API
- Offline-Fallback mit gecachter Lizenz (max 7 Tage)
- Edition-Features (Community/Pro/Pro Business/Enterprise)
- Lizenz-Ablaufdatum-Prüfung

**Dateien:**
- `techcare/core/license.py`: **NEU** - `LicenseValidator`, `validate_license()`
- `techcare/core/bot.py`: `_check_license()` Methode
- `techcare/setup/wizard.py`: `_ask_license_key()`
- `techcare/config/settings.py`: `license_key`, `edition`
- `.env.example`: `LICENSE_KEY`, `EDITION`

**API-Endpoint (Backend):**
```
POST /api/license/validate
{
  "license_key": "TECHCARE-PRO-BUSINESS-ABC123"
}

Response:
{
  "valid": true,
  "edition": "pro_business",
  "expires_at": "2027-02-17T00:00:00",
  "max_systems": 0,
  "customer_name": "Firma XYZ"
}
```

**Verwendung:**
```bash
# Setup
LICENSE_KEY=TECHCARE-PRO-BUSINESS-ABC123
EDITION=pro_business

# Bei Start
techcare
# > 🔑 Validiere Lizenz...
# > ✓ Lizenz gültig: Pro Business
```

---

#### 4. **Monitoring/Sensor-Mode** 📡

**Zweck:** Proaktives System-Monitoring im Hintergrund

**Features:**
- Background-Service (Windows Service / macOS LaunchDaemon / Linux systemd)
- Sammelt Metriken alle 5 Minuten (konfigurierbar)
- Sendet Daten an Backend
- Metriken: CPU, RAM, Disk, Services, Updates, Errors, SMART

**Dateien:**
- `techcare/monitoring/sensor.py`: **NEU** - `SystemSensor` Klasse
- `techcare/monitoring/service.py`: **NEU** - Service-Installation
- `.env.example`: `SENSOR_INTERVAL`

**Gesammelte Metriken:**
- CPU / RAM / Disk Usage
- Kritische Service-Status (Firewall, Defender, etc.)
- Pending Updates
- Event Log Errors (letzte 5)
- SMART Disk Health

**Installation als Service:**
```bash
# Windows
python -m techcare.monitoring.service
# > Windows Service installiert!

# macOS
python -m techcare.monitoring.service
# > LaunchDaemon installiert!

# Linux
python -m techcare.monitoring.service
# > systemd Service installiert!
```

**Manuelle Ausführung:**
```bash
python -m techcare.monitoring.sensor
# > 🔍 TechCare Sensor gestartet (Interval: 300s)
# > [10:30:00] Sammle Metriken...
# > [10:30:05] ✓ Metriken gesendet
```

---

#### 5. **Treiber-Management** 🔧

**Zweck:** Prüft Treiber-Status und empfiehlt Updates

**Features:**
- Windows Update API Integration
- macOS Software Update Integration
- Custom Driver Database (JSON)
- Installations-Anweisungen
- Kritische vs. empfohlene Updates

**Dateien:**
- `techcare/tools/drivers/driver_manager.py`: **NEU** - `DriverManager` Klasse
- `techcare/tools/drivers/driver_database.json`: **NEU** - Custom Driver DB
- `techcare/tools/audit/drivers.py`: **NEU** - Audit Tool

**Verwendung im Bot:**
```
> "Prüfe Treiber-Updates"

Bot führt check_drivers aus:

📊 Statistik:
   • Installierte Treiber: 150
   • Veraltete Treiber: 3
   • Kritische Updates: 1
   • Empfohlene Updates: 2

🔄 VERFÜGBARE UPDATES:

🔴 1. NVIDIA GeForce RTX 3080
   Aktuell: 512.95
   Verfügbar: 528.49
   Wichtigkeit: CRITICAL
   Quelle: windows_update
```

**Custom Database erweitern:**

Bearbeite `techcare/tools/drivers/driver_database.json`:
```json
{
  "hardware_id": "PCI\\VEN_10DE&DEV_2206",
  "name": "NVIDIA GeForce RTX 3080",
  "vendor": "NVIDIA",
  "category": "Graphics",
  "latest_version": "528.49",
  "release_date": "2023-02-14",
  "download_url": "https://...",
  "notes": "Game Ready Driver"
}
```

---

#### 6. **Deinstallation** 🗑️

**Zweck:** Einfache Deinstallation von TechCare

**Features:**
- Löscht .env, data/, ~/.techcare/
- User-Bestätigung erforderlich
- Python-Package bleibt installiert (manuell deinstallieren)

**Dateien:**
- `techcare/__main__.py`: `uninstall()` Funktion

**Verwendung:**
```bash
techcare --uninstall

# > 🗑️  TechCare Deinstallation
# > Folgende Daten werden gelöscht:
# >   • .env Datei (API-Key, Konfiguration)
# >   • data/ Verzeichnis (Sessions, Changelogs, Cases)
# >   • ~/.techcare/ (User-Config, Cache)
# >
# > Wirklich deinstallieren? [y/N]: y
# >
# > ✓ .env gelöscht
# > ✓ data/ gelöscht
# > ✓ ~/.techcare/ gelöscht
# >
# > ✅ TechCare erfolgreich deinstalliert!
```

---

### 🔧 Änderungen an bestehenden Komponenten

#### Setup-Wizard (`techcare/setup/wizard.py`)

**Neue Fragen:**
- Lizenzschlüssel (für Pro+)
- Netzwerkverbindung (Cloudflare/Tailscale/VPN/Direkt)
- Backend-URL
- Techniker-Passwort

**Neue Methoden:**
- `_ask_license_key()`
- `_ask_network_connection()`
- `_ask_technician_password()`

#### Settings (`techcare/config/settings.py`)

**Neue Felder:**
- `backend_url: str` - URL zum Backend
- `network_method: str` - Netzwerk-Methode
- `edition: str` - Edition
- `license_key: str` - Lizenzschlüssel
- `technician_password_hash: str` - bcrypt-Hash
- `session_timeout: int` - Session-Timeout

#### Bot (`techcare/core/bot.py`)

**Neue Methode:**
- `async def _check_license()` - Prüft Lizenz beim Start

**Neue Imports:**
- `from techcare.core.license import validate_license, check_edition_features`

#### Main Entry (`techcare/__main__.py`)

**Neue Funktionen:**
- `verify_technician_password()` - Passwort-Check
- `uninstall()` - Deinstallation
- `set_password()` - Passwort setzen/ändern

**Neue CLI-Argumente:**
- `--uninstall` - Deinstalliert TechCare
- `--set-password` - Setzt/ändert Passwort
- `--version` - Zeigt Version

#### Environment Variables (`.env.example`)

**Neue Variablen:**
```bash
# Network Connection
BACKEND_URL=
NETWORK_METHOD=direct

# License
EDITION=community
LICENSE_KEY=

# Security
TECHNICIAN_PASSWORD_HASH=
SESSION_TIMEOUT=3600

# Monitoring
SENSOR_INTERVAL=300
```

---

### 📦 Neue Dependencies (`requirements.txt`)

```txt
passlib[bcrypt]>=1.7.4   # Passwort-Hashing
httpx>=0.25.0            # Async HTTP Client
```

**Optional (für Windows Service):**
```bash
pip install pywin32  # Windows Service Support
```

---

### 📁 Neue Dateien/Verzeichnisse

```
techcare/
├── core/
│   └── license.py                  # NEU - Lizenzvalidierung
├── monitoring/                      # NEU
│   ├── __init__.py
│   ├── sensor.py                   # Monitoring Sensor
│   └── service.py                  # Service-Installation
└── tools/
    └── drivers/                    # NEU
        ├── __init__.py
        ├── driver_manager.py       # Driver-Management
        └── driver_database.json    # Custom Driver DB

HYBRID_ARCHITECTURE.md              # NEU - Architektur-Dokumentation
CHANGELOG_HYBRID.md                 # NEU - Changelog
```

---

### 🚀 Deployment

#### Docker-Services (Zentral)

Neue `docker-compose.yml` (vereinfacht):

```yaml
services:
  postgres:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=techcare_learning
      - POSTGRES_USER=techcare
      - POSTGRES_PASSWORD=secure_password

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  license-server:
    image: techcare/license-server:latest
    environment:
      - DATABASE_URL=postgresql://...
```

**Web/API/Nginx entfernt** - CLI kommuniziert direkt mit Services

---

### 🔐 Sicherheit

**Neue Sicherheits-Features:**
1. Passwort-Schutz (bcrypt)
2. Lizenz-Validierung (signierte Keys)
3. Verschlüsselte Netzwerkverbindungen (HTTPS/VPN)
4. Session-Timeout
5. Offline-Lizenz-Cache max 7 Tage

---

### 📖 Verwendung

#### Installation

```bash
# 1. Klone Repo
git clone <repo>
cd TechCare-Bot

# 2. Dependencies installieren
pip install -e .

# 3. Setup ausführen
techcare
# Setup-Wizard startet automatisch

# 4. Passwort setzen (optional)
techcare --set-password

# 5. Sensor-Service installieren (optional)
python -m techcare.monitoring.service
```

#### Nutzung

```bash
# Starten
techcare

# Passwort eingeben (wenn gesetzt)
# Bot startet

# Chat:
> "Prüfe Treiber-Updates"
> "Analysiere System"
> "GO REPAIR: 1,2,3"

# Exit
> exit
```

---

### 🐛 Bugfixes

Keine - Dies ist ein Major-Feature-Update

---

### 💡 Breaking Changes

**WICHTIG:** Migration von v1.x zu v2.0:

1. **Setup neu durchführen** - Neue Fragen (Netzwerk, Lizenz, Passwort)
2. **Docker-Compose anpassen** - Web-Services entfernt
3. **Backend-URL konfigurieren** - Cloudflare/Tailscale/VPN
4. **Lizenzschlüssel eingeben** - Für Pro/Enterprise

---

### 🔮 Roadmap (Nächste Schritte)

- [ ] Web-Dashboard für Monitoring-Daten
- [ ] Multi-System Management (mehrere PCs gleichzeitig)
- [ ] Scheduled Maintenance (automatische Wartung)
- [ ] Custom Tool Plugins (Drittanbieter-Tools)
- [ ] Rollback-Mechanismus (Auto-Rollback bei Fehlern)
- [ ] Team-Features (für Enterprise)

---

### 👥 Contributor

- Carsten Eckhardt (Eckhardt-Marketing)

---

### 📄 License

MIT License

---

## Installation & Setup Guide

Siehe **HYBRID_ARCHITECTURE.md** für Details zur neuen Architektur.

---

**Viel Erfolg mit TechCare Bot 2.0!** 🚀
