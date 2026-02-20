"""
CE365 Agent - System Repair Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

System-Reparatur:
- Windows: SFC /scannow, DISM
- macOS: Disk First Aid, Permissions Repair
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import RepairTool


class RunSFCScanTool(RepairTool):
    """
    Windows System File Check (SFC /scannow)

    Repariert beschädigte System-Dateien
    Dauert 10-30 Minuten!
    """

    @property
    def name(self) -> str:
        return "run_sfc_scan"

    @property
    def description(self) -> str:
        return (
            "Führt Windows System File Check (SFC /scannow) aus. "
            "Repariert beschädigte Windows-System-Dateien. "
            "Nutze dies bei: 1) System-Crashes, 2) Fehler bei Updates, "
            "3) Beschädigte DLL-Dateien, 4) Blue Screen Errors. "
            "ACHTUNG: Dauert 10-30 Minuten! "
            "Nur für Windows, erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Führt SFC Scan aus

        Returns:
            Scan-Ergebnis oder Fehler
        """
        os_type = platform.system()

        if os_type != "Windows":
            return "❌ Dieses Tool ist nur für Windows verfügbar"

        try:
            output = [
                "🔍 Starte System File Check (SFC /scannow)",
                "",
                "⏱️  Geschätzte Dauer: 10-30 Minuten",
                "⚠️  Schließe dieses Fenster NICHT während dem Scan!",
                ""
            ]

            # SFC Scan ausführen
            result = subprocess.run(
                ["sfc", "/scannow"],
                capture_output=True,
                text=True,
                timeout=3600  # 60 Minuten Timeout
            )

            # Ergebnis parsen
            scan_output = result.stdout

            if "Windows-Ressourcenschutz hat keine Integritätsverletzungen gefunden" in scan_output:
                output.append("✅ Scan abgeschlossen: Keine Probleme gefunden")
                output.append("")
                output.append("Alle System-Dateien sind intakt.")

            elif "Windows-Ressourcenschutz hat beschädigte Dateien gefunden und erfolgreich repariert" in scan_output:
                output.append("✅ Scan abgeschlossen: Probleme gefunden und REPARIERT")
                output.append("")
                output.append("Beschädigte System-Dateien wurden erfolgreich wiederhergestellt.")
                output.append("")
                output.append("📝 Details: C:\\Windows\\Logs\\CBS\\CBS.log")

            elif "Windows-Ressourcenschutz hat beschädigte Dateien gefunden, konnte jedoch einige der Dateien nicht reparieren" in scan_output:
                output.append("⚠️  Scan abgeschlossen: Probleme gefunden, aber NICHT alle repariert")
                output.append("")
                output.append("Einige System-Dateien konnten nicht repariert werden.")
                output.append("")
                output.append("Nächster Schritt: run_dism_repair ausführen, dann SFC erneut.")

            else:
                output.append("ℹ️  Scan abgeschlossen")
                output.append("")
                output.append(scan_output[:500])

            return "\n".join(output)

        except subprocess.TimeoutExpired:
            return (
                "❌ SFC Scan Timeout (>60 Minuten)\n\n"
                "Der Scan hat zu lange gedauert. Möglicherweise hängt der Prozess.\n"
                "Prüfe Task Manager ob SFC läuft."
            )
        except Exception as e:
            return f"❌ Fehler beim SFC Scan: {str(e)}"


