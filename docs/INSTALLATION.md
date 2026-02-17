# CE365 Agent - Installation

## 📋 Voraussetzungen

### Windows
- **Windows 10** oder **Windows 11**
- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Terminal** (PowerShell oder CMD)
- **Anthropic API Key** ([Erstellen](https://console.anthropic.com/))

### macOS
- **macOS 13+** (Ventura, Sonoma, Sequoia)
- **Python 3.9+** (meist vorinstalliert)
- **Terminal**
- **Anthropic API Key** ([Erstellen](https://console.anthropic.com/))

---

## 🪟 Installation auf Windows

### Schritt 1: Python installieren

1. Gehe zu https://www.python.org/downloads/
2. Lade **Python 3.9+** herunter
3. **WICHTIG**: Aktiviere bei Installation "Add Python to PATH"!
4. Prüfe Installation:
   ```cmd
   python --version
   ```
   Sollte zeigen: `Python 3.9.x` oder höher

### Schritt 2: CE365 Agent herunterladen

**Option A: Mit Git**
```cmd
cd C:\Users\<DeinName>\Documents
git clone <repository-url> CE365-Bot
cd CE365-Bot
```

**Option B: ZIP herunterladen**
1. Lade ZIP herunter
2. Entpacke nach `C:\Users\<DeinName>\Documents\CE365-Bot`
3. Öffne PowerShell:
   ```powershell
   cd C:\Users\<DeinName>\Documents\CE365-Bot
   ```

### Schritt 3: Virtual Environment erstellen

```powershell
# Virtual Environment erstellen
python -m venv venv

# Virtual Environment aktivieren
.\venv\Scripts\activate

# Du solltest jetzt "(venv)" vor dem Prompt sehen
```

### Schritt 4: Dependencies installieren

```powershell
# Packages installieren
pip install -e .

# Prüfen ob Installation erfolgreich
ce365 --help
```

Falls `ce365` nicht gefunden wird:
```powershell
python -m ce365
```

### Schritt 5: API Key konfigurieren

1. Erstelle `.env` Datei:
   ```powershell
   copy .env.example .env
   notepad .env
   ```

2. Trage deinen API Key ein:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-xxx...
   ```

3. Speichern und schließen

### Schritt 6: Bot starten

```powershell
ce365
```

**Bei jedem Start**: Virtual Environment aktivieren:
```powershell
cd C:\Users\<DeinName>\Documents\CE365-Bot
.\venv\Scripts\activate
ce365
```

---

## 🍎 Installation auf macOS

### Schritt 1: Python prüfen

```bash
# Python Version prüfen
python3 --version

# Sollte Python 3.9+ zeigen
# Falls nicht: Homebrew installieren und Python upgraden
```

Falls Python fehlt oder veraltet:
```bash
# Homebrew installieren (falls noch nicht vorhanden)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python installieren
brew install python@3.11
```

### Schritt 2: CE365 Agent herunterladen

**Option A: Mit Git**
```bash
cd ~/Documents
git clone <repository-url> CE365-Bot
cd CE365-Bot
```

**Option B: ZIP herunterladen**
1. Lade ZIP herunter
2. Entpacke nach `~/Documents/CE365-Bot`
3. Terminal öffnen:
   ```bash
   cd ~/Documents/CE365-Bot
   ```

### Schritt 3: Virtual Environment erstellen

```bash
# Virtual Environment erstellen
python3 -m venv venv

# Virtual Environment aktivieren
source venv/bin/activate

# Du solltest jetzt "(venv)" vor dem Prompt sehen
```

### Schritt 4: Dependencies installieren

```bash
# Packages installieren
pip install -e .

# Prüfen ob Installation erfolgreich
ce365 --help
```

Falls `ce365` nicht gefunden wird:
```bash
python -m ce365
```

### Schritt 5: API Key konfigurieren

```bash
# .env Datei erstellen
cp .env.example .env

# Mit Texteditor öffnen
nano .env
```

Trage deinen API Key ein:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxx...
```

Speichern: `Ctrl+O`, `Enter`, `Ctrl+X`

### Schritt 6: Bot starten

```bash
ce365
```

**Bei jedem Start**: Virtual Environment aktivieren:
```bash
cd ~/Documents/CE365-Bot
source venv/bin/activate
ce365
```

---

## 🔑 Anthropic API Key erstellen

1. Gehe zu: https://console.anthropic.com/
2. Registriere dich / Logge dich ein
3. Navigiere zu "API Keys"
4. Klicke "Create Key"
5. Kopiere den Key (beginnt mit `sk-ant-api03-...`)
6. **WICHTIG**: Speichere den Key sicher, er wird nur einmal angezeigt!

---

## 🧪 Test-Installation

Nach der Installation kannst du testen:

### Windows:
```powershell
cd C:\Users\<DeinName>\Documents\CE365-Bot
.\venv\Scripts\activate
python auto_demo_test.py
```

### macOS:
```bash
cd ~/Documents/CE365-Bot
source venv/bin/activate
python auto_demo_test.py
```

Sollte ausgeben:
```
✅ ALLE TESTS ERFOLGREICH:
  ✓ System Prompt (alle Features)
  ✓ Tool Registry
  ✓ State Machine
  ...
```

---

## 🚨 Troubleshooting

### Windows

**Problem**: `python` nicht gefunden
```powershell
# Lösung: Vollständiger Pfad verwenden
C:\Users\<DeinName>\AppData\Local\Programs\Python\Python39\python.exe -m venv venv
```

**Problem**: Virtual Environment aktiviert nicht
```powershell
# Lösung: Execution Policy ändern
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\activate
```

**Problem**: `ce365` nicht gefunden
```powershell
# Lösung: Python-Modul direkt aufrufen
python -m ce365
```

### macOS

**Problem**: `python3` nicht gefunden
```bash
# Lösung: Homebrew installieren und Python installieren
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.11
```

**Problem**: Permission denied
```bash
# Lösung: Dateirechte setzen
chmod +x ce365/__main__.py
```

**Problem**: Virtual Environment aktiviert nicht
```bash
# Lösung: Prüfe ob venv korrekt erstellt wurde
ls -la venv/bin/activate
source venv/bin/activate
```

### Beide Plattformen

**Problem**: API Key ungültig
```
# Symptom: "AuthenticationError: Invalid API Key"
# Lösung:
1. Prüfe .env Datei: cat .env (macOS) oder type .env (Windows)
2. Stelle sicher, dass Key mit "sk-ant-api03-" beginnt
3. Keine Leerzeichen vor/nach dem Key
4. Erstelle neuen Key in Anthropic Console
```

**Problem**: Dependencies installieren fehlgeschlagen
```bash
# Lösung: pip upgraden
pip install --upgrade pip
pip install -e .
```

**Problem**: Out of Memory
```
# Symptom: Prozess friert ein oder stürzt ab
# Lösung: Mindestens 4GB RAM verfügbar haben
# Große Systeminfo-Outputs vermeiden
```

---

## 📞 Support

Bei weiteren Problemen:
1. Prüfe `TEST_RESULTS.md` für bekannte Issues
2. Schaue in `docs/VORLAGEN.md` für Beispiele
3. Erstelle ein Issue auf GitHub

---

## 🔄 Update auf neue Version

### Windows:
```powershell
cd C:\Users\<DeinName>\Documents\CE365-Bot
.\venv\Scripts\activate
git pull
pip install -e . --upgrade
```

### macOS:
```bash
cd ~/Documents/CE365-Bot
source venv/bin/activate
git pull
pip install -e . --upgrade
```

---

## 🗑️ Deinstallation

### Windows:
```powershell
# Virtual Environment deaktivieren
deactivate

# Verzeichnis löschen
cd ..
rmdir /s CE365-Bot
```

### macOS:
```bash
# Virtual Environment deaktivieren
deactivate

# Verzeichnis löschen
cd ..
rm -rf CE365-Bot
```

---

**Bereit für den ersten Fall!** → Siehe `docs/NUTZUNGSANLEITUNG.md`
