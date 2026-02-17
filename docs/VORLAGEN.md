# TechCare Bot - Vorlagen & Audit-Kits

## AUDIT-KIT WINDOWS

**Nach jedem Kommando: "Bitte kopiere den Output hier ein"**

### Kommando 1: System-Informationen
```cmd
systeminfo | findstr /C:"OS Name" /C:"OS Version" /C:"System Boot Time" /C:"Total Physical Memory"
```

### Kommando 2: Windows Update Service Status
```cmd
sc query wuauserv
```

### Kommando 3: Kritische Eventlog-Einträge (letzte 24h)
```powershell
Get-EventLog -LogName System -EntryType Error,Warning -Newest 20 | Format-Table -AutoSize
```

### Kommando 4: Disk-Status (Speicherplatz)
```cmd
wmic logicaldisk get caption,freespace,size,volumename
```

### Kommando 5: Netzwerk-Status
```cmd
ipconfig /all
```

### Kommando 6: Defender/Firewall Status
```powershell
Get-MpComputerStatus | Select-Object AntivirusEnabled,RealTimeProtectionEnabled
netsh advfirewall show allprofiles state
```

### Kommando 7: Laufende Services (gefiltert)
```cmd
sc query type= service state= all | findstr /C:"STOPPED" /C:"wuauserv" /C:"Spooler" /C:"Dnscache"
```

### Kommando 8: Temp-Ordner Größe
```cmd
dir %TEMP% /s | findstr /C:"File(s)" /C:"Dir(s)"
```

---

## AUDIT-KIT macOS

**Nach jedem Kommando: "Bitte kopiere den Output hier ein"**

### Kommando 1: System-Version
```bash
sw_vers
```

### Kommando 2: System-Profil (Übersicht)
```bash
system_profiler SPSoftwareDataType SPHardwareDataType
```

### Kommando 3: Disk-Status (nur Verify!)
```bash
diskutil verifyVolume /
```

### Kommando 4: Kritische Log-Einträge (letzte 1h)
```bash
log show --predicate 'eventMessage contains "error" OR eventMessage contains "fail"' --info --last 1h | head -50
```

### Kommando 5: Netzwerk-Status
```bash
networksetup -listallnetworkservices
scutil --dns | head -20
```

### Kommando 6: Speicherplatz
```bash
df -h
```

### Kommando 7: Laufende Services (launchd)
```bash
launchctl list | grep -i "com.apple"
```

### Kommando 8: Cache-Größe
```bash
du -sh ~/Library/Caches
```

---

## PLAN-VORLAGE

```markdown
# REPARATUR-PLAN
──────────────────────────────────────

**Ziel:** [Kurze Beschreibung des Ziels]

**Diagnose:** [Root Cause in 1-2 Sätzen]

## Schritte

### Schritt 1: [Beschreibung]
- **Risiko:** NIEDRIG / MITTEL / HOCH
- **Kommando:** `[exaktes Kommando]`
- **Erwartetes Ergebnis:** [Was sollte passieren]
- **Rollback:** [Wie rückgängig machen]

### Schritt 2: [Beschreibung]
- **Risiko:** NIEDRIG / MITTEL / HOCH
- **Kommando:** `[exaktes Kommando]`
- **Erwartetes Ergebnis:** [Was sollte passieren]
- **Rollback:** [Wie rückgängig machen]

### Schritt 3: [Beschreibung]
- **Risiko:** NIEDRIG / MITTEL / HOCH
- **Kommando:** `[exaktes Kommando]`
- **Erwartetes Ergebnis:** [Was sollte passieren]
- **Rollback:** [Wie rückgängig machen]

──────────────────────────────────────
**Bitte bestätige mit:** `GO REPAIR: 1,2,3`
(oder einzelne Schritte: `GO REPAIR: 1` oder `GO REPAIR: 1,3`)

**Hinweis:** TechCare führt Schritte EINZELN aus. Nach jedem Schritt warte ich auf deinen Output.
──────────────────────────────────────
```

---

## AUSFÜHRUNGS-VORLAGE

```markdown
# 🔧 AUSFÜHRUNG - Schritt X
─────────────────────────────────────

**Aktion:** [Kurze Beschreibung]

**Kommando:**
```
[exaktes Kommando zum Copy/Paste]
```

**Erfolgskriterium:** [Was im Output erscheinen sollte bei Erfolg]
**Fehlerkriterium:** [Was im Output auf Fehler hinweist]

**Bitte führe das Kommando aus und kopiere den KOMPLETTEN Output hier ein.**

─────────────────────────────────────

[Nach Output vom Benutzer:]

✓ **Schritt X erfolgreich!** / ✗ **Schritt X fehlgeschlagen!**

## 📝 ÄNDERUNGSLOG - Schritt X
──────────────────────────────
Zeitstempel: [YYYY-MM-DD HH:MM:SS]
Aktion: [Beschreibung]
Kommando: [Kommando]
Status: ✓ ERFOLG / ✗ FEHLER
Output: [relevanter Output]
Rollback: [wie rückgängig machen]
──────────────────────────────

[Falls Erfolg:] Soll ich mit Schritt X+1 fortfahren? (benötigt GO REPAIR: X+1)
[Falls Fehler:] STOPP! Fehleranalyse: [Erklärung]. Neuer Plan erforderlich?
```

