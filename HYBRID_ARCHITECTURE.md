# TechCare Bot - Hybrid Architecture

## Übersicht

TechCare Bot verwendet eine **Hybrid-Architektur**:

- **CLI auf Kunden-PC** (voller System-Zugriff für Reparaturen)
- **Zentrale Docker-Services** (PostgreSQL, License Server, Redis)
- **Netzwerkverbindung** via VPN/Cloudflare/Tailscale

## Architektur-Diagramm

```
┌─────────────────────────────────────────┐
│  Kunden-PC / Techniker-Laptop           │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  TechCare CLI                     │ │
│  │                                   │ │
│  │  • System-Diagnose (lokal)       │ │
│  │  • Reparaturen (Admin-Rechte)    │ │
│  │  • Terminal-UI (Rich Console)    │ │
│  │  • Sensor-Mode (optional)        │ │
│  └───────────────────────────────────┘ │
│               │                         │
│               │ VPN / Cloudflare /      │
│               │ Tailscale               │
└───────────────┼─────────────────────────┘
                │
                │ HTTPS / TLS
                ▼
┌─────────────────────────────────────────┐
│  Zentrale Firma NAS / Server (Docker)   │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  PostgreSQL                      │  │
│  │  (Shared Learning Database)      │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  License Server (FastAPI)        │  │
│  │  (Lizenzvalidierung)             │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Redis (Cache)                   │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Neue Features (Hybrid-Mode)

### 1. **Techniker-Passwort**

Schützt TechCare vor unbefugtem Zugriff:

```bash
# Beim ersten Start oder Setup:
# Passwort wird abgefragt und als bcrypt-Hash gespeichert

# Passwort ändern:
techcare --set-password

# Bei jedem Start:
# Passwort-Eingabe (3 Versuche)
```

**Konfiguration in .env:**
```bash
TECHNICIAN_PASSWORD_HASH=<bcrypt-hash>
SESSION_TIMEOUT=3600  # 1 Stunde
```

---

### 2. **Netzwerkverbindung**

Verbindung zu zentralen Services über verschiedene Methoden:

#### a) Cloudflare Tunnel (empfohlen)
```bash
BACKEND_URL=https://techcare.deinefirma.de
NETWORK_METHOD=cloudflare
```

**Vorteile:**
- Automatisches HTTPS
- Keine Port-Freigabe nötig
- DDoS-Schutz
- Zero-Trust Security

**Setup:**
```bash
# Auf Server:
cloudflared tunnel create techcare
cloudflared tunnel route dns techcare techcare.deinefirma.de

# CLI-Installation beim Kunden: nichts nötig!
```

#### b) Tailscale (Zero-Config VPN)
```bash
BACKEND_URL=http://techcare  # Magic DNS
NETWORK_METHOD=tailscale
```

**Vorteile:**
- Einfachste Einrichtung
- WireGuard-basiert (schnell)
- Peer-to-Peer wenn möglich
- Cross-Platform

**Setup:**
```bash
# Auf Server + jedem Techniker-Laptop:
tailscale up
```

#### c) VPN (WireGuard/OpenVPN)
```bash
BACKEND_URL=http://192.168.1.100
NETWORK_METHOD=vpn
```

**Vorteile:**
- Volle Kontrolle
- On-Premise
- Keine Drittanbieter

#### d) Direkte IP / Port-Forwarding
```bash
BACKEND_URL=https://techcare.firma.de:8443
NETWORK_METHOD=direct
```

**Nur für Testing! Nicht Production!**

---

### 3. **Lizenzvalidierung**

Prüft Lizenzschlüssel beim Start:

```bash
LICENSE_KEY=TECHCARE-PRO-BUSINESS-ABC123
EDITION=pro_business
```

**Features nach Edition:**

| Feature                | Community | Pro | Pro Business | Enterprise |
|------------------------|-----------|-----|--------------|------------|
| Unbegrenzte Reparaturen| ❌        | ✅  | ✅           | ✅         |
| Unbegrenzte Systeme    | ❌        | ❌  | ✅           | ✅         |
| Sensor-Mode            | ❌        | ❌  | ✅           | ✅         |
| Shared Learning DB     | ❌        | ❌  | ❌           | ✅         |
| Team-Features          | ❌        | ❌  | ❌           | ✅         |

**Online + Offline:**
- Bei Start: Online-Validierung via Backend
- Bei Offline: Cached License (max 7 Tage)
- Bei Ablauf: Error + CLI beendet

---

### 4. **Monitoring/Sensor-Mode**

Background-Service der System-Metriken sammelt:

```bash
# Manuelle Ausführung:
python -m techcare.monitoring.sensor

# Als Service installieren:
python -m techcare.monitoring.service

# Windows: Windows Service
# macOS: LaunchDaemon
# Linux: systemd Service
```

**Gesammelte Metriken:**
- CPU / RAM / Disk Usage
- Kritische Service-Status (Firewall, Defender, etc.)
- Pending Updates
- Event Log Errors (letzte 5)
- SMART Disk Health

**Interval:**
```bash
SENSOR_INTERVAL=300  # 5 Minuten (Standard)
```

**Backend-Endpoint:**
```
POST /api/monitoring/metrics
Authorization: Bearer <api_key>

