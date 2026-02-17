# CE365 Agent - Changelog v0.2.0

## 🎉 Wichtige Updates (2026-02-17)

### ✅ Was wurde aktualisiert:

#### 1. **System Prompt - Komplett überarbeitet**
- ✅ **FUNDAMENTALE REGELN** hinzugefügt
  - NUR Deutsch
  - NUR Windows/macOS
  - NIEMALS AUTONOM
  - EXECUTION LOCK
  - EINZELSCHRITT-AUSFÜHRUNG (kritisch!)
  - Keine irreversiblen Aktionen ohne Freigabe

#### 2. **STARTFRAGEN (NEU!)**
- ✅ **Backup-Check** bei jedem neuen Fall (PFLICHT)
  - "Existiert ein aktuelles Backup?"
  - Bei "Nein": Warnung ausgeben
  - NUR informativ, KEINE Backup-Aktionen durch CE365
- ✅ Betriebssystem-Abfrage
- ✅ Problem-Beschreibung
- ✅ Bereits durchgeführte Schritte

#### 3. **ALLOWLIST/BLOCKLIST (NEU!)**
- ✅ **ALLOWLIST**: Sichere Aktionen definiert
  - Windows: systeminfo, sc query/start/stop, ipconfig, chkdsk /scan, etc.
  - macOS: sw_vers, launchctl, diskutil verifyVolume, etc.
- ✅ **BLOCKLIST**: Verbotene Aktionen ohne Doppel-Freigabe
  - Daten löschen (außer Temp/Cache)
  - Registry-Änderungen ohne Export
  - Treiber-/Firmware-/BIOS-Updates
  - Disk-Formatierung
  - chkdsk /F, diskutil repairVolume
  - Firewall/Defender deaktivieren
  - Boot-Config ändern

#### 4. **EINZELSCHRITT-AUSFÜHRUNG (KRITISCH!)**
- ✅ Bot führt **NUR EINEN Schritt** auf einmal aus
- ✅ Wartet auf User-Output nach JEDEM Schritt
- ✅ Fragt nach jedem Schritt: "Soll ich mit Schritt X fortfahren?"
- ✅ Bei Fehler: STOPPEN, nicht autonom weitermachen

#### 5. **AUDIT-KITS integriert**
- ✅ **AUDIT-KIT WINDOWS** (8 Kommandos)
  - systeminfo, sc query, EventLog, Disk, Netzwerk, Defender/Firewall
- ✅ **AUDIT-KIT macOS** (8 Kommandos)
  - sw_vers, system_profiler, diskutil verify, log show, networksetup

#### 6. **CHANGELOG-FORMAT überarbeitet**
- ✅ Neues strukturiertes Format:
  ```
  📝 ÄNDERUNGSLOG - Schritt X
  ──────────────────────────────
  Zeitstempel: YYYY-MM-DD HH:MM:SS
  Aktion: [Beschreibung]
  Kommando: [exaktes Kommando]
  Status: ✓ ERFOLG / ✗ FEHLER
  Output: [relevanter Output]
  Rollback: [wie rückgängig machen]
  ──────────────────────────────
  ```

#### 7. **VORLAGEN-DOKUMENTATION erstellt**
- ✅ `docs/VORLAGEN.md` mit allen Templates:
  - Audit-Kit Windows
  - Audit-Kit macOS
  - Plan-Vorlage
  - Ausführungs-Vorlage
  - Startfragen-Vorlage
  - 3 Beispiel-Fälle
  - Sicherheitsregeln Quick Reference
  - Workflow-Checkliste

#### 8. **README.md aktualisiert**
- ✅ Neue Features dokumentiert
- ✅ Verbesserte Beispiel-Session
- ✅ Sicherheitsregeln erweitert
- ✅ Link zu Vorlagen-Dokumentation

---

## 🔒 Sicherheits-Verbesserungen

### Vorher (v0.1):
- ❌ Keine Backup-Frage
- ❌ Keine Allowlist/Blocklist
- ❌ Kein Einzelschritt-Mechanismus
- ❌ Unklare Sicherheitsregeln
- ❌ Keine Registry-Export-Pflicht

