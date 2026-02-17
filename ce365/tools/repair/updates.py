"""
CE365 Agent - Update Installation Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

System-Updates installieren:
- Windows: Windows Update Installation
- macOS: Software Update Installation
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import RepairTool


class InstallSystemUpdatesTool(RepairTool):
    """
    Installiert verfügbare System-Updates

    Windows: Windows Update
    macOS: Software Update

    ACHTUNG: Kann 30+ Minuten dauern!
    Kann Neustart erfordern!
    """

    @property
    def name(self) -> str:
        return "install_system_updates"

    @property
    def description(self) -> str:
        return (
            "Installiert verfügbare System-Updates (Windows Update / macOS Software Update). "
            "Nutze dies bei: 1) Sicherheitsupdates verfügbar, 2) Regelmäßige Wartung, "
            "3) Vor größeren System-Änderungen. "
            "ACHTUNG: Kann 30+ Minuten dauern und Neustart erfordern! "
            "WICHTIG: Erfordert GO REPAIR Freigabe!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "auto_reboot": {
                    "type": "boolean",
                    "description": "Automatischer Neustart nach Installation (Standard: false)",
                    "default": False
                },
                "install_all": {
                    "type": "boolean",
                    "description": "Alle Updates installieren (Standard: true)",
                    "default": True
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Installiert System-Updates

        Args:
            auto_reboot: Auto-Neustart nach Installation (default: False)
            install_all: Alle Updates installieren (default: True)

        Returns:
            Installations-Bericht
        """
        auto_reboot = kwargs.get("auto_reboot", False)
        install_all = kwargs.get("install_all", True)

        os_type = platform.system()

        if os_type == "Windows":
            return self._install_windows_updates(auto_reboot, install_all)
        elif os_type == "Darwin":
            return self._install_macos_updates(auto_reboot, install_all)
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _install_windows_updates(self, auto_reboot: bool, install_all: bool) -> str:
        """Windows Updates installieren"""
        try:
            output = [
                "🔄 Windows Update Installation gestartet",
                "",
                "⏱️  Geschätzte Dauer: 10-60 Minuten (abhängig von Update-Größe)",
                "⚠️  Schließe dieses Fenster NICHT während der Installation!",
                ""
            ]

            # Methode 1: PSWindowsUpdate Modul (wenn verfügbar)
            reboot_flag = "-AutoReboot" if auto_reboot else ""
            accept_flag = "-AcceptAll" if install_all else ""

            ps_cmd = f"""
            if (Get-Module -ListAvailable -Name PSWindowsUpdate) {{
                Import-Module PSWindowsUpdate
                Install-WindowsUpdate {accept_flag} {reboot_flag} -Verbose |
                Select-Object KB, Title, Result |
                ConvertTo-Json
            }} else {{
                Write-Output "PSWindowsUpdate_NOT_INSTALLED"
            }}
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=3600  # 60 Minuten Timeout
            )

            # PSWindowsUpdate Modul fehlt?
            if "PSWindowsUpdate_NOT_INSTALLED" in result.stdout:
                return self._install_windows_updates_fallback(auto_reboot)

            # Parse Ergebnis
            import json
            try:
                updates = json.loads(result.stdout)

                if not updates:
                    output.append("ℹ️  Keine Updates zum Installieren gefunden")
                    return "\n".join(output)

                # Sicherstellen dass updates Liste ist
                if not isinstance(updates, list):
                    updates = [updates]

                output.append(f"✅ {len(updates)} Update(s) installiert:\n")

                for update in updates:
                    kb = update.get("KB", "Unbekannt")
                    title = update.get("Title", "Unbekannt")
                    result_status = update.get("Result", "Unknown")

                    if result_status == "Installed" or "Success" in str(result_status):
                        status = "✓"
                    else:
                        status = "✗"

                    output.append(f"{status} KB{kb}: {title}")

                output.append("")

                if auto_reboot:
                    output.append("🔄 System wird automatisch neugestartet...")
                else:
                    output.append("⚠️  NEUSTART ERFORDERLICH!")
                    output.append("   Starte das System neu um Updates abzuschließen.")

                return "\n".join(output)

            except json.JSONDecodeError:
                # Fallback: Raw output
                output.append("Installation abgeschlossen.")
                output.append("")
                if result.stdout:
                    output.append(result.stdout[:500])
                return "\n".join(output)

        except subprocess.TimeoutExpired:
            return (
                "❌ Windows Update Installation Timeout (>60 Minuten)\n\n"
                "Die Installation hat zu lange gedauert.\n"
                "Prüfe Windows Update Status manuell."
            )
        except Exception as e:
            return f"❌ Fehler bei Update-Installation: {str(e)}"

    def _install_windows_updates_fallback(self, auto_reboot: bool) -> str:
        """Fallback ohne PSWindowsUpdate Modul"""
        return (
            "⚠️  PSWindowsUpdate Modul nicht installiert\n\n"
            "Automatische Update-Installation erfordert das PSWindowsUpdate PowerShell-Modul.\n\n"
            "Installation:\n"
            "1. Öffne PowerShell als Administrator\n"
            "2. Führe aus: Install-Module PSWindowsUpdate -Force\n"
            "3. Führe aus: Add-WUServiceManager -ServiceID 7971f918-a847-4430-9279-4a52d1efe18d\n\n"
            "Alternative:\n"
            "Installiere Updates manuell über Settings → Update & Security → Windows Update"
        )

    def _install_macos_updates(self, auto_reboot: bool, install_all: bool) -> str:
        """macOS Software Updates installieren"""
        try:
            output = [
                "🔄 macOS Software Update Installation gestartet",
                "",
                "⏱️  Geschätzte Dauer: 10-60 Minuten (abhängig von Update-Größe)",
                "⚠️  Schließe dieses Fenster NICHT während der Installation!",
                ""
            ]

            # softwareupdate -i -a (all updates)
            cmd = ["softwareupdate", "-i", "-a"]

            if auto_reboot:
                cmd.append("--restart")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 60 Minuten
            )

            install_output = result.stdout + result.stderr

            # Parse Ergebnis
            if "No updates are available" in install_output:
                output.append("ℹ️  Keine Updates zum Installieren gefunden")
                return "\n".join(output)

            # Erfolgreiche Installation?
            if "Done" in install_output or "successfully installed" in install_output.lower():
                output.append("✅ Updates erfolgreich installiert")
                output.append("")

                # Zeige installierte Updates (falls im Output)
                lines = install_output.split("\n")
                for line in lines:
                    if "Installing" in line or "Done" in line:
                        output.append(f"  {line.strip()}")

                output.append("")

                if auto_reboot:
                    output.append("🔄 System wird automatisch neugestartet...")
                else:
                    output.append("⚠️  NEUSTART EMPFOHLEN!")
                    output.append("   Einige Updates erfordern einen Neustart.")

            else:
                output.append("⚠️  Update-Installation abgeschlossen")
                output.append("")
                output.append(install_output[:500])

            return "\n".join(output)

        except subprocess.TimeoutExpired:
            return (
                "❌ macOS Software Update Timeout (>60 Minuten)\n\n"
                "Die Installation hat zu lange gedauert.\n"
                "Prüfe Software Update Status manuell in System Settings."
            )
        except Exception as e:
            return f"❌ Fehler bei Update-Installation: {str(e)}"
