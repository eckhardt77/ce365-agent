# 🔧 TechCare Bot - Community Edition v2.0.0

**KI-gestützter IT-Wartungs-Assistent für Windows und macOS**

🇩🇪 Deutsche Version | [🇺🇸 English Version](README.md)

TechCare Bot ist ein KI-gestützter IT-Wartungs-Assistent, der dir bei der Diagnose und Reparatur von Windows- und macOS-Systemen hilft. Mit natürlicher Sprachinteraktion und **über 30 integrierten Tools** wird IT-Wartung zum Kinderspiel!

[![License: Source Available](https://img.shields.io/badge/License-Source%20Available-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude%20Sonnet%204.5-blueviolet)](https://anthropic.com)

---

## 🆕 Neuerungen in v2.0

### ✨ Neue Features

- 🔐 **Techniker-Passwort-Schutz** - Schütze TechCare vor unbefugtem Zugriff
- 🔧 **Treiber-Management** - Prüfe auf Treiber-Updates (Windows Update + Eigene DB)
- 📡 **Monitoring-Sensor** - Hintergrunddienst für proaktive Systemüberwachung
- 🗑️ **Einfache Deinstallation** - Deinstallation mit `techcare --uninstall`
- 🔑 **Lizenz-System** - Optional für Pro/Enterprise (Community ist kostenlos!)
- 🌐 **Netzwerk-Optionen** - Remote-Dienste via VPN/Cloudflare/Tailscale (optional)

### 🎯 Alle Community-Features (Kostenlos)

✅ **15 Basis-Tools** - Grundlegende Diagnose und Reparatur
✅ **KI-gestützte Analyse** - Ursachenerkennung
✅ **Treiber-Check** - Automatische Treiber-Update-Erkennung
✅ **Monitoring** - Hintergrund-Systemüberwachung
✅ **Passwort-Schutz** - Sicherer TechCare-Zugang
✅ **Max 10 Reparaturen/Monat** - Ideal zum Testen
✅ **Multi-Language** - Deutsch + Englisch
✅ **Cross-Platform** - Windows, macOS, Linux (exp)

---

## ⚠️ Haftungsausschluss

**WICHTIG: Nutzung auf eigene Verantwortung!**

TechCare Bot wird "WIE BESEHEN" bereitgestellt, OHNE JEGLICHE GARANTIE.

**Keine Haftung für:**
- ❌ Datenverlust
- ❌ Systemschäden
- ❌ Fehlerhafte Reparaturen
- ❌ Ausfallzeiten
- ❌ Sicherheitsvorfälle

**Vor der Nutzung:**
- ✅ **Immer Backups erstellen**
- ✅ **Erst in Test-Umgebung testen**
- ✅ **Alle Befehle vor Freigabe prüfen**
- ✅ **Keine autonomen Reparaturen** (GO REPAIR-Sperre erforderlich)

Mit der Nutzung von TechCare Bot übernimmst du die volle Verantwortung.

---

## 🚀 Quick Start

### Installation (5 Minuten)

#### 1. Python 3.11 oder 3.12 installieren

**macOS (Homebrew):**
```bash
brew install python@3.12
```

**Windows:**
Download von [python.org](https://www.python.org/downloads/)

#### 2. Repository klonen

```bash
git clone https://github.com/yourusername/techcare-bot.git
cd techcare-bot
```

#### 3. Virtuelle Umgebung erstellen

```bash
# Venv erstellen
python3.12 -m venv venv

# Aktivieren
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

#### 4. TechCare installieren

```bash
pip install -e .
```

#### 5. TechCare starten

```bash
techcare
```

Beim ersten Start führt dich der **Setup-Assistent** durch:
- Name & Firma
- Edition (Community / Pro / Enterprise)
- Anthropic API Key ([Kostenlos holen](https://console.anthropic.com))
- Sprache (English / Deutsch)
- **Optional:** Techniker-Passwort
- **Optional:** Netzwerk-Konfiguration (für Pro/Enterprise)

---

## 📋 Voraussetzungen

- **Python 3.11 oder 3.12** (Python 3.14 wird noch nicht unterstützt)
- **Anthropic API Key** ([Kostenlose Stufe verfügbar](https://console.anthropic.com))
- Internet-Verbindung (für Claude API)

---

## 🎮 Verwendung

### Basis-Befehle

```bash
# TechCare starten
techcare

# Techniker-Passwort setzen/ändern
techcare --set-password

# Version anzeigen
techcare --version

# TechCare deinstallieren
techcare --uninstall

# Hilfe
techcare --help
```

### Beispiel-Session

```
🔧 TechCare Bot v2.0.0
Session ID: abc123...
💡 Learning: 5 Fälle gespeichert, 2 Wiederverwendungen
─────────────────────────────────────────────────
Sprache: Deutsch | 'exit' zum Beenden
─────────────────────────────────────────────────

🔍 Erstelle System-Statusbericht...

[System Info]
🖥️  macOS 14.2, CPU: 8 Kerne (12% Auslastung)
RAM: 16.0 GB (8.2 GB frei, 48% genutzt)
Disk: 500 GB (120 GB frei, 76% genutzt)
Uptime: 3d 2h 15m

✅ System-Statusbericht abgeschlossen
💬 Wie kann ich dir helfen?
─────────────────────────────────────────────────

> Prüfe auf Treiber-Updates

🔄 Prüfe Treiber...

📊 Statistiken:
   • Installierte Treiber: 150
   • Veraltete Treiber: 3
   • Kritische Updates: 1
   • Empfohlene Updates: 2

🔄 VERFÜGBARE UPDATES:

🔴 1. NVIDIA GeForce RTX 3080
   Aktuell: 512.95
   Verfügbar: 528.49
   Wichtigkeit: KRITISCH
   Quelle: windows_update

🟡 2. Intel Wi-Fi 6 AX200
   Aktuell: 22.80.0
   Verfügbar: 22.120.0
   Wichtigkeit: EMPFOHLEN
   Quelle: windows_update

⚠️  EMPFEHLUNG:
   Installiere 1 kritisches Treiber-Update!

> Windows Update funktioniert nicht

Lass mich das analysieren...

🎯 URSACHE GEFUNDEN
╔══════════════════════════════════════════════╗
║  Ursache: BITS-Dienst hängt                  ║
║  Konfidenz: 87%                              ║
║                                              ║
║  Beweis:                                     ║
║  ✓ Event Log: BITS Fehler 0x80070057        ║
║  ✓ Service-Status: Läuft, aber reagiert     ║
║     nicht                                    ║
║  ✓ Temp-Ordner: 47 unvollständige Downloads ║
║                                              ║
║  Lösung:                                     ║
║  1. BITS-Dienst neu starten                 ║
║  2. Download-Warteschlange leeren           ║
╚══════════════════════════════════════════════╝

Reparatur-Plan:
1. BITS-Dienst neu starten (wuauserv)
2. Windows Update Cache leeren

Bitte bestätigen mit: GO REPAIR: 1,2

> GO REPAIR: 1,2

✅ Führe Reparaturen aus...
[Schritt 1/2] Starte BITS-Dienst neu... ✓
[Schritt 2/2] Leere Update-Cache... ✓

🎉 Alle Reparaturen erfolgreich abgeschlossen!
📋 Changelog gespeichert unter: data/changelogs/abc123.json
```

---

## 🛠️ Verfügbare Tools (30+)

### 📊 Audit-Tools (Read-Only)

| Tool | Beschreibung |
|------|--------------|
| **System Info** | OS, CPU, RAM, Disk, Uptime |
| **Process Monitor** | Laufende Prozesse, CPU/RAM-Nutzung |
| **System Logs** | Event Log / Syslog-Analyse |
| **Updates Check** | Ausstehende Windows/macOS-Updates |
| **Backup Status** | Time Machine / Windows Backup-Status |
| **Security Audit** | Firewall, Antivirus, Gatekeeper, SIP |
| **Startup Programs** | Autostart-Apps mit Impact-Analyse |
| **Malware Scanner** | Windows Defender / ClamAV Integration |
| **🆕 Driver Check** | Treiber-Updates prüfen |
| **Network Diagnostics** | IP, DNS, Verbindungstests |
| **Stress Tests** | CPU, Speicher, Disk-Geschwindigkeitstests |
| **System Report** | Umfassender HTML-Report |
| **Web Search** | Online-Lösungssuche |

### 🔧 Reparatur-Tools (Freigabe erforderlich)

| Tool | Beschreibung |
|------|--------------|
| **Service Manager** | Windows/macOS-Dienste starten/stoppen/neu starten |
| **Disk Cleanup** | Temp-Dateien, Cache, Logs löschen |
| **DNS Flush** | DNS-Cache leeren |
| **Network Reset** | TCP/IP-Stack zurücksetzen |
| **SFC Scan** | System File Checker (Windows) |
| **Disk Repair** | Disk-Berechtigungen reparieren (macOS) |
| **Update Installer** | Windows/macOS-Updates installieren |
| **Backup Creator** | Wiederherstellungspunkt / Time Machine-Backup erstellen |
| **Startup Manager** | Autostart-Programme aktivieren/deaktivieren |
| **Update Scheduler** | Automatische Updates planen |

### 🧠 KI-Analyse-Tools

- 🎯 **Root Cause Analysis** - KI-gestützte Problemdiagnose
- 📊 **Pattern Recognition** - Wiederkehrende Probleme erkennen

---

## 🆕 Neue Features im Detail

### 🔐 Techniker-Passwort-Schutz

Schütze TechCare vor unbefugtem Zugriff:

```bash
# Passwort während Setup setzen
techcare
# > Techniker-Passwort setzen? [J/n]: j
# > Passwort: ********

# Oder später setzen
techcare --set-password

# Bei jedem Start
techcare
# > 🔐 TechCare Zugang
# > Passwort: ********
# > ✓ Authentifiziert
```

**Features:**
- bcrypt-gehashtes Passwort (sicher)
- 3 Versuchslimit
- Session-Timeout (konfigurierbar)
- Optional (kann übersprungen werden)

---

### 🔧 Treiber-Management

Automatische Treiber-Update-Erkennung:

```bash
> Prüfe auf Treiber-Updates

📊 Treiber-Statusbericht:
   • Treiber gesamt: 150
   • Veraltet: 3
   • Kritisch: 1
   • Empfohlen: 2

🔄 Verfügbare Updates:
🔴 NVIDIA Grafiktreiber (Kritisch)
🟡 Intel Netzwerkadapter (Empfohlen)
```

**Quellen:**
- Windows Update API (Windows)
- Apple Software Update (macOS)
- Eigene Treiber-Datenbank (JSON-basiert)

**Eigene Datenbank:**
Füge eigene Treiber in `techcare/tools/drivers/driver_database.json` hinzu

---

### 📡 Monitoring-Sensor

Hintergrunddienst für proaktive Überwachung:

```bash
# Manueller Test
python -m techcare.monitoring.sensor

# Als Dienst installieren
python -m techcare.monitoring.service

# Windows: Windows Service
# macOS: LaunchDaemon
# Linux: systemd Service
```

**Erfasste Metriken:**
- CPU / RAM / Disk-Nutzung
- Status kritischer Dienste (Firewall, Antivirus)
- Ausstehende Updates
- Aktuelle Event-Log-Fehler
- SMART Disk-Gesundheit

**Standard-Intervall:** 5 Minuten (konfigurierbar)

---

### 🗑️ Einfache Deinstallation

Einfache Deinstallation:

```bash
techcare --uninstall

# Löscht:
# ✓ .env-Datei (Konfiguration)
# ✓ data/ Verzeichnis (Sessions, Changelogs, Cases)
# ✓ ~/.techcare/ (Cache, User-Konfiguration)
```

---

## 🔐 Sicherheitsfeatures

### 1. GO REPAIR-Sperre

```
Keine Reparaturen ohne deine explizite Freigabe:
- Bot erstellt Reparatur-Plan
- Du prüfst jeden Schritt
- Du gibst frei mit: GO REPAIR: 1,2,3
- Nur freigegebene Schritte werden ausgeführt
```

### 2. Techniker-Passwort (NEU!)

```
Schütze TechCare vor unbefugtem Zugriff:
- Passwort beim Start erforderlich
- 3 Versuchslimit
- bcrypt-gehashed (sicher)
- Session-Timeout
```

### 3. Verschlüsselte API-Key-Speicherung

```
API-Keys sicher im OS-Keychain gespeichert:
- macOS: Keychain Access
- Windows: Credential Manager
- Linux: Secret Service (gnome-keyring)
- Fallback: .env (mit Migrations-Hinweis)
```

### 4. PII-Erkennung (Microsoft Presidio)

```
Erkennt und anonymisiert automatisch:
- Kreditkartennummern
- E-Mail-Adressen
- Telefonnummern
- Passwörter
- IP-Adressen
```

### 5. Audit Trail

```
Jede Reparatur wird protokolliert:
- Zeitstempel
- Verwendetes Tool
- Eingabe-Parameter
- Ergebnis
- Erfolg/Fehler-Status

Gespeichert unter: data/changelogs/{session_id}.json
```

---

## 🌍 Multi-Language-Support

TechCare Bot unterstützt:
- 🇺🇸 **English**
- 🇩🇪 **Deutsch**

### Sprache ändern

**Während Setup:**
```
Choose language / Sprache wählen:
1. English
2. Deutsch
```

**Nach Setup:**
```bash
# Via Befehl
techcare --language de

# Interaktiv
> language de
Sprache geändert auf: Deutsch
```

---

## 🧠 Lernsystem (Pro+)

**Ab Pro Edition:** TechCare lernt aus jeder Reparatur:

```python
# Ähnliches Problem erkannt
💡 Learning: Ich habe einen ähnlichen Fall von vor 3 Tagen gefunden:
   Problem: "Windows Update fehlgeschlagen"
   Lösung: BITS-Dienst neu gestartet
   Erfolg: Ja

   Soll ich dieselbe Lösung anwenden? (ja/nein)
```

**Vorteile:**
- ⚡ Schnellere Lösung (verwendet bewährte Lösungen wieder)
- 📈 Verbessert sich mit der Zeit
- 🎯 Höhere Erfolgsrate

**Datenschutz:**
- **Pro/Pro Business:** Lokal gespeichert in `data/cases.db`
- **Enterprise:** Optional zentrale Team-Wissensdatenbank (PostgreSQL)
- PII automatisch anonymisiert
- Kann mit `techcare --clear-cases` gelöscht werden

---

## 🏢 Pro & Enterprise Features (Optional)

Community Edition ist **100% kostenlos** - perfekt zum Testen mit max 10 Reparaturen/Monat.

Für professionelle und kommerzielle Nutzung bieten wir:

### TechCare Pro (49€/Monat)
- ✅ 30+ Tools (statt 15)
- ✅ Unbegrenzte Reparaturen (statt max 10)
- ✅ Lokales Lernsystem (SQLite)
- ✅ Case-Wiederverwendung
- ✅ 1 System
- ✅ E-Mail-Support

### TechCare Pro Business (99€/Monat)
- ✅ Alle Pro-Features
- ✅ Unbegrenzte Systeme
- ✅ Zentrale Dashboards
- ✅ Fleet-Management
- ✅ Priority-Support

### TechCare Enterprise (ab 149€/Monat)
- ✅ Alle Pro Business-Features
- ✅ Gemeinsame Team-Lerndatenbank (PostgreSQL)
- ✅ Team-Management (LDAP/SSO)
- ✅ Zentrale Überwachung
- ✅ Individuelle Integrationen
- ✅ Dedizierter Support

**Lizenz-System:**
- Optional (Community funktioniert ohne Lizenz)
- Online + Offline-Validierung
- Flexible Lizenzmodelle
- Kontakt: sales@eckhardt-marketing.de

---

## 📦 Projekt-Struktur

```
techcare-bot/
├── techcare/                          # Hauptpaket
│   ├── core/                         # Kern-Funktionalität
│   │   ├── bot.py                   # Haupt-Bot-Orchestrierung
│   │   ├── client.py                # Anthropic API-Client
│   │   ├── session.py               # Session-Management
│   │   └── license.py               # Lizenz-Validierung (optional)
│   ├── tools/                        # Tool-System
│   │   ├── audit/                   # Read-only-Tools
│   │   ├── repair/                  # Reparatur-Tools
│   │   ├── drivers/                 # Treiber-Management (NEU!)
│   │   └── analysis/                # KI-Analyse-Tools
│   ├── workflow/                     # Workflow-Zustandsmaschine
│   ├── learning/                     # Lernsystem
│   ├── monitoring/                   # Monitoring-Sensor (NEU!)
│   ├── security/                     # PII-Erkennung
│   └── ui/                           # Terminal-UI (Rich)
├── data/                             # Lokale Daten (gitignored)
│   ├── sessions/                    # Chat-Sessions
│   ├── changelogs/                  # Reparatur-Logs
│   └── cases.db                     # Lerndatenbank
├── .env.example                      # Umgebungs-Template
├── requirements.txt                  # Python-Abhängigkeiten
└── README_DE.md                      # Diese Datei
```

---

## 🔄 Updates

```bash
# TechCare updaten
cd techcare-bot
git pull
pip install -r requirements.txt --upgrade

# Version prüfen
techcare --version
```

---

## 🐛 Fehlerbehebung

### Import Error: No module named 'rich'

```bash
pip install -r requirements.txt
```

### Python 3.14 Kompatibilität

Python 3.14 wird noch nicht unterstützt. Verwende Python 3.11 oder 3.12:

```bash
brew install python@3.12
python3.12 -m venv venv
source venv/bin/activate
pip install -e .
```

### Treiber-Check funktioniert nicht

- **Windows:** Benötigt Admin-Rechte (PowerShell)
- **macOS:** Terminal-Berechtigungen prüfen
- **Linux:** `smartctl` installieren

### "techcare: command not found"

```bash
# Python direkt verwenden
python -m techcare

# Oder PATH prüfen
which techcare
```

---

## 🤝 Mitwirken

Beiträge sind willkommen! Bitte:

1. Repository forken
2. Feature-Branch erstellen (`git checkout -b feature/NeuesFeature`)
3. Änderungen committen (`git commit -m 'Füge NeuesFeature hinzu'`)
4. Zum Branch pushen (`git push origin feature/NeuesFeature`)
5. Pull Request öffnen

**Entwicklungs-Setup:**
```bash
git clone https://github.com/yourusername/techcare-bot.git
cd techcare-bot
python3.12 -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt  # Dev-Abhängigkeiten
```

---

## 📄 Lizenz

**Source Available License** - Kostenlos für nicht-kommerzielle Nutzung.

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing

Die Community Edition ist kostenlos für persönliche, akademische und
nicht-kommerzielle Nutzung. Kommerzielle Nutzung (IT-Dienstleister, MSPs,
Unternehmens-IT) erfordert eine [Kommerzielle Lizenz](https://techcare.eckhardt-marketing.de).

Siehe [LICENSE](LICENSE) für vollständige Details.

---

## 🐛 Bug-Reports & Sicherheit

**Bug-Reports:**
- GitHub Issues: https://github.com/yourusername/techcare-bot/issues

**Sicherheitslücken:**
- **KEINE** öffentlichen Issues erstellen
- E-Mail: security@eckhardt-marketing.de
- Betreff: [SECURITY] TechCare Bot - [Kurze Beschreibung]

Siehe [SECURITY.md](SECURITY.md) für Responsible Disclosure Policy.

---

## 💬 Support

- 📖 Dokumentation: [Wiki](https://github.com/yourusername/techcare-bot/wiki)
- 💬 Diskussionen: [GitHub Discussions](https://github.com/yourusername/techcare-bot/discussions)
- 🐛 Bug-Reports: [GitHub Issues](https://github.com/yourusername/techcare-bot/issues)

**Kommerzieller Support:**
- E-Mail: support@eckhardt-marketing.de
- Website: https://techcare.eckhardt-marketing.de

---

## 🙏 Danksagungen

- **Anthropic Claude** - KI-Engine
- **Microsoft Presidio** - PII-Erkennung
- **Rich** - Schöne Terminal-Ausgabe
- **psutil** - System-Monitoring
- **spaCy** - NLP-Verarbeitung

---

## 📊 Statistiken

- **30+ Tools** - Umfassendes IT-Toolset
- **52 Error-Codes** - Integrierte Wissensdatenbank
- **2 Sprachen** - Deutsch + Englisch
- **3 Plattformen** - Windows, macOS, Linux (exp)
- **100% Kostenlos** - Community Edition (nicht-kommerzielle Nutzung)

---

## 🗺️ Roadmap

### v2.1 (Q2 2026)
- [ ] Web-Dashboard (optional)
- [ ] Plugin-System
- [ ] Mehr Sprachen (Französisch, Spanisch)

### v2.2 (Q3 2026)
- [ ] Predictive Maintenance
- [ ] Cloud-Backup-Integration
- [ ] Mobile Companion App

### v3.0 (Q4 2026)
- [ ] Multi-System-Management
- [ ] Geplante Wartung
- [ ] Custom Tool Builder

---

Made with ❤️ by Eckhardt-Marketing

**TechCare Bot** - Weil IT-Wartung einfach sein sollte.

**Community Edition v2.0.0** - Für immer kostenlos 🎉
