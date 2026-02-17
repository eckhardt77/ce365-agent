# CE365 Agent - Tool Roadmap

## Ziel
CE365 soll ein **vollständiger IT-Wartungsassistent** sein der:
- Analysiert
- Optimiert
- Updated
- Fehler behebt
- Repariert

## Tool-Kategorien

### 1. AUDIT TOOLS (Read-Only)
Sammeln Informationen ohne System zu ändern

### 2. REPAIR TOOLS (mit Freigabe)
Ändern System-Einstellungen

### 3. OPTIMIZATION TOOLS (mit Freigabe)
Verbessern Performance

### 4. UPDATE TOOLS (mit Freigabe)
Installieren Updates

---

## 🪟 Windows Tools

### ✅ Bereits implementiert:
- [x] `get_system_info` - System-Informationen (OS, CPU, RAM, Disk)
- [x] `manage_service` - Service Start/Stop/Restart

### 📊 AUDIT TOOLS (neu)

| Tool | Beschreibung | Kommando | Priorität |
|------|--------------|----------|-----------|
| `check_event_logs` | Windows Event Viewer Fehler der letzten 24h | `Get-EventLog -LogName System -EntryType Error -Newest 50` | **HOCH** |
| `check_running_processes` | Prozesse mit hoher CPU/RAM-Nutzung | `Get-Process \| Sort-Object CPU -Descending` | **HOCH** |
| `check_startup_programs` | Autostart-Programme auflisten | `Get-CimInstance Win32_StartupCommand` | MITTEL |
| `check_disk_health` | Disk-Status mit SMART | `Get-PhysicalDisk \| Get-StorageReliabilityCounter` | HOCH |
| `check_network_config` | Netzwerk-Adapter, IP, DNS | `ipconfig /all` + `Get-NetAdapter` | MITTEL |
| `check_windows_update` | Verfügbare Updates | `Get-WindowsUpdate` (PSWindowsUpdate) | **HOCH** |
| `check_firewall_status` | Windows Firewall Status | `Get-NetFirewallProfile` | MITTEL |
| `check_defender_status` | Windows Defender Status & Scan-Datum | `Get-MpComputerStatus` | MITTEL |

### 🔧 REPAIR TOOLS (neu)

| Tool | Beschreibung | Kommando | Priorität |
|------|--------------|----------|-----------|
| `run_sfc_scan` | System File Check | `sfc /scannow` | **HOCH** |
| `run_dism_repair` | Windows Image Repair | `DISM /Online /Cleanup-Image /RestoreHealth` | **HOCH** |
| `repair_windows_update` | Windows Update Service reparieren | Reset wuauserv, cryptsvc, bits | **HOCH** |
| `flush_dns_cache` | DNS Cache leeren | `ipconfig /flushdns` | MITTEL |
| `reset_network_stack` | Netzwerk-Stack zurücksetzen | `netsh winsock reset` + `netsh int ip reset` | MITTEL |
| `repair_windows_store` | Microsoft Store reparieren | `wsreset.exe` | NIEDRIG |

### ⚡ OPTIMIZATION TOOLS (neu)

