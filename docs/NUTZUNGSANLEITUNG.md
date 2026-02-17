# TechCare Bot - Nutzungsanleitung

## 🚀 Quick Start

### Bot starten

**Windows:**
```powershell
cd C:\Users\<DeinName>\Documents\TechCare-Bot
.\venv\Scripts\activate
techcare
```

**macOS:**
```bash
cd ~/Documents/TechCare-Bot
source venv/bin/activate
techcare
```

Du siehst dann:
```
╔════════════════════════════════════════╗
║                                        ║
║       🔧 TechCare Bot v0.2.0 🔧       ║
║                                        ║
║   IT-Wartungs-Assistent für            ║
║   Windows & macOS Systeme              ║
║                                        ║
╚════════════════════════════════════════╝

Workflow: Audit → Analyse → Plan → GO REPAIR → Ausführung
```

---

## 📖 Workflow-Übersicht

TechCare folgt einem **strengen 5-Phasen Workflow**:

```
1. STARTFRAGEN        → Backup? Betriebssystem? Problem?
2. AUDIT (Read-Only)  → System analysieren (keine Änderungen!)
3. DIAGNOSE           → Problem identifizieren
4. REPARATUR-PLAN     → Schritte vorschlagen
5. AUSFÜHRUNG         → Nach "GO REPAIR" Freigabe
```

**WICHTIG**: TechCare ändert **NIE autonom** etwas an deinem System!

---

## 🎯 Beispiel 1: Windows Update Problem

### Phase 1: Neuen Fall starten

```
You: Neuer Fall

TechCare:
🔧 TechCare - Neue Diagnose-Session
──────────────────────────────────────

1. Existiert ein aktuelles Backup? (Ja/Nein/Unbekannt)
2. Betriebssystem? (Windows 10/11 oder macOS)
3. Was ist das Problem?
4. Bereits versucht?
```

### Phase 2: Startfragen beantworten

```
You:
Ja, Backup vorhanden.
Windows 11.
Windows Update Fehler 0x80070002.
Neustart versucht, hat nicht geholfen.

TechCare:
✓ Backup vorhanden - gut!
✓ Windows 11 erkannt

📋 AUDIT-PHASE
──────────────

Ich benötige folgende Informationen. Bitte führe aus und kopiere Output:

Kommando 1:
systeminfo | findstr /C:"OS Name" /C:"OS Version"

[Warte auf Output...]
```

### Phase 3: Audit-Kommandos ausführen

**In PowerShell/CMD ausführen:**
```powershell
systeminfo | findstr /C:"OS Name" /C:"OS Version"
```

**Output kopieren:**
```
OS Name:                   Microsoft Windows 11 Pro
OS Version:                10.0.22621 N/A Build 22621
```

**Im Chat einfügen:**
```
You:
OS Name:                   Microsoft Windows 11 Pro
OS Version:                10.0.22621 N/A Build 22621

TechCare:
[analysiert Output]

Kommando 2:
sc query wuauserv

[Warte auf Output...]
```

### Phase 4: Reparatur-Plan

Nach allen Audit-Kommandos:

```
TechCare:
🔍 DIAGNOSE
───────────
Problem: Windows Update Service (wuauserv) läuft nicht
Root Cause: Service ist gestoppt

📋 REPARATUR-PLAN
─────────────────
Ziel: Windows Update Service reparieren

Schritt 1: Windows Update Service starten
  Risiko: NIEDRIG (reversibel)
  Kommando: sc start wuauserv
  Rollback: sc stop wuauserv

Schritt 2: SoftwareDistribution-Cache leeren
  Risiko: NIEDRIG (wird neu erstellt)
  Kommando: rd /s /q C:\Windows\SoftwareDistribution\Download
  Rollback: Automatisch beim nächsten Update

──────────────────────────────────────
Bitte bestätige mit: GO REPAIR: 1,2
──────────────────────────────────────
```

### Phase 5: Freigabe und Ausführung

```
You: GO REPAIR: 1

TechCare:
✓ Freigabe erhalten für Schritt 1

🔧 AUSFÜHRUNG - Schritt 1
─────────────────────────
Aktion: Windows Update Service starten
Kommando: sc start wuauserv

Erfolgskriterium: "STATE: RUNNING"
Fehlerkriterium: "ERROR" im Output

Bitte führe aus und kopiere Output:
sc start wuauserv
```

**Kommando ausführen:**
```powershell
sc start wuauserv
```

**Output:**
```
SERVICE_NAME: wuauserv
        TYPE               : 20  WIN32_SHARE_PROCESS
        STATE              : 2  START_PENDING
        ...
        STATE              : 4  RUNNING
```

**Im Chat einfügen:**
```
You:
[Output kopiert]

TechCare:
✓ Schritt 1 erfolgreich!

📝 ÄNDERUNGSLOG - Schritt 1
──────────────────────────────
Zeitstempel: 2026-02-17 14:35:12
Aktion: Windows Update Service gestartet
Kommando: sc start wuauserv
Status: ✓ ERFOLG
Output: STATE: RUNNING
Rollback: sc stop wuauserv
──────────────────────────────

Schritt 2 wurde nicht freigegeben.
Soll ich mit Schritt 2 fortfahren? (benötigt GO REPAIR: 2)
```

