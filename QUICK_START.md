# CE365 Agent — Quick Start

## Installation

```bash
pip install ce365-agent
ce365
```

Alternative (aus Quellcode):

```bash
git clone https://github.com/eckhardt77/ce365-agent.git
cd ce365-agent
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -e .
python -m ce365
```

---

## Erster Start: Setup-Wizard

Beim ersten Start fuehrt dich der Wizard durch die Konfiguration:

```
1. Name eingeben          → Wird fuer Reports und Changelog verwendet
2. Edition waehlen        → Community (kostenlos) oder Pro
3. LLM-Provider waehlen   → Anthropic (empfohlen), OpenAI oder OpenRouter
4. API-Key eingeben       → Von deinem Provider (BYOK)
5. Passwort setzen        → Optional, schuetzt den Zugang
```

Danach startet Steve automatisch.

---

## Erster Test-Fall

```
💻 Darwin 25.2.0 | CPU: 11 Kerne | RAM: 76% | Disk frei: 92 GB
💬 Wie kann ich dir helfen?

> Steve: Mein Laptop ist seit Tagen extrem langsam.

Steve fragt: Backup vorhanden? Betriebssystem?

> Steve: Ja, Time Machine. macOS Sequoia.

Steve fuehrt Diagnose aus (Read-Only, keine Aenderungen)...

█ Diagnose abgeschlossen
  ❌ Festplatte: 97% voll
  ❌ 14 Autostart-Programme

Steve schlaegt vor:
  1. Temp-Dateien bereinigen
  2. Autostart-Programme deaktivieren

> Steve: GO REPAIR: 1

Steve fuehrt nur Schritt 1 aus, zeigt Ergebnis.
Fertig!
```

---

## Die wichtigsten Befehle

| Eingabe | Was passiert |
|---------|-------------|
| `/` | Alle Commands anzeigen |
| `/help` | Ausfuehrliche Hilfe |
| `/stats` | Learning-Statistiken |
| `/provider` | LLM-Provider wechseln |
| `/model` | LLM-Modell wechseln |
| `/report` | Incident Report erstellen |
| `/privacy` | Datenschutz-Einstellungen |
| `GO REPAIR: 1,2` | Reparatur-Schritte freigeben |
| `exit` | Session beenden |

---

## Wichtigste Regeln

**Steve aendert nie etwas ohne deine Freigabe.**

- Diagnose = Read-Only (automatisch)
- Reparatur = nur nach `GO REPAIR`
- Schritte laufen einzeln, nie parallel
- Alles wird protokolliert

---

## CLI-Optionen

```bash
ce365                    # Normaler Start
ce365 --version          # Version anzeigen
ce365 --health           # Health-Check
ce365 --set-password     # Passwort setzen/aendern
ce365 --update           # Update
ce365 --rollback         # Rollback
ce365 --uninstall        # Deinstallation
```

---

## Hilfe

- Ausfuehrliche Anleitung: `docs/NUTZUNGSANLEITUNG.md`
- Installation: `docs/INSTALLATION.md`
- GitHub: [github.com/eckhardt77/ce365-agent/issues](https://github.com/eckhardt77/ce365-agent/issues)
- Website: [agent.ce365.de](https://agent.ce365.de)
