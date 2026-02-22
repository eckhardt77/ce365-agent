"""
CE365 Agent - Memory Dump Analysis Tool

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Analysiert Windows Minidumps und macOS Panic-Logs:
- Dump-Dateien finden und auflisten
- Bugcheck-Codes aus Event-Log extrahieren
- Ursachen-Analyse mit Empfehlungen
- Crash-Frequenz und Korrelation mit Kernel-Power Events
"""

import platform
from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.core.command_runner import get_command_runner


def _run_cmd(cmd: list, timeout: int = 15) -> str:
    result = get_command_runner().run_sync(cmd, timeout=timeout)
    return result.stdout


# Bekannte Bugcheck-Codes mit Klartext und Empfehlung
BUGCHECK_DB = {
    "0x0000000A": {
        "name": "IRQL_NOT_LESS_OR_EQUAL",
        "cause": "Treiber-Problem: Faulty Driver versucht auf gesperrten Speicher zuzugreifen",
        "action": "Treiber-Updates pruefen, zuletzt installierte Treiber zurueckrollen",
    },
    "0x0000001E": {
        "name": "KMODE_EXCEPTION_NOT_HANDLED",
        "cause": "Kernel-Mode-Fehler: Treiber oder Systemkomponente hat unbehandelte Exception ausgeloest",
        "action": "Fehlerhaften Treiber identifizieren (im Dump-Message), Treiber aktualisieren oder deinstallieren",
    },
    "0x0000003B": {
        "name": "SYSTEM_SERVICE_EXCEPTION",
        "cause": "System-Service-Fehler: Treiber oder Systemdienst hat ungueltige Operation ausgefuehrt",
        "action": "Antivirensoftware pruefen, Treiber aktualisieren, SFC /scannow ausfuehren",
    },
    "0x00000050": {
        "name": "PAGE_FAULT_IN_NONPAGED_AREA",
        "cause": "Speicher-Fehler: Zugriff auf nicht vorhandene Speicherseite",
        "action": "RAM-Test (memtest86) ausfuehren, kuerzlich installierte Software/Treiber pruefen",
    },
    "0x0000007E": {
        "name": "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED",
        "cause": "System-Thread-Fehler: Treiber hat kritische Exception nicht behandelt",
        "action": "Fehlerhaften Treiber im Dump identifizieren, Treiber aktualisieren oder entfernen",
    },
    "0x0000009F": {
        "name": "DRIVER_POWER_STATE_FAILURE",
        "cause": "Treiber-Energieproblem: Treiber reagiert nicht auf Power-State-Wechsel",
        "action": "Netzwerk- und Grafiktreiber aktualisieren, Energieoptionen pruefen",
    },
    "0x000000C2": {
        "name": "BAD_POOL_CALLER",
        "cause": "Speicherpool-Fehler: Treiber hat ungueltigen Speicherzugriff auf Kernel-Pool",
        "action": "Fehlerhaften Treiber identifizieren, Windows-Updates installieren",
    },
    "0x000000D1": {
        "name": "DRIVER_IRQL_NOT_LESS_OR_EQUAL",
        "cause": "Treiber-Speicherfehler: Treiber greift bei falschem IRQL auf Speicher zu",
        "action": "Netzwerktreiber pruefen (haeufigste Ursache), Treiber aktualisieren",
    },
    "0x000000EF": {
        "name": "CRITICAL_PROCESS_DIED",
        "cause": "Kritischer Prozess beendet: Ein fuer Windows essentieller Prozess ist abgestuerzt",
        "action": "SFC /scannow und DISM ausfuehren, System auf Malware pruefen",
    },
    "0x000000F4": {
        "name": "CRITICAL_OBJECT_TERMINATION",
        "cause": "Kritisches Objekt beendet: Ein wichtiger System-Prozess wurde unerwartet terminiert",
        "action": "Festplatten-Gesundheit pruefen, SFC ausfuehren, Kabel ueberpruefen",
    },
    "0x00000124": {
        "name": "WHEA_UNCORRECTABLE_ERROR",
        "cause": "Hardware-Fehler: CPU/RAM/Mainboard meldet unkorrigierbaren Fehler",
        "action": "RAM-Test (memtest86), CPU-Temperatur pruefen, BIOS/UEFI aktualisieren",
    },
    "0x0000012B": {
        "name": "FAULTY_HARDWARE_CORRUPTED_PAGE",
        "cause": "Defekte Hardware: RAM-Modul liefert korrupte Daten",
        "action": "RAM-Test ausfuehren, einzelne RAM-Module testen, Slots wechseln",
    },
    "0x00000133": {
        "name": "DPC_WATCHDOG_VIOLATION",
        "cause": "DPC-Timeout: Treiber braucht zu lange fuer Deferred Procedure Call",
        "action": "SSD-Firmware aktualisieren, SATA-Controller-Treiber pruefen (storahci)",
    },
    "0x00000139": {
        "name": "KERNEL_SECURITY_CHECK_FAILURE",
        "cause": "Kernel-Integritaetsfehler: Speicherkorruption oder Stack-Buffer-Overflow erkannt",
        "action": "Treiber aktualisieren, RAM testen, Windows-Updates installieren",
    },
    "0x0000013A": {
        "name": "KERNEL_MODE_HEAP_CORRUPTION",
        "cause": "Kernel-Heap-Korruption: Treiber hat Heap-Speicher beschaedigt",
        "action": "Kuerzlich installierte Treiber/Software deinstallieren, System-Dateien pruefen",
    },
    "0x00000154": {
        "name": "UNEXPECTED_STORE_EXCEPTION",
        "cause": "Speicher-Ausnahme: Unerwarteter Fehler im Speicher-Subsystem",
        "action": "Festplatten-Gesundheit pruefen, Schnellstart deaktivieren, Treiber aktualisieren",
    },
    "0x000001CA": {
        "name": "SYNTHETIC_WATCHDOG_TIMEOUT",
        "cause": "Watchdog-Timeout: System reagierte zu lange nicht (haeufig in VMs)",
        "action": "VM-Ressourcen pruefen, Host-System entlasten, Hyper-V-Treiber aktualisieren",
    },
}