---

## 🎯 Beispiel 2: macOS WLAN/DNS Problem

### Vollständiger Dialog

```
You: Neuer Fall

TechCare:
[Startfragen...]

You:
Ja, Time Machine Backup.
macOS Sequoia 15.
WLAN verbunden, aber Websites laden nicht.
Neustart versucht.

TechCare:
✓ Backup vorhanden
✓ macOS Sequoia 15 erkannt

📋 AUDIT-PHASE
──────────────

Kommando 1: sw_vers

You:
[führt aus und kopiert Output]

TechCare:
Kommando 2: networksetup -listallnetworkservices

You:
[führt aus und kopiert Output]

TechCare:
Kommando 3: scutil --dns

You:
[führt aus und kopiert Output]

TechCare:
🔍 DIAGNOSE
───────────
Problem: DNS-Auflösung schlägt fehl
Root Cause: DNS-Cache korrupt

📋 REPARATUR-PLAN
─────────────────

Schritt 1: DNS-Cache leeren
  Risiko: NIEDRIG (ungefährlich)
  Kommando: sudo dscacheutil -flushcache
  Rollback: Nicht nötig (Cache baut sich neu auf)

Bitte bestätige mit: GO REPAIR: 1

You: GO REPAIR: 1

TechCare:
🔧 AUSFÜHRUNG - Schritt 1
Kommando: sudo dscacheutil -flushcache

[User führt aus, gibt Passwort ein]

You:
[kein Output = erfolgreich]

TechCare:
✓ Schritt 1 erfolgreich!
DNS-Cache wurde geleert. Teste jetzt, ob Websites laden.
```

---

## 🎯 Beispiel 3: Drucker-Problem (Windows)

```
You: Neuer Fall

TechCare: [Startfragen...]

You:
Ja Backup.
Windows 11.
Druckaufträge hängen, nichts druckt.
Drucker neu gestartet.

TechCare:
📋 AUDIT-PHASE
Kommando 1: sc query Spooler

You: [Output]

TechCare:
Kommando 2: Get-PrintJob -PrinterName * | Format-Table

You: [Output]

TechCare:
🔍 DIAGNOSE
Problem: Spooler Service läuft, aber Warteschlange blockiert
Root Cause: Hängender Druckauftrag

📋 REPARATUR-PLAN

Schritt 1: Spooler Service stoppen
  Risiko: NIEDRIG
  Kommando: net stop Spooler

Schritt 2: Druckwarteschlange leeren
  Risiko: NIEDRIG (Druckaufträge gehen verloren!)
  Kommando: del /q /f /s %systemroot%\System32\spool\PRINTERS\*

Schritt 3: Spooler Service starten
  Risiko: NIEDRIG
  Kommando: net start Spooler

Bitte bestätige mit: GO REPAIR: 1,2,3

You: GO REPAIR: 1-3

TechCare:
[Führt Schritt 1 aus, wartet auf Output]
[Führt Schritt 2 aus, wartet auf Output]
[Führt Schritt 3 aus, wartet auf Output]

✓ Alle Schritte abgeschlossen!
```

---

## 💡 Wichtige Befehle

### GO REPAIR Befehle

```bash
GO REPAIR: 1          # Nur Schritt 1
GO REPAIR: 1,2,3      # Schritte 1, 2 und 3
GO REPAIR: 1-3        # Schritte 1 bis 3 (Range)
GO REPAIR: 1,3-5,7    # Gemischt: 1, 3, 4, 5, 7
```

**WICHTIG**:
- TechCare führt **nur freigegebene Schritte** aus
- TechCare führt **nur EINEN Schritt auf einmal** aus
- Nach jedem Schritt wartet TechCare auf deinen Output

### Session-Befehle

```bash
exit      # Session beenden
quit      # Session beenden
q         # Session beenden
```

---

## 📋 Workflow-Checkliste

### Für jeden Fall:

- [ ] **Backup-Check**: Hat TechCare nach Backup gefragt?
- [ ] **Betriebssystem**: Hat TechCare OS erkannt?
- [ ] **Audit-Phase**: Hat TechCare Kommandos einzeln gegeben?
- [ ] **Nach Output gefragt**: Hat TechCare auf Output gewartet?
- [ ] **Diagnose**: Hat TechCare Root Cause erklärt?
- [ ] **Plan mit Risiko**: Hat TechCare Risiko angegeben?
- [ ] **Rollback-Option**: Hat TechCare Rollback erklärt?
- [ ] **GO REPAIR gefordert**: Hat TechCare explizit gefragt?
- [ ] **Einzelschritt**: Hat TechCare nur 1 Schritt ausgeführt?
- [ ] **Changelog**: Hat TechCare Änderungslog geschrieben?

---

## 🚨 Was TechCare NIEMALS tut