class RunDISMRepairTool(RepairTool):
    """
    Windows DISM (Deployment Image Servicing and Management)

    Repariert das Windows Component Store (WinSxS).
    Wird typischerweise VOR einem erneuten SFC-Scan ausgefuehrt,
    wenn SFC beschaedigte Dateien nicht reparieren konnte.
    """

    @property
    def name(self) -> str:
        return "run_dism_repair"

    @property
    def description(self) -> str:
        return (
            "Fuehrt Windows DISM Repair aus (Deployment Image Servicing and Management). "
            "Repariert das Windows Component Store und den System-Image. "
            "Nutze dies bei: 1) SFC konnte Dateien nicht reparieren, "
            "2) Windows Update Fehler, 3) Component Store Korruption, "
            "4) Feature-Installation schlaegt fehl. "
            "ACHTUNG: Dauert 15-45 Minuten, benoetigt Internet! "
            "Nur fuer Windows, erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scan_only": {
                    "type": "boolean",
                    "description": "Nur scannen ohne Reparatur (CheckHealth + ScanHealth)",
                    "default": False,
                }
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        """
        Fuehrt DISM Repair aus

        Args:
            scan_only: True = nur pruefen, False = auch reparieren

        Returns:
            Scan/Repair-Ergebnis
        """
        os_type = platform.system()

        if os_type != "Windows":
            return "❌ Dieses Tool ist nur fuer Windows verfuegbar"

        scan_only = kwargs.get("scan_only", False)

        try:
            output = []

            # Phase 1: CheckHealth (schnell, <1 Minute)
            output.append("🔍 Phase 1/3: DISM CheckHealth")
            output.append("")

            result_check = subprocess.run(
                ["DISM", "/Online", "/Cleanup-Image", "/CheckHealth"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 Minuten
            )

            check_out = result_check.stdout
            if "No component store corruption detected" in check_out:
                output.append("✅ CheckHealth: Keine Korruption erkannt")
            elif "component store is repairable" in check_out:
                output.append("⚠️  CheckHealth: Korruption erkannt, reparierbar")
            else:
                output.append(f"ℹ️  CheckHealth: {check_out[:200]}")
            output.append("")

            # Phase 2: ScanHealth (gruendlicher, 5-15 Minuten)
            output.append("🔍 Phase 2/3: DISM ScanHealth (kann 5-15 Minuten dauern)")
            output.append("")

            result_scan = subprocess.run(
                ["DISM", "/Online", "/Cleanup-Image", "/ScanHealth"],
                capture_output=True,
                text=True,
                timeout=1800,  # 30 Minuten
            )

            scan_out = result_scan.stdout
            if "No component store corruption detected" in scan_out:
                output.append("✅ ScanHealth: Component Store ist intakt")
                if scan_only:
                    output.append("")
                    output.append("Scan-Modus: Keine Reparatur durchgefuehrt.")
                    return "\n".join(output)
                # Auch bei intaktem Store beenden
                output.append("")
                output.append("✅ Keine Reparatur notwendig — Component Store ist gesund.")
                return "\n".join(output)

            elif "component store is repairable" in scan_out:
                output.append("⚠️  ScanHealth: Component Store ist beschaedigt, aber reparierbar")
            else:
                output.append(f"ℹ️  ScanHealth: {scan_out[:200]}")

            output.append("")

            if scan_only:
                output.append("Scan-Modus: Keine Reparatur durchgefuehrt.")
                output.append("Empfehlung: Erneut mit scan_only=false ausfuehren fuer Reparatur.")
                return "\n".join(output)

            # Phase 3: RestoreHealth (Reparatur, 15-45 Minuten, braucht Internet)
            output.append("🔧 Phase 3/3: DISM RestoreHealth (15-45 Minuten, benoetigt Internet)")
            output.append("⚠️  Schliesse dieses Fenster NICHT waehrend der Reparatur!")
            output.append("")

            result_restore = subprocess.run(
                ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"],
                capture_output=True,
                text=True,
                timeout=3600,  # 60 Minuten
            )

            restore_out = result_restore.stdout

            if result_restore.returncode == 0:
                output.append("✅ RestoreHealth abgeschlossen: Component Store repariert")
                output.append("")
                output.append("Naechster Schritt: SFC /scannow erneut ausfuehren (run_sfc_scan)")
            else:
                # Fehler parsen
                restore_err = result_restore.stderr or restore_out
                if "0x800f081f" in restore_err:
                    output.append("❌ RestoreHealth fehlgeschlagen: Quell-Dateien nicht gefunden")
                    output.append("")
                    output.append("Moegliche Loesungen:")
                    output.append("  1. Windows Update Dienst pruefen (muss laufen)")
                    output.append("  2. Internet-Verbindung pruefen")
                    output.append("  3. Windows ISO als Quelle verwenden:")
                    output.append("     DISM /Online /Cleanup-Image /RestoreHealth /Source:D:\\Sources\\install.wim")
                elif "0x800f0906" in restore_err:
                    output.append("❌ RestoreHealth fehlgeschlagen: Download-Fehler")
                    output.append("")
                    output.append("Windows konnte die Reparatur-Dateien nicht herunterladen.")
                    output.append("Pruefen: Internet-Verbindung, Proxy, Windows Update Dienst")
                else:
                    output.append(f"❌ RestoreHealth fehlgeschlagen (Exit Code: {result_restore.returncode})")
                    output.append("")
                    output.append(restore_err[:500] if restore_err else restore_out[:500])

            # Log-Hinweis
            output.append("")
            output.append("📝 DISM-Log: C:\\Windows\\Logs\\DISM\\dism.log")

            return "\n".join(output)

        except subprocess.TimeoutExpired:
            return (
                "❌ DISM Timeout (>60 Minuten)\n\n"
                "Die Reparatur hat zu lange gedauert.\n"
                "Pruefen: Internetverbindung, Windows Update Dienst, Systemlast."
            )
        except Exception as e:
            return f"❌ Fehler bei DISM: {str(e)}"


class RunChkdskTool(RepairTool):
    """
    Windows Check Disk (chkdsk)

    Prueft und repariert Dateisystem-Fehler auf Windows-Laufwerken.
    Gegenstueck zu macOS diskutil repairVolume.
    """

    @property
    def name(self) -> str:
        return "run_chkdsk"

    @property
    def description(self) -> str:
        return (
            "Fuehrt Windows Check Disk (chkdsk) aus. "
            "Prueft und repariert Dateisystem-Fehler und fehlerhafte Sektoren. "
            "Nutze dies bei: 1) Disk-Fehlern, 2) Langsamer Festplatte, "
            "3) Dateisystem-Korruption, 4) Unerwartete Abstuerze, "
            "5) S.M.A.R.T. Warnungen. "
            "ACHTUNG: Kann 30-60+ Minuten dauern! "
            "Repair-Modus auf System-Laufwerk erfordert Neustart! "
            "Nur fuer Windows, erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "drive": {
                    "type": "string",
                    "description": "Laufwerk zu pruefen (z.B. C:, D:). Standard: C:",
                    "default": "C:",
                },
                "scan_only": {
                    "type": "boolean",
                    "description": "Nur scannen ohne Reparatur (kein /F, kein /R)",
                    "default": False,
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        """
        Fuehrt chkdsk aus

        Args:
            drive: Laufwerk (default C:)
            scan_only: True = nur pruefen, False = auch reparieren

        Returns:
            Scan/Repair-Ergebnis
        """
        os_type = platform.system()

        if os_type != "Windows":
            return "❌ Dieses Tool ist nur fuer Windows verfuegbar"

        drive = kwargs.get("drive", "C:")
        scan_only = kwargs.get("scan_only", False)

        # Laufwerksbuchstabe validieren (nur A-Z mit Doppelpunkt)
        drive = drive.strip().upper()
        if len(drive) != 2 or not drive[0].isalpha() or drive[1] != ":":
            return f"❌ Ungueltiges Laufwerk: '{drive}'. Format: C: oder D:"

        try:
            output = []

            if scan_only:
                # Scan-Only: kein /F, kein /R — nur Bericht
                output.append(f"🔍 Starte chkdsk Scan fuer {drive} (nur Pruefung)")
                output.append("")

                result = subprocess.run(
                    ["chkdsk", drive],
                    capture_output=True,
                    text=True,
                    timeout=3600,  # 60 Minuten
                )

                scan_out = result.stdout

                # Ergebnis parsen
                if "Windows has scanned the file system and found no problems" in scan_out:
                    output.append(f"✅ Keine Fehler auf {drive} gefunden")
                elif "Windows has checked the file system and found no problems" in scan_out:
                    output.append(f"✅ Keine Fehler auf {drive} gefunden")
                elif "hat das Dateisystem" in scan_out and "keine Probleme" in scan_out:
                    output.append(f"✅ Keine Fehler auf {drive} gefunden")
                else:
                    output.append(f"ℹ️  chkdsk Ergebnis fuer {drive}:")
                    output.append("")
                    # Letzte relevante Zeilen extrahieren
                    lines = [l.strip() for l in scan_out.splitlines() if l.strip()]
                    for line in lines[-15:]:
                        output.append(f"  {line}")

                return "\n".join(output)

            else:
                # Repair-Modus: /F (Fehler beheben) + /R (fehlerhafte Sektoren)
                output.append(f"🔧 Starte chkdsk Repair fuer {drive}")
                output.append("")
                output.append("⏱️  Geschaetzte Dauer: 30-60+ Minuten")
                output.append("")

                # System-Laufwerk erfordert Neustart
                is_system_drive = drive.upper() in ("C:", "C:\\")

                if is_system_drive:
                    output.append("⚠️  System-Laufwerk C: kann nur beim Neustart geprueft werden.")
                    output.append("   Plane chkdsk beim naechsten Neustart ein...")
                    output.append("")

                    # chkdsk /F /R beim naechsten Boot einplanen
                    result = subprocess.run(
                        ["chkdsk", drive, "/F", "/R"],
                        capture_output=True,
                        text=True,
                        input="Y\n",  # Bestaetigung: Beim naechsten Neustart
                        timeout=30,
                    )

                    if result.returncode == 0 or "beim naechsten Neustart" in (result.stdout + result.stderr) or "next time the system restarts" in (result.stdout + result.stderr):
                        output.append("✅ chkdsk wurde fuer den naechsten Neustart eingeplant.")
                        output.append("")
                        output.append("Beim naechsten Windows-Neustart wird Folgendes ausgefuehrt:")
                        output.append(f"  - Dateisystem-Pruefung auf {drive}")
                        output.append("  - Fehlerhafte Sektoren suchen und reparieren")
                        output.append("  - Dateisystem-Fehler beheben")
                        output.append("")
                        output.append("⚠️  Der Neustart dauert deutlich laenger als normal!")
                        output.append("   Computer NICHT ausschalten waehrend chkdsk laeuft!")
                    else:
                        # Eventuell als Admin ausgefuehrt und direkt repariert
                        scan_out = result.stdout
                        output.append(f"ℹ️  chkdsk Ergebnis:")
                        output.append("")
                        lines = [l.strip() for l in scan_out.splitlines() if l.strip()]
                        for line in lines[-10:]:
                            output.append(f"  {line}")

                else:
                    # Nicht-System-Laufwerk: direkt reparieren
                    output.append(f"Repariere {drive} direkt (kein Neustart noetig)")
                    output.append("⚠️  Schliesse alle Dateien auf {drive}!")
                    output.append("")

                    result = subprocess.run(
                        ["chkdsk", drive, "/F", "/R"],
                        capture_output=True,
                        text=True,
                        timeout=7200,  # 2 Stunden
                    )

                    scan_out = result.stdout

                    if result.returncode == 0:
                        output.append(f"✅ chkdsk Repair fuer {drive} abgeschlossen")
                    else:
                        output.append(f"⚠️  chkdsk fuer {drive} beendet (Exit Code: {result.returncode})")

                    output.append("")
                    # Letzte Zeilen
                    lines = [l.strip() for l in scan_out.splitlines() if l.strip()]
                    for line in lines[-15:]:
                        output.append(f"  {line}")

                return "\n".join(output)

        except subprocess.TimeoutExpired:
            return (
                f"❌ chkdsk Timeout fuer {drive}\n\n"
                "Der Scan hat zu lange gedauert.\n"
                "Bei grossen Laufwerken kann chkdsk mehrere Stunden dauern."
            )
        except Exception as e:
            return f"❌ Fehler bei chkdsk: {str(e)}"


class RepairDiskPermissionsTool(RepairTool):
    """
    macOS Disk Permissions Repair

    Repariert Dateiberechtigungen auf macOS
    """

    @property
    def name(self) -> str:
        return "repair_disk_permissions"

    @property
    def description(self) -> str:
        return (
            "Repariert Dateiberechtigungen auf macOS. "
            "Nutze dies bei: 1) Permission denied Fehlern, "
            "2) Apps starten nicht, 3) Schreib-/Lesefehler, "
            "4) Nach System-Updates. "
            "Nur für macOS, erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Repariert Disk Permissions

        Returns:
            Ergebnis oder Fehler
        """
        os_type = platform.system()

        if os_type != "Darwin":
            return "❌ Dieses Tool ist nur für macOS verfügbar"

        try:
            # Get User ID
            import os
            user_id = os.getuid()

            output = [
                "🔧 Repariere Disk Permissions",
                ""
            ]

            # diskutil resetUserPermissions ausführen
            result = subprocess.run(
                ["diskutil", "resetUserPermissions", "/", str(user_id)],
                capture_output=True,
                text=True,
                timeout=300  # 5 Minuten
            )

            if result.returncode == 0:
                output.append("✅ Disk Permissions repariert")
                output.append("")
                output.append(f"User-Permissions für UID {user_id} wurden zurückgesetzt.")
                output.append("")
                output.append("Die meisten Permission-Probleme sollten nun behoben sein.")

            else:
                output.append("❌ Fehler beim Reparieren:")
                output.append("")
                output.append(result.stderr)

            return "\n".join(output)

        except subprocess.TimeoutExpired:
            return "❌ Timeout beim Permission Repair (>5 Minuten)"
        except Exception as e:
            return f"❌ Fehler: {str(e)}"


class RepairDiskTool(RepairTool):
    """
    macOS Disk First Aid

    Führt Disk Utility First Aid aus
    """

    @property
    def name(self) -> str:
        return "repair_disk"

    @property
    def description(self) -> str:
        return (
            "Führt macOS Disk First Aid aus (Festplatten-Reparatur). "
            "Nutze dies bei: 1) Disk-Fehlern, 2) Langsamer Performance, "
            "3) Datei-System-Fehlern, 4) Vor größeren Updates. "
            "ACHTUNG: Kann 10-30 Minuten dauern! "
            "Nur für macOS, erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "volume": {
                    "type": "string",
                    "description": "Volume zu reparieren (Standard: /)",
                    "default": "/"
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Führt Disk Repair aus

        Args:
            volume: Volume zu reparieren (default: /)

        Returns:
            Repair-Ergebnis
        """
        os_type = platform.system()

        if os_type != "Darwin":
            return "❌ Dieses Tool ist nur für macOS verfügbar"

        volume = kwargs.get("volume", "/")

        try:
            output = [
                f"🔧 Starte Disk First Aid für {volume}",
                "",
                "⏱️  Geschätzte Dauer: 10-30 Minuten",
                "⚠️  Schließe dieses Fenster NICHT während der Reparatur!",
                ""
            ]

            # diskutil repairVolume ausführen
            result = subprocess.run(
                ["diskutil", "repairVolume", volume],
                capture_output=True,
                text=True,
                timeout=3600  # 60 Minuten
            )

            repair_output = result.stdout

            if "The volume appears to be OK" in repair_output or "Repair complete" in repair_output:
                output.append("✅ Disk Repair abgeschlossen: Keine Probleme gefunden")
                output.append("")
                output.append("Das Volume ist in gutem Zustand.")

            elif "was repaired successfully" in repair_output:
                output.append("✅ Disk Repair abgeschlossen: Probleme REPARIERT")
                output.append("")
                output.append("Festplatten-Fehler wurden erfolgreich behoben.")

            elif "could not be repaired" in repair_output:
                output.append("❌ Disk Repair fehlgeschlagen")
                output.append("")
                output.append("Einige Probleme konnten nicht behoben werden.")
                output.append("")
                output.append("Empfehlung: Backup erstellen und macOS neu installieren.")

            else:
                output.append("ℹ️  Disk Repair abgeschlossen")
                output.append("")
                output.append(repair_output[:500])

            return "\n".join(output)

        except subprocess.TimeoutExpired:
            return "❌ Disk Repair Timeout (>60 Minuten)"
        except Exception as e:
            return f"❌ Fehler beim Disk Repair: {str(e)}"