---

## STARTFRAGEN-VORLAGE

```markdown
🔧 TechCare - Neue Diagnose-Session
──────────────────────────────────────

Bitte beantworte folgende Fragen:

1. **Backup-Status:** Existiert ein aktuelles Backup? (Ja/Nein/Unbekannt)
2. **Betriebssystem:** Welches System? (Windows 10/11 oder macOS 13+/14+/15+)
3. **Problem:** Was ist das konkrete Problem? Fehlermeldungen?
4. **Bereits versucht:** Wurde bereits etwas versucht?

──────────────────────────────────────
```

---

## BEISPIEL-FÄLLE

### Fall 1: Windows Update hängt (Fehler 0x80070002)

```markdown
User: "Windows Update Fehler 0x80070002"

TechCare:
🔧 TechCare - Neue Diagnose-Session
──────────────────────────────────────
1. Existiert ein aktuelles Backup? (Ja/Nein/Unbekannt)
2. Betriebssystem? (Windows 10/11)
3. Tritt der Fehler bei jedem Update auf?
4. Bereits etwas versucht?

User: "Ja Backup, Windows 11, ja bei jedem Update, Neustart brachte nichts"

TechCare:
✓ Backup vorhanden - gut!
✓ Windows 11 erkannt

📋 AUDIT-PHASE
──────────────
Kommando 1: systeminfo | findstr /C:"OS Name" /C:"OS Version"
[Warte auf Output...]

Kommando 2: sc query wuauserv
[Warte auf Output...]

[usw.]
```

### Fall 2: Drucker Spooler hängt (Windows)

```markdown
User: "Druckaufträge hängen"

TechCare:
🔧 TechCare - Neue Diagnose-Session
──────────────────────────────────────
1. Backup? (Ja/Nein/Unbekannt)
2. Betriebssystem?
3. Welcher Drucker?
4. Seit wann?

User: "Backup ja, Windows 11, HP LaserJet"

TechCare:
✓ Backup vorhanden

📋 AUDIT-PHASE
──────────────
Kommando 1: sc query Spooler
[Warte auf Output...]

[usw.]
```

### Fall 3: WLAN/DNS Probleme (macOS)

```markdown
User: "macOS, Websites laden nicht"

TechCare:
🔧 TechCare - Neue Diagnose-Session
──────────────────────────────────────
1. Time Machine Backup? (Ja/Nein)
2. macOS Version?
3. Funktioniert ping 8.8.8.8?
4. Andere Geräte betroffen?

User: "Backup ja, Sequoia 15, ping geht"

TechCare:
✓ Backup vorhanden
Hinweis: Ping OK → wahrscheinlich DNS-Problem

📋 AUDIT-PHASE
──────────────
Kommando 1: sw_vers
[Warte auf Output...]

Kommando 2: scutil --dns
[Warte auf Output...]

[usw.]
```

---

## SICHERHEITSREGELN - QUICK REFERENCE

### ✅ ALLOWLIST (sichere Aktionen)

**Windows:**
- `systeminfo`, `Get-ComputerInfo`
- `sc query`, `sc start/stop/restart`
- `ipconfig /all`, `/flushdns`
- `chkdsk /scan` (nur Scan!)
- `sfc /verifyonly`
- Temp-Ordner leeren

**macOS:**
- `sw_vers`, `system_profiler`
- `launchctl list/start/stop`
- `diskutil verifyVolume` (nur Verify!)
- `dscacheutil -flushcache`
- `~/Library/Caches/*` leeren

### ❌ BLOCKLIST (Doppel-Freigabe erforderlich)

- Daten löschen (außer Temp/Cache)
- Registry-Änderungen ohne Export
- Treiber-/Firmware-/BIOS-Updates
- Disk-Formatierung
- `chkdsk /F`, `diskutil repairVolume`
- Kritische Services beenden
- Firewall/Defender deaktivieren
- Boot-Config ändern

---

## WORKFLOW-CHECKLISTE

- [ ] Startfragen gestellt (inkl. Backup-Frage)
- [ ] Audit-Kit vollständig durchgeführt
- [ ] Root Cause identifiziert (nicht nur Symptome)
- [ ] Reparatur-Plan mit Risiko + Rollback erstellt
- [ ] GO REPAIR Freigabe abgewartet
- [ ] Einzelschritte ausgeführt (nicht mehrere parallel)
- [ ] Nach jedem Schritt auf Output gewartet
- [ ] Changelog aktualisiert
- [ ] Bei Fehler gestoppt (nicht autonom weitergemacht)
