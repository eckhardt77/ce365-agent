# CE365 Agent

**KI-gestuetzter IT-Service-Assistent mit Multi-Agent System**

[![License: BSL-1.1](https://img.shields.io/badge/License-BSL--1.1-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](https://agent.ce365.de)

CE365 Agent ist dein KI-Sidekick im Terminal. Er diagnostiziert IT-Probleme, schlaegt Reparaturen vor und dokumentiert alles automatisch. Powered by Claude, GPT-4o oder beliebige OpenRouter-Modelle (BYOK).

**[Website](https://agent.ce365.de)** | **[English Version](https://agent.ce365.de/en/)**

---

## Quick Start

```bash
pip install ce365-agent
ce365
```

Der Setup-Wizard fuehrt dich durch Provider-Auswahl und API-Key-Konfiguration.

---

## Features

### Community (Kostenlos)

- 7 Diagnose-Tools (System Info, Logs, Prozesse, Updates, Backup, Security, Startup)
- 3 Basis-Repair-Tools (Service Manager, Disk Cleanup, DNS Flush)
- 5 Repairs / Monat
- PII-Erkennung (Microsoft Presidio) — DSGVO-konform
- Lokales Learning System (SQLite)
- Multi-Provider: Claude, GPT-4o, OpenRouter (BYOK)
- Multi-Language: Deutsch + English
- Passwort-Schutz

### Pro

- **Alles aus Community, plus:**
- Unbegrenzte Repairs
- **Multi-Agent System** — Steve + 3 spezialisierte Agenten
- **Live-Modell-Auswahl** — KI-Modelle on-the-fly wechseln per `/model`
- **SOAP Incident Reports** — Professionelle Einsatzberichte per `/report`
- **Slash-Commands** — `/help`, `/stats`, `/provider`, `/model`, `/report`, `/privacy`
- **Provider Hot-Swap** — Provider mitten in der Session wechseln per `/provider`
- 30+ Tools (Advanced Audit, Repair, Stress Tests, Drivers, Malware Scan)
- Web-Recherche + KI Root-Cause-Analyse
- Shared Learning (PostgreSQL)
- Kommerzielle Nutzung
- Auto-Updates + Priority Support

**[Pro holen](https://agent.ce365.de/#pricing)**

---

## So funktioniert's

```
$ ce365

Hey, ich bin Steve — dein IT-Sidekick. Was liegt an?

> Kunde meldet: Laptop extrem langsam seit 2 Wochen

Verstanden. Ich starte eine Komplett-Diagnose...

█ Diagnose abgeschlossen (7 Tools, 12 Sek.)

  ❌ Festplatte: 97% voll (nur 4 GB frei)
  ❌ 14 Autostart-Programme (Boot: 3 Min 20 Sek)
  ⚠️  RAM: 7.2/8 GB belegt (Chrome: 4.1 GB)
  ✔ CPU-Temperatur: 62°C (OK)

Mein Vorschlag:
  1. Temp-Dateien bereinigen (~18 GB freigeben)
  2. 9 unnoetige Autostart-Programme deaktivieren
  3. Chrome-Profil optimieren

Soll ich loslegen? Tippe GO REPAIR: 1,2,3
```

Keine Reparatur wird ohne deine explizite Freigabe per `GO REPAIR` ausgefuehrt.

---

## Multi-Agent System (Pro)

Steve koordiniert 3 spezialisierte KI-Agenten, die parallel arbeiten:

| Agent | Aufgabe |
|-------|---------|
| **Diagnostics Agent** | Analysiert System, Event-Logs, Prozesse, Netzwerk |
| **Repair Agent** | Fuehrt freigegebene Reparaturen aus |
| **Documentation Agent** | Protokolliert alles automatisch (Changelog + SOAP) |

Wie ein eingespieltes Team — nur schneller.

---

## Slash-Commands (Pro)

| Command | Funktion |
|---------|----------|
| `/help` | Hilfe und verfuegbare Befehle |
| `/stats` | Session-Statistiken (Tokens, Kosten, Tools) |
| `/provider` | KI-Provider wechseln |
| `/model` | KI-Modell wechseln (Live-Liste von Provider-API) |
| `/report` | SOAP Incident Report generieren |
| `/privacy` | PII-Erkennungsstatus anzeigen |

---

## Voraussetzungen

- Python 3.11 oder 3.12
- API-Key fuer: Anthropic (Claude), OpenAI (GPT-4o) oder OpenRouter
- Windows, macOS oder Linux

---

## Installation

### Per pip (empfohlen)

```bash
pip install ce365-agent
ce365
```

### Aus dem Quellcode

```bash
git clone https://github.com/eckhardt77/ce365-agent.git
cd ce365-agent
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
python -m ce365
```

---

## CLI-Optionen

```bash
ce365                    # Normaler Start
ce365 --version          # Version anzeigen
ce365 --health           # Health-Check (Python, Dependencies, API, Config)
ce365 --set-password     # Techniker-Passwort setzen/aendern
ce365 --update           # Auf neueste Version aktualisieren
ce365 --rollback         # Rollback zur letzten Version
ce365 --uninstall        # Deinstallation
```

---

## Sicherheit

- **GO REPAIR Lock** — Keine Systemeingriffe ohne explizite Freigabe
- **PII-Erkennung** — Personenbezogene Daten werden vor API-Calls automatisch anonymisiert (Presidio)
- **Passwort-Schutz** — Optionaler bcrypt-gesicherter Zugang
- **Audit Trail** — Jede Aktion wird im Changelog protokolliert
- **Datenschutz** — Alle Daten bleiben lokal, DSGVO-konform
- **OS Keychain** — API-Keys im System-Keychain gespeichert (macOS Keychain, Windows Credential Manager)

---

## Projektstruktur

```
ce365-agent/
  ce365/
    core/           Bot, Providers, License, Session, Agents, Commands
    tools/          30+ Audit-, Repair-, Research-, Analyse-Tools
    config/         Settings, System-Prompt, Secrets
    workflow/       State Machine, Execution Lock
    learning/       Case Library, Similarity Matching
    privacy/        PII Detection (Presidio)
    i18n/           Mehrsprachigkeit (DE + EN)
    ui/             Rich Terminal UI
    setup/          Setup-Wizard
  license-server/   FastAPI Lizenzserver (Stripe, Brevo)
  website/          Landing Page (DE + EN)
  scripts/          Build- und Deployment-Tools
  docs/             Dokumentation
  tests/            Test-Suite
```

---

## Lizenz

**Business Source License 1.1 (BSL-1.1)**

- Lesen, Studieren, Modifizieren: **erlaubt**
- Nicht-kommerzielle Nutzung: **erlaubt**
- Kommerzielle Nutzung: erfordert eine [Pro-Lizenz](https://agent.ce365.de)
- Ab 2030-02-19: wird zu Apache License 2.0

Siehe [LICENSE](LICENSE) fuer Details.

---

## Support

- Issues: [GitHub Issues](https://github.com/eckhardt77/ce365-agent/issues)
- E-Mail: info@eckhardt-marketing.de
- Website: [agent.ce365.de](https://agent.ce365.de)

---

Made by [Eckhardt-Marketing](https://eckhardt-marketing.de)
