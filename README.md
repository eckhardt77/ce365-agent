# TechCare Bot 🔧

**AI-powered IT-Wartungs-Assistent für Windows/macOS Systeme**

TechCare Bot ist dein intelligenter Helfer für IT-Wartung und -Support. Mit Claude AI als Engine hilft er dir bei Diagnose und Reparatur von IT-Problemen – sicher, transparent und lernfähig.

## ✨ Features

### 🔒 Sicherheit First
- **Sicherer Workflow**: Audit → Analyse → Plan → Freigabe → Ausführung
- **Execution Lock**: Keine Reparaturen ohne explizite "GO REPAIR" Freigabe
- **Backup-Check**: Fragt vor jeder Diagnose nach Backup-Status
- **Changelog**: Automatisches Logging aller Reparatur-Aktionen

### 🧠 Intelligent & Lernfähig
- **Learning System**: Bot lernt aus gelösten Problemen
- **Ähnliche Fälle**: Schlägt bekannte Lösungen vor bei ähnlichen Problemen
- **Team Learning**: Optional mit Remote-Datenbank (PostgreSQL/MySQL)
- **Web-Recherche**: Sucht online nach Lösungen über DuckDuckGo

### 🛡️ DSGVO-konform
- **PII Detection**: Automatische Erkennung sensibler Daten mit Microsoft Presidio
- **Anonymisierung**: Emails, Telefonnummern, Namen werden vor API-Übertragung anonymisiert
- **User-Warnings**: Warnt wenn persönliche Daten erkannt wurden

### 🌍 Cross-Platform
- **Windows & macOS Support**
- **NUR Deutsch**: Alle Kommunikation ausschließlich auf Deutsch

## 📚 Dokumentation

- **🚀 Quick Start**: `QUICK_START.md` - 5-Minuten Anleitung
- **💿 Installation**: `docs/INSTALLATION.md` - Windows & macOS Schritt-für-Schritt
- **📖 Nutzung**: `docs/NUTZUNGSANLEITUNG.md` - Vollständige Anleitung mit Beispielen
- **📋 Vorlagen**: `docs/VORLAGEN.md` - Audit-Kits, Templates, Beispiele
- **✅ Tests**: `TEST_RESULTS.md` - Live-Test Ergebnisse

## 🚀 Quick Start

