# 🚀 TechCare Bot - Quick Start

## 5-Minuten Start-Anleitung

### Windows (PowerShell)

```powershell
# 1. In Projektverzeichnis wechseln
cd C:\Users\<DeinName>\Documents\TechCare-Bot

# 2. Virtual Environment aktivieren
.\venv\Scripts\activate

# 3. Bot starten
techcare

# Bei Problemen:
python -m techcare
```

### macOS (Terminal)

```bash
# 1. In Projektverzeichnis wechseln
cd ~/Documents/TechCare-Bot

# 2. Virtual Environment aktivieren
source venv/bin/activate

# 3. Bot starten
techcare

# Bei Problemen:
python -m techcare
```

---

## ⚡ Erster Test-Fall

```
1. Bot startet und zeigt Logo

2. Du schreibst: Neuer Fall

3. TechCare fragt:
   - Backup vorhanden? → Antworte: Ja
   - Betriebssystem? → Antworte: Windows 11 (oder dein OS)
   - Problem? → Antworte: Windows Update Fehler
   - Bereits versucht? → Antworte: Neustart

4. TechCare startet Audit:
   Kommando 1: systeminfo | findstr /C:"OS Name"

5. Du führst Kommando aus und kopierst Output zurück

6. TechCare analysiert und gibt weitere Kommandos

7. Nach Audit: TechCare erstellt Reparatur-Plan

8. Du gibst Freigabe: GO REPAIR: 1

9. TechCare führt Schritt 1 aus (nur dieser!)

10. Fertig! ✓
```

---

## 📖 Vollständige Anleitungen

- **Installation**: `docs/INSTALLATION.md`
  - Windows & macOS Schritt-für-Schritt
  - Python Installation
  - API Key Setup
  - Troubleshooting

- **Nutzung**: `docs/NUTZUNGSANLEITUNG.md`
  - 3 vollständige Beispiele
  - Workflow-Erklärung
  - Alle Befehle
  - Best Practices
  - Tipps & Tricks

- **Vorlagen**: `docs/VORLAGEN.md`
  - Audit-Kits (Windows + macOS)
  - Plan-Vorlagen
  - Ausführungs-Vorlagen
  - Beispiel-Fälle

---

## 🔑 API Key Setup

Falls noch nicht gemacht:

1. Gehe zu: https://console.anthropic.com/
2. Erstelle Account / Login
3. "API Keys" → "Create Key"
4. Kopiere Key (beginnt mit `sk-ant-api03-...`)
5. Öffne `.env` Datei im Projektverzeichnis
6. Trage ein: `ANTHROPIC_API_KEY=sk-ant-api03-xxx...`
7. Speichern

---

## 💡 Wichtigste Regeln

### ✅ DO

- **Backup haben** bevor du startest
- **Output komplett kopieren** (nicht nur Teile)
- **Schritte einzeln freigeben** (GO REPAIR: 1)
- **Plan lesen** bevor du GO REPAIR gibst

### ❌ DON'T

- **Keine Freigabe ohne Plan** zu verstehen
- **Nicht alle Schritte blind freigeben**
- **Keine Admin-Rechte** wenn nicht nötig
- **Session nicht unterbrechen**

---

## 🆘 Hilfe

**Bot startet nicht?**
→ Siehe `docs/INSTALLATION.md` Troubleshooting

**API Key fehlt?**
→ `.env` Datei prüfen: `cat .env` (macOS) / `type .env` (Windows)

**Bot macht nichts?**
→ Schreibe "Neuer Fall" um zu starten

**Weitere Fragen?**
→ Siehe `docs/NUTZUNGSANLEITUNG.md` FAQ

---

## 📞 Support

- Installation: `docs/INSTALLATION.md`
- Nutzung: `docs/NUTZUNGSANLEITUNG.md`
- Vorlagen: `docs/VORLAGEN.md`
- Tests: `TEST_RESULTS.md`

---

**Los geht's!** 🚀

```bash
# Windows
.\venv\Scripts\activate
techcare

# macOS
source venv/bin/activate
techcare
```