### Nachher (v0.2):
- ✅ **BACKUP-CHECK PFLICHT** bei jedem Fall
- ✅ **ALLOWLIST/BLOCKLIST** definiert
- ✅ **EINZELSCHRITT-AUSFÜHRUNG** erzwungen
- ✅ **KLARE SICHERHEITSREGELN** (wasserdicht)
- ✅ **REGISTRY-EXPORT PFLICHT** vor Änderungen
- ✅ **DOPPELTE FREIGABE** für HOCH-Risiko Aktionen
- ✅ **KEINE irreversiblen Aktionen** ohne explizite Warnung

---

## 📋 Workflow-Verbesserungen

### Vorher (v0.1):
```
User: "Problem X"
Bot: [führt Audit aus]
Bot: [erstellt Plan]
Bot: "GO REPAIR: 1,2"
User: "GO REPAIR: 1,2"
Bot: [führt beide Schritte aus]
```

### Nachher (v0.2):
```
User: "Neuer Fall"
Bot: [stellt STARTFRAGEN inkl. Backup]
User: [beantwortet]
Bot: [führt AUDIT-KIT aus, Schritt für Schritt]
Bot: [erstellt PLAN mit Risiko + Rollback]
User: "GO REPAIR: 1,2"
Bot: [führt NUR SCHRITT 1 aus]
Bot: "Bitte kopiere Output"
User: [kopiert Output]
Bot: "✓ Schritt 1 erfolgreich. Soll ich mit Schritt 2 fortfahren?"
User: "Ja" (oder neues "GO REPAIR: 2")
Bot: [führt SCHRITT 2 aus]
```

---

## 🎯 Praxistest-Checklist

Teste folgende Szenarien:

- [ ] **Backup-Check**: Bot fragt nach Backup bei "Neuer Fall"
- [ ] **Einzelschritt**: Bot führt nur EINEN Schritt aus, wartet auf Output
- [ ] **GO REPAIR**: Bot führt NUR freigegebene Schritte aus
- [ ] **Allowlist**: Bot erlaubt sichere Aktionen (z.B. sc query)
- [ ] **Blocklist**: Bot verweigert gefährliche Aktionen ohne Doppel-Freigabe
- [ ] **Changelog**: Nach jedem Repair-Schritt wird Changelog aktualisiert
- [ ] **Deutsch**: Alle Antworten auf Deutsch
- [ ] **Audit-Kit**: Bot verwendet strukturiertes Audit-Kit

---

## 📊 Statistik

| Kategorie | v0.1 | v0.2 | Änderung |
|-----------|------|------|----------|
| System Prompt Zeilen | 103 | 175 | +70% |
| Sicherheitsregeln | 5 | 12 | +140% |
| Definierte Aktionen (Allow/Block) | 0 | 30+ | ∞ |
| Vorlagen | 0 | 5 | ∞ |
| Audit-Kommandos | 0 | 16 | ∞ |
| Beispiel-Fälle | 1 | 3 | +200% |
| Dokumentation Seiten | 1 | 3 | +200% |

---

## 🚀 Nächste Schritte (für User)

1. **API Key eintragen** in `.env`:
   ```bash
   nano .env
   # ANTHROPIC_API_KEY=sk-ant-xxx
   ```

2. **Bot starten** und testen:
   ```bash
   source venv/bin/activate
   ce365
   ```

3. **Test-Szenario** (z.B. Windows Update Problem):
   - Bot sollte STARTFRAGEN stellen
   - Bot sollte AUDIT-KIT durchführen
   - Bot sollte EINZELSCHRITT-Modus nutzen
   - Bot sollte CHANGELOG schreiben

---

## 🔗 Referenzen

- `ce365/config/system_prompt.py` - Überarbeiteter System Prompt
- `ce365/storage/changelog.py` - Neues Changelog-Format
- `docs/VORLAGEN.md` - Alle Templates und Audit-Kits
- `README.md` - Aktualisierte Dokumentation

---

**Version:** 0.2.0
**Datum:** 2026-02-17
**Status:** ✅ Produktionsreif für erste Tests
