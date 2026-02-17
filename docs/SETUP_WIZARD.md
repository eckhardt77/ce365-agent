# Setup-Wizard - Dokumentation

## Überblick

Der Setup-Wizard wird **automatisch beim ersten Start** ausgeführt, wenn noch keine `.env` Konfiguration existiert.

## Features

✅ **Interaktive Konfiguration**
- Name & Firma eingeben
- Anthropic API Key einrichten
- Optional: Use-Case beschreiben

✅ **API Key Validierung**
- Format-Check (muss mit `sk-ant-` beginnen)
- Optional: Test-Request an Claude API

✅ **Automatische .env Erstellung**
- Erstellt `.env` aus Template
- Setzt sichere Permissions (600)
- Fügt User-Info als Kommentar hinzu

✅ **Benutzerfreundlich**
- Rich Console UI mit Farben
- Klare Anweisungen
- Abbruch jederzeit möglich (exit/quit/q)

## Ablauf

### 1. Erster Start (ohne .env)

```bash
techcare
```

Der Wizard startet automatisch:

```
╔════════════════════════════════════════════════════════════════╗
║  🔧 TechCare Bot - Einrichtungsassistent                       ║
║                                                                ║
║  Willkommen! Lass uns TechCare Bot einrichten.                ║
║  Das dauert nur 2 Minuten.                                    ║
╚════════════════════════════════════════════════════════════════╝

1. Dein Name
   Wird für Changelog und Personalisierung verwendet

   Name: █
```

### 2. Name eingeben

```
   Name: Max Mustermann
```

### 3. Firma/Team (optional)

```
2. Firma / Team (optional)
   Für Team-Reports und Identifikation

   Firma/Team: IT-Abteilung GmbH
```

### 4. API Key

```
3. Anthropic API Key (erforderlich)
   Erstelle einen Key: https://console.anthropic.com

   API Key: ••••••••••••••••••••
```

**Format-Validierung:**
- Muss mit `sk-ant-` beginnen
- Wird als Passwort-Input versteckt

**Bei falschem Format:**
```
   ❌ Ungültiges Format. API Keys beginnen mit 'sk-ant-'
   Nochmal versuchen? [Y/n]:
```

### 5. Briefing (optional)

```
4. Briefing / Use-Case (optional)
   Beschreibe kurz wofür du TechCare nutzt
   Beispiel: 'Windows-Support für 50 Clients'

   Briefing: IT-Support für Büro, hauptsächlich Windows
```

### 6. API Key Test

```
API Key jetzt testen? [Y/n]: y

⠋ Teste API Key...

✓ API Key funktioniert!
```

### 7. Fertig!

```
╔════════════════════════════════════════════════════════════════╗
║  ✅ Setup abgeschlossen!                                        ║
║                                                                ║
║  Willkommen, Max Mustermann! TechCare Bot ist jetzt           ║
║  einsatzbereit.                                               ║
║                                                                ║
║  Starte mit: Neuer Fall                                       ║
╚════════════════════════════════════════════════════════════════╝

TechCare Bot v0.2 - AI IT-Wartungsassistent
...
```

## .env Datei

Nach dem Setup wird automatisch `.env` erstellt:

```bash
# ============================================================================
# TechCare Bot - Konfiguration
# ============================================================================
# User: Max Mustermann
# Firma: IT-Abteilung GmbH
# Use-Case: IT-Support für Büro, hauptsächlich Windows
# Erstellt: 2026-02-17 13:45:23
# ============================================================================

# Anthropic API Key (erforderlich)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx...

# Optional: Log Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Optional: Claude Model
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# ... (weitere Konfiguration)
```

## Setup erneut ausführen

Um den Setup-Wizard erneut auszuführen:

```bash
# .env löschen oder umbenennen
mv .env .env.old

# TechCare starten
techcare
```

Der Wizard startet automatisch.

## Setup überspringen

Falls `.env` bereits existiert, startet TechCare direkt ohne Setup-Wizard.

## Manuelle Konfiguration

Du kannst `.env` auch manuell erstellen:

```bash
# Template kopieren
cp .env.example .env

# API Key eintragen
nano .env  # oder Editor deiner Wahl
```

Dann startet TechCare ohne Wizard.

## Abbruch

Setup kann jederzeit abgebrochen werden:

- Eingabe: `exit`, `quit` oder `q`
- Oder: `Ctrl+C`

```
Setup abgebrochen.
👋 Setup abgebrochen. Auf Wiedersehen!
```

## Fehlerbehandlung

### API Key Test fehlgeschlagen

```
❌ API Key Test fehlgeschlagen: Invalid API key

⚠️  API Key konnte nicht getestet werden.
   Du kannst TechCare trotzdem nutzen.

Trotzdem fortfahren? [Y/n]:
```

**Optionen:**
- `y` → Setup wird abgeschlossen (trotz fehlgeschlagenem Test)
- `n` → Setup wird abgebrochen

### .env Schreibfehler

```
❌ Fehler beim Erstellen der .env Datei
```

**Mögliche Ursachen:**
- Keine Schreibrechte im Verzeichnis
- Festplatte voll
- .env existiert bereits (sollte nicht passieren)

**Lösung:**
- Verzeichnis-Permissions prüfen
- Manuell `.env` erstellen

## Sicherheit

### API Key Handling

- ✅ **Passwort-Input**: API Key wird während Eingabe versteckt
- ✅ **Secure Permissions**: `.env` wird mit `chmod 600` erstellt (nur Owner lesbar)
- ✅ **Nicht in Git**: `.env` ist in `.gitignore` gelistet

### API Key Test

Der Test-Request:
- Verwendet minimal Tokens (~10 Tokens)
- Sendet nur "Hi" als Test-Message
- Kostet < 0.001€

**Privacy:**
- Keine persönlichen Daten werden gesendet
- Nur API-Key-Validierung

## Code-Referenz

**Setup-Wizard:** `techcare/setup/wizard.py`

**Integration:** `techcare/__main__.py` (Zeile 15-18)

```python
# Setup-Wizard (falls .env nicht existiert)
if not run_setup_if_needed():
    print("\n👋 Setup abgebrochen. Auf Wiedersehen!")
    sys.exit(0)
```

## Erweiterungen (Future)

Mögliche Erweiterungen:

- [ ] Spacy-Modell automatisch installieren (für PII Detection)
- [ ] Database Setup (Remote PostgreSQL/MySQL)
- [ ] Team-Konfiguration (Multi-User)
- [ ] Plugin-Installation
- [ ] Update-Check beim Setup