### Voraussetzungen
- Python 3.9+
- Anthropic API Key ([hier erstellen](https://console.anthropic.com))

### Installation

```bash
# Repository klonen
git clone https://github.com/yourusername/techcare-bot.git
cd techcare-bot

# Virtual Environment erstellen
python -m venv venv

# Aktivieren
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Bot installieren
pip install -e .

# API Key konfigurieren
cp .env.example .env
# Dann ANTHROPIC_API_KEY in .env eintragen

# Bot starten
techcare
```

**Vollständige Anleitung**: Siehe `docs/INSTALLATION.md`

## Verwendung

### Bot starten

```bash
techcare
```

### Beispiel-Session

```
You: Neuer Fall

TechCare:
🔧 TechCare - Neue Diagnose-Session
──────────────────────────────────────
1. Existiert ein aktuelles Backup? (Ja/Nein/Unbekannt)
2. Betriebssystem? (Windows 10/11 oder macOS)
3. Was ist das Problem?
4. Bereits etwas versucht?

You: Ja Backup, Windows 11, Windows Update Fehler

TechCare:
✓ Backup vorhanden - gut!

📋 AUDIT-PHASE
Kommando 1: systeminfo | findstr /C:"OS Name"
Bitte kopiere den Output hier ein.

You: [kopiert Output]

TechCare: [analysiert weitere Kommandos...]

🔍 DIAGNOSE
Problem: Windows Update Service läuft nicht
Root Cause: Service wuauserv gestoppt

📋 REPARATUR-PLAN
Schritt 1: Windows Update Service starten
  Risiko: NIEDRIG
  Rollback: sc stop wuauserv

Bitte bestätige mit: GO REPAIR: 1

You: GO REPAIR: 1

TechCare:
🔧 AUSFÜHRUNG - Schritt 1
Kommando: sc start wuauserv
Bitte führe aus und kopiere Output.

You: [kopiert Output]

TechCare:
✓ Schritt 1 erfolgreich!
📝 ÄNDERUNGSLOG - Schritt 1 [gespeichert]
```

## Workflow

### 1. AUDIT Phase (Read-Only)
- Bot sammelt System-Informationen
- Keine Änderungen am System
- Audit-Tools sind immer erlaubt

### 2. ANALYSE Phase
- Bot analysiert gesammelte Daten
- Identifiziert Probleme

### 3. PLAN Phase
- Bot erstellt nummerierten Reparatur-Plan
- Erklärt jeden Schritt

### 4. FREIGABE
- User gibt Schritte frei: `GO REPAIR: 1,2,3`
- Auch Range möglich: `GO REPAIR: 1-3`

### 5. AUSFÜHRUNG
- Bot führt nur freigegebene Schritte aus
- Changelog wird automatisch erstellt

## 🛠️ Verfügbare Tools

### Audit-Tools (immer erlaubt)
- **get_system_info**: System-Informationen (OS, CPU, RAM, Disk, Uptime)
- **web_search**: Internet-Recherche für Problemlösungen (DuckDuckGo)
- **web_instant_answer**: Schnelle Antworten für einfache Fragen

### Repair-Tools (nach GO REPAIR)
- **manage_service**: Service Management (start/stop/restart/status)

## 🧠 Learning System

TechCare Bot lernt aus gelösten Problemen:

### Lokales Learning (Standard)
- Speichert Fälle in lokaler SQLite-Datenbank (`data/cases.db`)
- Keine zusätzliche Konfiguration nötig

### Team Learning (Optional)
Mit Remote-Datenbank können mehrere Techniker Wissen teilen:

```bash
# .env konfigurieren
LEARNING_DB_TYPE=postgresql  # oder mysql
LEARNING_DB_URL=postgresql://user:pass@host:5432/techcare
```

**Features:**
- Keyword-basierte Ähnlichkeitssuche
- Error-Code Matching
- Success Rate Tracking
- Automatischer Fallback auf lokale DB bei Connection-Fehler

Siehe `docs/REMOTE_DB_SETUP.md` für Details.

## 🛡️ PII Detection (DSGVO)

Microsoft Presidio erkennt und anonymisiert automatisch:
- Email-Adressen
- Telefonnummern
- Namen (Personen)
- IP-Adressen
- IBAN, Kreditkarten
- Passwörter (Pattern-basiert)

**Konfiguration:**
```bash
# .env
PII_DETECTION_ENABLED=true
PII_DETECTION_LEVEL=high  # high, medium, low
PII_SHOW_WARNINGS=true
```

Siehe `docs/PII_DETECTION.md` für Details.

## 🔍 Web-Recherche

Bot kann online nach Lösungen suchen:
- DuckDuckGo Search (kostenlos, kein API-Key)
- KB Article Detection (Microsoft, Apple Support)
- DACH Region (de-de)
- Safe Search aktiviert

**Konfiguration:**
```bash
# .env
WEB_SEARCH_ENABLED=true
```

## Sicherheitsregeln

1. **Execution Lock**: Keine Repair-Tools ohne GO REPAIR Befehl
2. **Read-Only First**: Immer erst Audit, dann Plan
3. **Einzelschritt**: Nur EIN Schritt auf einmal, dann Output abwarten
4. **Backup-Check**: Vor jeder Diagnose nach Backup fragen
5. **Allowlist/Blocklist**: Strikte Kontrolle über Aktionen
6. **Transparenz**: Jeder Schritt wird erklärt
7. **Changelog**: Alle Änderungen werden geloggt
8. **NUR Deutsch**: Alle Kommunikation auf Deutsch

## Dokumentation

- **Vorlagen & Audit-Kits**: Siehe `docs/VORLAGEN.md`
  - Audit-Kit Windows (8 Kommandos)
  - Audit-Kit macOS (8 Kommandos)
  - Plan-Vorlage
  - Ausführungs-Vorlage
  - Beispiel-Fälle
  - Sicherheitsregeln Quick Reference

## Entwicklung

### Neue Tools hinzufügen

1. Audit-Tool erstellen:
```python
from techcare.tools.base import AuditTool

class MyAuditTool(AuditTool):
    @property
    def name(self) -> str:
        return "my_audit_tool"

    @property
    def description(self) -> str:
        return "Beschreibung für Claude"

    @property
    def input_schema(self) -> dict:
        return {"type": "object", "properties": {...}}

    async def execute(self, **kwargs) -> str:
        # Implementation
        return "Result"
```

2. Tool in `techcare/core/bot.py` registrieren:
```python
self.tool_registry.register(MyAuditTool())
```

## Changelog

Alle Repair-Aktionen werden in `data/changelogs/{session_id}.json` geloggt:

```json
{
  "session_id": "...",
  "created_at": "2026-02-17T10:30:00",
  "entries": [
    {
      "timestamp": "2026-02-17T10:35:12",
      "tool_name": "manage_service",
      "tool_input": {"service_name": "wuauserv", "action": "restart"},
      "result": "SUCCESS",
      "success": true
    }
  ]
}
```

## 🔧 Technologie-Stack

- **Python 3.9+**
- **Anthropic API** (Claude Sonnet 4.5)
- **SQLAlchemy** (Multi-DB Support)
- **Microsoft Presidio** (PII Detection)
- **DuckDuckGo Search** (Web-Recherche)
- **psutil** (System-Informationen)
- **rich** (Terminal UI)
- **pydantic** (Data Validation)

## 📄 Lizenz

MIT License

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing

Siehe `LICENSE` für Details.

## 🤝 Support

Bei Fragen oder Problemen: Issue auf GitHub erstellen

---

**Made with ❤️ by Carsten Eckhardt / Eckhardt-Marketing**