class AnalyzeMemoryDumpsTool(AuditTool):
    """
    Analysiert Windows Memory-Dumps und macOS Panic-Logs
    nach Crash-Ursachen und liefert Handlungsempfehlungen.
    """

    @property
    def name(self) -> str:
        return "analyze_memory_dumps"

    @property
    def description(self) -> str:
        return (
            "Analysiert Windows Minidumps (.dmp) und macOS Panic-Logs nach Crash-Ursachen. "
            "Nutze dies bei: 1) Blue Screens (BSOD), 2) Unerwarteten Neustarts, "
            "3) System-Freezes, 4) Wiederholten Abstuerzen, "
            "5) Hardware-Verdacht (RAM/CPU/Disk). "
            "Liefert: Dump-Dateien, Bugcheck-Codes mit Klartext-Ursache, "
            "Crash-Frequenz, Kernel-Power Events und konkrete Empfehlungen."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "max_dumps": {
                    "type": "integer",
                    "description": "Anzahl der letzten Dumps/Crashes zum Analysieren (Standard: 5)",
                    "default": 5,
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        max_dumps = kwargs.get("max_dumps", 5)
        os_type = platform.system()

        if os_type == "Windows":
            return self._analyze_windows(max_dumps)
        elif os_type == "Darwin":
            return self._analyze_macos(max_dumps)
        else:
            return f"❌ Nicht unterstuetztes OS: {os_type}"

    def _analyze_windows(self, max_dumps: int) -> str:
        lines = ["\U0001f9e0 MEMORY DUMP ANALYSE", "=" * 50, ""]

        # 1. Minidump-Dateien auflisten
        lines.extend(self._list_minidumps(max_dumps))
        lines.append("")

        # 2. Vollstaendigen Dump pruefen
        lines.extend(self._check_full_dump())
        lines.append("")

        # 3. Crash-Analyse aus Event-Log (BugCheck Events)
        lines.extend(self._analyze_bugchecks(max_dumps))
        lines.append("")

        # 4. Crash-Frequenz
        lines.extend(self._crash_frequency())
        lines.append("")

        # 5. Kernel-Power Events (unerwartete Shutdowns)
        lines.extend(self._kernel_power_events(max_dumps))
        lines.append("")

        # 6. Dump-Konfiguration
        lines.extend(self._dump_configuration())
        lines.append("")

        # 7. Empfehlungen
        lines.extend(self._generate_recommendations())

        return "\n".join(lines)

    def _list_minidumps(self, max_dumps: int) -> list:
        lines = ["\U0001f4c1 Dump-Dateien:"]

        ps_cmd = (
            f"Get-ChildItem 'C:\\Windows\\Minidump\\*.dmp' -ErrorAction SilentlyContinue | "
            f"Sort-Object LastWriteTime -Descending | Select-Object -First {max_dumps} | "
            f"ForEach-Object {{ \"$($_.FullName)|$($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))|$([math]::Round($_.Length/1KB))\" }}"
        )
        output = _run_cmd(["powershell", "-Command", ps_cmd], timeout=15)

        if output and output.strip():
            for line in output.strip().splitlines():
                parts = line.strip().split("|")
                if len(parts) >= 3:
                    path = parts[0].strip()
                    date = parts[1].strip()
                    size_kb = parts[2].strip()
                    lines.append(f"  {path}  ({date}, {size_kb} KB)")
        else:
            lines.append("  Keine Minidump-Dateien gefunden")

        return lines

    def _check_full_dump(self) -> list:
        lines = []
        ps_cmd = (
            "if (Test-Path 'C:\\Windows\\MEMORY.DMP') { "
            "$f = Get-Item 'C:\\Windows\\MEMORY.DMP'; "
            "\"EXISTS|$($f.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))|$([math]::Round($f.Length/1GB, 1))\" "
            "} else { 'NONE' }"
        )
        output = _run_cmd(["powershell", "-Command", ps_cmd], timeout=10)

        if output and output.strip().startswith("EXISTS"):
            parts = output.strip().split("|")
            if len(parts) >= 3:
                date = parts[1].strip()
                size_gb = parts[2].strip()
                lines.append(f"  Vollstaendiger Dump: C:\\Windows\\MEMORY.DMP ({date}, {size_gb} GB)")
        else:
            lines.append("  Vollstaendiger Dump: Nicht vorhanden")

        return lines

    def _analyze_bugchecks(self, max_dumps: int) -> list:
        lines = [f"\U0001f4a5 Crash-Analyse (letzte {max_dumps}):"]

        # BugCheck Events aus WER-SystemErrorReporting
        ps_cmd = (
            f"Get-WinEvent -FilterHashtable @{{LogName='System'; Id=1001; "
            f"ProviderName='Microsoft-Windows-WER-SystemErrorReporting'}} "
            f"-MaxEvents {max_dumps} -ErrorAction SilentlyContinue | "
            f"ForEach-Object {{ "
            f"$msg = $_.Message; "
            f"$code = ''; "
            f"if ($msg -match '0x([0-9a-fA-F]{{8}})') {{ $code = '0x' + $Matches[1].ToUpper() }}; "
            f"\"$($_.TimeCreated.ToString('yyyy-MM-dd HH:mm'))|$code|$($msg.Substring(0, [Math]::Min(200, $msg.Length)))\" }}"
        )
        output = _run_cmd(["powershell", "-Command", ps_cmd], timeout=20)

        self._found_codes = []  # Fuer Empfehlungen merken

        if output and output.strip():
            for line in output.strip().splitlines():
                parts = line.strip().split("|", 2)
                if len(parts) >= 2:
                    timestamp = parts[0].strip()
                    code_raw = parts[1].strip()
                    # Hex-Ziffern uppercase, aber 0x Prefix beibehalten
                    code = "0x" + code_raw[2:].upper() if code_raw.startswith("0x") else code_raw.upper()

                    info = BUGCHECK_DB.get(code)
                    if info:
                        self._found_codes.append(code)
                        lines.append(f"  {timestamp}  {info['name']} ({code})")
                        lines.append(f"    \u2192 {info['cause']}")
                        lines.append(f"    \u2192 Empfehlung: {info['action']}")
                    elif code:
                        self._found_codes.append(code)
                        lines.append(f"  {timestamp}  Bugcheck {code}")
                        lines.append(f"    \u2192 Unbekannter Code — WinDbg-Analyse empfohlen")
                    else:
                        lines.append(f"  {timestamp}  Crash (Code nicht extrahierbar)")
                    lines.append("")
        else:
            lines.append("  Keine BugCheck-Events im Event-Log gefunden")

        return lines

    def _crash_frequency(self) -> list:
        lines = ["\U0001f4ca Crash-Frequenz:"]

        ps_cmd = (
            "$events = Get-WinEvent -FilterHashtable @{LogName='System'; Id=1001; "
            "ProviderName='Microsoft-Windows-WER-SystemErrorReporting'} -ErrorAction SilentlyContinue; "
            "$now = Get-Date; "
            "$d7 = ($events | Where-Object { $_.TimeCreated -gt $now.AddDays(-7) }).Count; "
            "$d30 = ($events | Where-Object { $_.TimeCreated -gt $now.AddDays(-30) }).Count; "
            "$total = $events.Count; "
            "\"$d7|$d30|$total\""
        )
        output = _run_cmd(["powershell", "-Command", ps_cmd], timeout=20)

        if output and "|" in output.strip():
            parts = output.strip().split("|")
            if len(parts) >= 3:
                d7 = parts[0].strip() or "0"
                d30 = parts[1].strip() or "0"
                total = parts[2].strip() or "0"
                lines.append(f"  Letzte 7 Tage: {d7} Crashes")
                lines.append(f"  Letzte 30 Tage: {d30} Crashes")
                lines.append(f"  Gesamt im Log: {total} Crashes")

                try:
                    if int(d7) >= 3:
                        lines.append("  \u26a0\ufe0f  Kritisch: Mehrere Crashes pro Woche — dringendes Problem!")
                    elif int(d30) >= 5:
                        lines.append("  \u26a0\ufe0f  Erhoehte Crash-Rate — systematisches Problem wahrscheinlich")
                    elif int(d30) == 0 and int(total) == 0:
                        lines.append("  \u2705 Keine Crashes dokumentiert")
                except ValueError:
                    pass
        else:
            lines.append("  Keine Crash-Daten verfuegbar")

        return lines

    def _kernel_power_events(self, max_events: int) -> list:
        lines = ["\u26a1 Kernel-Power Events (unerwartete Shutdowns):"]

        ps_cmd = (
            f"Get-WinEvent -FilterHashtable @{{LogName='System'; Id=41}} "
            f"-MaxEvents {max_events} -ErrorAction SilentlyContinue | "
            f"ForEach-Object {{ \"$($_.TimeCreated.ToString('yyyy-MM-dd HH:mm'))|$($_.Message.Substring(0, [Math]::Min(100, $_.Message.Length)))\" }}"
        )
        output = _run_cmd(["powershell", "-Command", ps_cmd], timeout=15)

        if output and output.strip():
            for line in output.strip().splitlines():
                parts = line.strip().split("|", 1)
                if len(parts) >= 1:
                    timestamp = parts[0].strip()
                    lines.append(f"  {timestamp}  Event 41 \u2014 Unerwarteter Neustart")
        else:
            lines.append("  Keine Kernel-Power Events gefunden")

        return lines

    def _dump_configuration(self) -> list:
        lines = ["\u2699\ufe0f  Dump-Konfiguration:"]

        ps_cmd = (
            "$cc = Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\CrashControl' -ErrorAction SilentlyContinue; "
            "if ($cc) { \"$($cc.CrashDumpEnabled)|$($cc.MinidumpDir)|$($cc.DumpFile)\" } else { 'NONE' }"
        )
        output = _run_cmd(["powershell", "-Command", ps_cmd], timeout=10)

        dump_types = {
            "0": "None (Dumps deaktiviert)",
            "1": "Complete Memory Dump",
            "2": "Kernel Memory Dump",
            "3": "Small Memory Dump (Minidump)",
            "7": "Automatic Memory Dump",
        }

        if output and output.strip() != "NONE":
            parts = output.strip().split("|")
            if len(parts) >= 1:
                dump_type = parts[0].strip()
                dump_desc = dump_types.get(dump_type, f"Unbekannt ({dump_type})")
                lines.append(f"  CrashDumpEnabled: {dump_type} ({dump_desc})")

                if dump_type == "0":
                    lines.append("  \u26a0\ufe0f  Dumps sind DEAKTIVIERT — Crash-Analyse nicht moeglich!")

            if len(parts) >= 2 and parts[1].strip():
                lines.append(f"  MinidumpDir: {parts[1].strip()}")
            if len(parts) >= 3 and parts[2].strip():
                lines.append(f"  DumpFile: {parts[2].strip()}")
        else:
            lines.append("  Dump-Konfiguration nicht lesbar")

        return lines

    def _generate_recommendations(self) -> list:
        lines = ["\u2500" * 50, "\U0001f4a1 Empfehlungen:"]

        codes = getattr(self, "_found_codes", [])

        if not codes:
            lines.append("  \u2022 Keine Crashes gefunden — System laeuft stabil")
            return lines

        # Treiber-bezogene Codes
        driver_codes = {"0x0000000A", "0x0000001E", "0x0000003B", "0x0000007E",
                        "0x0000009F", "0x000000D1"}
        if any(c in driver_codes for c in codes):
            lines.append("  \u2022 Treiber-Updates mit /scan pruefen")

        # Hardware-bezogene Codes
        hw_codes = {"0x00000124", "0x0000012B", "0x00000050"}
        if any(c in hw_codes for c in codes):
            lines.append("  \u2022 RAM-Test empfohlen (memtest86) bei Hardware-Fehlern")
            lines.append("  \u2022 CPU-Temperatur und Kuehlung pruefen")

        # System-Integritaet
        integrity_codes = {"0x000000EF", "0x00000139", "0x0000013A"}
        if any(c in integrity_codes for c in codes):
            lines.append("  \u2022 SFC /scannow + DISM ausfuehren")
            lines.append("  \u2022 System auf Malware pruefen")

        # Allgemeine Empfehlung bei mehreren Crashes
        if len(codes) >= 3:
            lines.append("  \u2022 Bei haeufigen Crashes: Systemwiederherstellung in Betracht ziehen")

        return lines

    def _analyze_macos(self, max_dumps: int) -> list:
        lines = ["\U0001f9e0 CRASH/PANIC LOG ANALYSE (macOS)", "=" * 50, ""]

        # 1. Panic-Reports aus DiagnosticReports
        lines.extend(self._list_panic_reports(max_dumps))
        lines.append("")

        # 2. Kernel-Panic aus log show
        lines.extend(self._check_panic_log(max_dumps))
        lines.append("")

        # 3. Unerwartete Shutdowns
        lines.extend(self._check_shutdown_cause())
        lines.append("")

        # 4. Empfehlungen
        lines.append("\u2500" * 50)
        lines.append("\U0001f4a1 Empfehlungen:")
        lines.append("  \u2022 Bei Kernel-Panics: Alle Kernel-Extensions pruefen (kextstat)")
        lines.append("  \u2022 macOS und alle Apps aktualisieren")
        lines.append("  \u2022 SMC/NVRAM Reset bei Hardware-bezogenen Panics")
        lines.append("  \u2022 Apple Diagnose ausfuehren (beim Start D gedrueckt halten)")

        return "\n".join(lines)

    def _list_panic_reports(self, max_dumps: int) -> list:
        lines = ["\U0001f4c1 Panic-Reports:"]

        # DiagnosticReports Verzeichnisse pruefen
        output = _run_cmd(
            ["ls", "-lt", "/Library/Logs/DiagnosticReports/"],
            timeout=10,
        )

        panic_files = []
        if output:
            for line in output.strip().splitlines():
                if "panic" in line.lower() or ".ips" in line.lower():
                    panic_files.append(line.strip())

        # Auch User-Verzeichnis pruefen
        user_output = _run_cmd(
            ["ls", "-lt", "~/Library/Logs/DiagnosticReports/"],
            timeout=10,
        )
        if user_output:
            for line in user_output.strip().splitlines():
                if "panic" in line.lower() or ".ips" in line.lower():
                    panic_files.append(line.strip())

        if panic_files:
            for pf in panic_files[:max_dumps]:
                lines.append(f"  {pf}")
        else:
            lines.append("  Keine Panic-Reports gefunden")

        return lines

    def _check_panic_log(self, max_entries: int) -> list:
        lines = ["\U0001f4a5 Kernel-Panic Events:"]

        output = _run_cmd(
            ["log", "show", "--predicate",
             'eventMessage contains "panic" or eventMessage contains "Kernel panic"',
             "--style", "compact", "--last", "30d"],
            timeout=30,
        )

        if output and output.strip():
            panic_lines = [
                l for l in output.strip().splitlines()
                if "panic" in l.lower() and not l.startswith("Timestamp")
            ]
            if panic_lines:
                for pl in panic_lines[:max_entries]:
                    lines.append(f"  {pl[:120]}")
            else:
                lines.append("  Keine Kernel-Panic Events in den letzten 30 Tagen")
        else:
            lines.append("  Keine Kernel-Panic Events in den letzten 30 Tagen")

        return lines

    def _check_shutdown_cause(self) -> list:
        lines = ["\u26a1 Shutdown-Ursachen:"]

        output = _run_cmd(
            ["log", "show", "--predicate",
             'eventMessage contains "Previous shutdown cause"',
             "--style", "compact", "--last", "30d"],
            timeout=20,
        )

        shutdown_causes = {
            "0": "Power-Fehler (Stromausfall)",
            "3": "Harter Shutdown (erzwungen)",
            "5": "Normaler Shutdown",
            "-3": "Thermischer Notfall",
            "-60": "Bad Master Directory Block (Dateisystem)",
            "-61": "Watchdog-Timeout",
            "-62": "Watchdog-Timeout (SOC)",
            "-71": "SOC Panic",
            "-74": "PMU Panic",
            "-100": "Unbekannter Fehler",
            "-104": "Power Supply Issue",
            "-128": "HALT erzwungen",
        }

        if output and output.strip():
            for line in output.strip().splitlines():
                if "Previous shutdown cause" in line:
                    # Code extrahieren
                    for code, desc in shutdown_causes.items():
                        if f"cause: {code}" in line or f"cause:{code}" in line:
                            timestamp = line[:19] if len(line) > 19 else ""
                            lines.append(f"  {timestamp}  Cause {code}: {desc}")
                            break
                    else:
                        lines.append(f"  {line[:120]}")
        else:
            lines.append("  Keine Shutdown-Ursachen in den letzten 30 Tagen")

        return lines