| Tool | Beschreibung | Kommando | Priorität |
|------|--------------|----------|-----------|
| `cleanup_disk` | Temp-Dateien löschen | `cleanmgr.exe` + Disk Cleanup API | **HOCH** |
| `disable_startup_program` | Autostart-Programm deaktivieren | Registry: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` | MITTEL |
| `optimize_power_plan` | Power-Plan auf "Höchstleistung" | `powercfg /setactive SCHEME_MIN` | NIEDRIG |

### 🔄 UPDATE TOOLS (neu)

| Tool | Beschreibung | Kommando | Priorität |
|------|--------------|----------|-----------|
| `install_windows_updates` | Windows Updates installieren | `Install-WindowsUpdate -AcceptAll` | **HOCH** |

---

## 🍎 macOS Tools

### ✅ Bereits implementiert:
- [x] `get_system_info` - System-Informationen (OS, CPU, RAM, Disk)
- [x] `manage_service` - LaunchAgent/LaunchDaemon Management

### 📊 AUDIT TOOLS (neu)

| Tool | Beschreibung | Kommando | Priorität |
|------|--------------|----------|-----------|
| `check_system_logs` | System-Logs der letzten 24h | `log show --predicate 'eventMessage contains "error"' --last 24h` | **HOCH** |
| `check_running_processes` | Prozesse mit hoher CPU/RAM | `ps aux \| sort -k 3 -r` | **HOCH** |
| `check_login_items` | Login Items (Autostart) | `osascript -e 'tell application "System Events" to get name of every login item'` | MITTEL |
| `check_disk_health` | Disk-Status mit SMART | `diskutil info disk0` + `smartctl` | HOCH |
| `check_network_config` | Netzwerk-Config | `networksetup -listallnetworkservices` | MITTEL |
| `check_software_updates` | Verfügbare Updates | `softwareupdate -l` | **HOCH** |
| `check_time_machine` | Time Machine Backup-Status | `tmutil latestbackup` + `tmutil destinationinfo` | MITTEL |
| `check_spotlight_status` | Spotlight Indexing-Status | `mdutil -s /` | NIEDRIG |

### 🔧 REPAIR TOOLS (neu)

| Tool | Beschreibung | Kommando | Priorität |
|------|--------------|----------|-----------|
| `repair_disk_permissions` | Disk Permissions reparieren | `diskutil resetUserPermissions / $(id -u)` | **HOCH** |
| `repair_disk` | First Aid auf Disk | `diskutil repairVolume /` | **HOCH** |
| `rebuild_spotlight` | Spotlight-Index neu aufbauen | `mdutil -E /` | MITTEL |
| `flush_dns_cache` | DNS Cache leeren | `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder` | MITTEL |
| `reset_smc` | SMC Reset (Anleitung) | Anleitung je nach Mac-Modell | NIEDRIG |
| `reset_nvram` | NVRAM/PRAM Reset (Anleitung) | Anleitung für Neustart | NIEDRIG |

### ⚡ OPTIMIZATION TOOLS (neu)

| Tool | Beschreibung | Kommando | Priorität |
|------|--------------|----------|-----------|
| `cleanup_caches` | System & User Caches löschen | `rm -rf ~/Library/Caches/*` (mit Whitelist) | **HOCH** |
| `cleanup_logs` | Alte Log-Dateien löschen | `rm -rf ~/Library/Logs/*` (älter als 30 Tage) | MITTEL |
| `remove_login_item` | Login Item entfernen | `osascript` + System Events | MITTEL |
| `purge_memory` | RAM freigeben | `sudo purge` | NIEDRIG |

### 🔄 UPDATE TOOLS (neu)

| Tool | Beschreibung | Kommando | Priorität |
|------|--------------|----------|-----------|
| `install_macos_updates` | macOS Updates installieren | `softwareupdate -i -a` | **HOCH** |

---

## 🧠 Intelligenz-Features

### Best Practices in System Prompt

CE365 soll **automatisch wissen** was zu tun ist bei:

1. **Langsames System**
   - Prozesse prüfen
   - Autostart-Programme checken
   - Disk Cleanup vorschlagen

2. **Windows Update Fehler**
   - Windows Update Service Status prüfen
   - Event Logs nach Fehler-Code suchen
   - Bekannte Fix-Procedures (z.B. 0x80070002 → Reset wuauserv)

3. **Netzwerk-Probleme**
   - DNS Cache leeren
   - Netzwerk-Stack Reset
   - Netzwerk-Config prüfen

4. **Disk-Probleme**
   - SMART-Status prüfen
   - Disk Cleanup
   - (Windows) chkdsk vorschlagen
   - (macOS) First Aid

5. **Startup-Probleme**
   - Autostart-Programme prüfen
   - Services checken
   - Event Logs analysieren

### Error-Code Datenbank

Häufige Error-Codes mit Fix-Procedure:

**Windows:**
- `0x80070002` → Windows Update: Reset wuauserv + SoftwareDistribution löschen
- `0x80070005` → Access Denied: Permissions prüfen, Administrator-Rechte
- `0x80004005` → Unspecified Error: Oft Registry/Permissions
- `0xc000021a` → Critical Process Died: Safe Mode → SFC /scannow

**macOS:**
- `-43` → File not found
- `-36` → I/O Error: Disk prüfen
- `-8003` → Invalid Argument

---

## Implementierungs-Plan

### Phase 1: Core Audit Tools (HEUTE)
- [x] `get_system_info` (bereits da)
- [ ] `check_event_logs` (Windows)
- [ ] `check_system_logs` (macOS)
- [ ] `check_running_processes` (beide)
- [ ] `check_disk_health` (beide)

### Phase 2: Core Repair Tools
- [ ] `run_sfc_scan` (Windows)
- [ ] `repair_disk_permissions` (macOS)
- [ ] `flush_dns_cache` (beide)
- [ ] `cleanup_disk` (beide)

### Phase 3: Update Management
- [ ] `check_windows_update` + `install_windows_updates`
- [ ] `check_software_updates` + `install_macos_updates`

### Phase 4: Advanced Tools
- [ ] `run_dism_repair` (Windows)
- [ ] `rebuild_spotlight` (macOS)
- [ ] `reset_network_stack` (Windows)
- [ ] Alle anderen Tools

### Phase 5: Intelligenz
- [ ] Error-Code Datenbank in System Prompt
- [ ] Best Practices für häufige Probleme
- [ ] Automatic Diagnosis Flow

---

## Technische Details

### Tool-Struktur

Jedes Tool hat:
```python
class MyTool(AuditTool):  # oder RepairTool
    @property
    def name(self) -> str:
        return "tool_name"

    @property
    def description(self) -> str:
        return "Was macht das Tool (für Claude)"

    @property
    def input_schema(self) -> dict:
        return {...}

    async def execute(self, **kwargs) -> str:
        # Platform Detection
        if platform.system() == "Windows":
            # Windows-Kommando
        elif platform.system() == "Darwin":
            # macOS-Kommando
        else:
            return "Unsupported OS"
```

### Safety

- **Audit Tools**: Immer erlaubt (Read-Only)
- **Repair Tools**: Nur nach GO REPAIR
- **Destructive Actions**: Immer mit Rollback-Plan
- **Permissions**: Prüfen ob sudo/admin nötig

---

## Prioritäten

**HOCH (sofort implementieren):**
1. Event/System Logs
2. Prozess-Check
3. SFC/Disk Repair
4. Disk Cleanup
5. Windows/macOS Updates

**MITTEL (nach Phase 1):**
- Netzwerk-Tools
- Startup-Management
- Firewall/Defender

**NIEDRIG (optional):**
- SMC/NVRAM Reset
- Power Plans
- Windows Store Repair