{
  "timestamp": "2026-02-17T10:30:00",
  "hostname": "DESKTOP-123",
  "os": "windows",
  "cpu_percent": 45.2,
  "ram_percent": 62.1,
  ...
}
```

---

### 5. **Treiber-Management**

Prüft Treiber-Status und empfiehlt Updates:

```python
# Als Audit Tool im Bot:
"Prüfe Treiber-Updates"

# CLI:
python -m techcare.tools.drivers.driver_manager
```

**Quellen:**
1. **Windows Update API** (Windows)
2. **Apple Software Update** (macOS)
3. **Custom Driver Database** (driver_database.json)

**Output:**
```
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
   Installation: Install via Windows Update
```

**Custom Database erweitern:**

Bearbeite `techcare/tools/drivers/driver_database.json`:

```json
{
  "hardware_id": "PCI\\VEN_XXXX&DEV_YYYY",
  "name": "Hardware Name",
  "vendor": "Vendor",
  "category": "Graphics",
  "latest_version": "1.2.3",
  "release_date": "2026-02-01",
  "download_url": "https://...",
  "notes": "Optional Notes"
}
```

---

### 6. **Deinstallation**

Einfacher Uninstall-Befehl:

```bash
techcare --uninstall
```

**Löscht:**
- `.env` Datei (API-Key, Konfiguration)
- `data/` Verzeichnis (Sessions, Changelogs, Cases)
- `~/.techcare/` (User-Config, Cache)

**Behält:**
- Python-Package (manuell deinstallieren: `pip uninstall techcare`)

---

## Setup-Wizard

Beim ersten Start führt der Setup-Wizard durch:

1. **Name & Firma** (für Changelog)
2. **Edition** (Community / Pro / Pro Business / Enterprise)
3. **Lizenzschlüssel** (für Pro+)
4. **API Key** (Anthropic)
5. **Netzwerkverbindung** (Cloudflare / Tailscale / VPN / Direkt)
6. **Backend-URL** (z.B. `https://techcare.firma.de`)
7. **Learning Database** (nur Enterprise: PostgreSQL/MySQL)
8. **Techniker-Passwort** (optional aber empfohlen)
9. **Briefing** (optional)

**Ergebnis:**
- `.env` Datei mit allen Settings
- Lizenz validiert
- Passwort-Hash gespeichert

---

## Docker-Services (Zentral)

Auf Server/NAS mit Docker:

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
      - JWT_SECRET=...
```

**Start:**
```bash
docker-compose up -d
```

**Netzwerk-Zugriff einrichten:**
- Cloudflare Tunnel oder
- Tailscale auf Server oder
- VPN oder
- Port-Forwarding (nicht empfohlen)

---

## CLI-Installation (Kunden-PC)

1. **Python installieren** (3.10+)

2. **TechCare installieren:**
```bash
git clone <repo>
cd TechCare-Bot
pip install -e .
```

3. **Setup ausführen:**
```bash
techcare
# Setup-Wizard startet automatisch
```

4. **Passwort setzen:**
```bash
techcare --set-password
```

5. **Optional: Sensor-Service installieren:**
```bash
python -m techcare.monitoring.service
```

---

## Verwendung

### Normale Nutzung

```bash
# Starten
techcare

# Passwort eingeben (wenn gesetzt)
# Bot startet

# Chat mit Bot:
> "Windows Update funktioniert nicht"
> "Prüfe Treiber-Updates"
> "GO REPAIR: 1,2,3"

# Exit
> exit
```

### Sensor-Mode

```bash
# Service starten (Windows)
sc start TechCareSensor

# Service starten (macOS)
sudo launchctl start com.techcare.sensor

# Service starten (Linux)
sudo systemctl start techcare-sensor

# Logs anzeigen (Windows)
# Event Viewer → Application Logs

# Logs anzeigen (macOS)
tail -f /var/log/techcare-sensor.log

# Logs anzeigen (Linux)
sudo journalctl -u techcare-sensor -f
```

---

## Sicherheit

### Passwort-Schutz

- Passwort wird als bcrypt-Hash gespeichert (nicht im Klartext)
- 3 Fehlversuche → CLI beendet
- Session-Timeout konfigurierbar

### Netzwerk-Sicherheit

- Cloudflare: HTTPS + DDoS-Schutz
- Tailscale: WireGuard VPN
- Alle Verbindungen verschlüsselt

### Lizenz-Schutz

- Lizenzschlüssel signiert (Server-Validierung)
- Offline-Cache nur 7 Tage gültig
- Lizenz-Ablauf wird geprüft

---

## Troubleshooting

### "Lizenz-Check fehlgeschlagen"

1. Prüfe BACKEND_URL in .env
2. Prüfe Netzwerkverbindung (ping)
3. Prüfe Lizenzschlüssel
4. Prüfe ob License-Server läuft

### "Passwort falsch"

```bash
# Passwort zurücksetzen:
techcare --set-password
```

### "Connection refused"

1. Prüfe ob Docker-Services laufen
2. Prüfe Firewall-Regeln
3. Prüfe Cloudflare/Tailscale Setup

### "Driver-Check fehlgeschlagen"

Windows: Prüfe Admin-Rechte (PowerShell)
macOS: Prüfe Terminal-Berechtigungen
Linux: Prüfe smartctl Installation

---

## Roadmap

- [ ] Web-Dashboard für Monitoring
- [ ] Multi-System Management
- [ ] Scheduled Maintenance
- [ ] Custom Tool Plugins
- [ ] Rollback-Mechanismus

---

Fragen? → GitHub Issues oder Support kontaktieren
