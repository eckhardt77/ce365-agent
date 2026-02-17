"""
CE365 Agent - System Repair Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

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