❌ **Autonome Änderungen** - Keine Reparaturen ohne GO REPAIR
❌ **Mehrere Schritte parallel** - Immer nur 1 Schritt
❌ **Daten löschen** (außer Temp/Cache nach Freigabe)
❌ **Registry ändern** (ohne Export)
❌ **Treiber-Updates** (ohne Freigabe)
❌ **BIOS/Firmware-Updates** (ohne Freigabe)
❌ **Firewall deaktivieren**
❌ **Backup erstellen** (nur informativ fragen)

✅ **Was TechCare macht:**
- Startfragen stellen (inkl. Backup-Check)
- System analysieren (Read-Only)
- Diagnose erstellen
- Plan vorschlagen (mit Risiko + Rollback)
- Nach GO REPAIR warten
- Schritte einzeln ausführen (nach Output warten)
- Changelog schreiben

---

## 🔍 Tipps & Tricks

### 1. Audit-Kommandos effizient ausführen

**Windows PowerShell:**
```powershell
# Alle Kommandos in einer Datei speichern
notepad audit.ps1

# Ausführen und Output in Datei
.\audit.ps1 > output.txt

# Output kopieren
type output.txt
```

**macOS Terminal:**
```bash
# Alle Kommandos in einer Datei
nano audit.sh

# Ausführen und Output speichern
bash audit.sh > output.txt

# Output kopieren
cat output.txt
```

### 2. Output schnell kopieren

**Windows:**
- PowerShell: Markieren → Rechtsklick → Kopiert automatisch
- CMD: Markieren → Enter

**macOS:**
- Terminal: Cmd+C (nach Markierung)

### 3. Lange Outputs kürzen

Falls Output zu lang:
```
TechCare fragt: "Bitte kopiere Output"

Du kannst sagen:
"Output ist sehr lang, soll ich nur relevante Zeilen kopieren?"

TechCare wird dir sagen, welche Zeilen wichtig sind.
```

### 4. Session unterbrochen?

Falls TechCare-Session abbricht:
```bash
# Changelog anschauen
cat data/changelogs/<session-id>.json

# Zeigt alle durchgeführten Schritte
```

### 5. Bei Unsicherheit

```
You: Ist Schritt X sicher?

TechCare wird erklären:
- Was genau passiert
- Welches Risiko besteht
- Wie man es rückgängig macht
```

---

## 📊 Changelog ansehen

Nach jeder Session:

**Windows:**
```powershell
type data\changelogs\<session-id>.json
```

**macOS:**
```bash
cat data/changelogs/<session-id>.json
```

Format:
```json
{
  "session_id": "...",
  "created_at": "2026-02-17T14:30:00",
  "entries": [
    {
      "timestamp": "2026-02-17T14:35:12",
      "tool_name": "manage_service",
      "tool_input": {"service": "wuauserv", "action": "restart"},
      "result": "✓ Erfolg",
      "success": true
    }
  ]
}
```

---

## 🆘 Häufige Fragen

### Q: TechCare macht nichts ohne meine Freigabe?
**A**: Korrekt! TechCare führt **NIE** autonome Änderungen durch. Immer erst "GO REPAIR" abwarten.

### Q: Kann ich einzelne Schritte überspringen?
**A**: Ja! `GO REPAIR: 1,3` führt nur Schritt 1 und 3 aus, überspringt Schritt 2.

### Q: Was passiert bei Fehlern?
**A**: TechCare stoppt sofort, analysiert Fehler, schlägt neuen Plan vor.

### Q: Werden meine Daten gelöscht?
**A**: Nur nach expliziter GO REPAIR Freigabe für Temp/Cache. Niemals User-Daten.

### Q: Brauche ich Administrator-Rechte?
**A**: Für manche Reparaturen (Services, System-Befehle) ja. TechCare warnt vorher.

### Q: Kann ich mehrere Sessions parallel?
**A**: Nein, immer nur eine Session gleichzeitig. Jede Session bekommt eigenes Changelog.

### Q: Kostet der API-Call Geld?
**A**: Ja, Anthropic berechnet nach Token-Usage. Ca. 3000-10000 Tokens pro Fall (ca. $0.03-$0.10).

---

## 🎓 Best Practices

### DO ✅

- **Backup vorhanden**: Immer "Ja" bei Backup-Frage (falls möglich)
- **Detaillierte Problem-Beschreibung**: Je mehr Info, desto besser
- **Output komplett kopieren**: Nicht nur Auszüge
- **Schrittweise freigeben**: Erst Schritt 1, dann entscheiden ob weiter
- **Changelog prüfen**: Nach Session anschauen was geändert wurde

### DON'T ❌

- **GO REPAIR ohne Plan lesen**: Immer erst Plan verstehen!
- **Alle Schritte blind freigeben**: Lieber einzeln
- **Output erfinden**: Immer echten Output kopieren
- **Admin-Rechte bei allem**: Nur wenn nötig
- **Session unterbrechen**: Immer mit `exit` beenden

---

## 📱 Support

Bei Problemen:
1. Schaue in `docs/INSTALLATION.md` (Troubleshooting)
2. Prüfe `TEST_RESULTS.md`
3. Lies `docs/VORLAGEN.md` für Beispiele
4. Erstelle GitHub Issue

---

**Viel Erfolg mit TechCare Bot!** 🚀
