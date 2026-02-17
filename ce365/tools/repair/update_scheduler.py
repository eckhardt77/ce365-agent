"""
CE365 Agent - Update Scheduler

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Automatische Updates planen/konfigurieren (Windows/macOS)
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import RepairTool


class ScheduleSystemUpdatesTool(RepairTool):
    """
    Konfiguriert automatische System-Updates

    Windows: Windows Update Policy (Automatic/Manual)
    macOS: Software Update Scheduler (on/off)
    """

    @property
    def name(self) -> str:
        return "schedule_system_updates"

    @property
    def description(self) -> str:
        return (
            "Konfiguriert automatische System-Updates. Nutze dies bei: "
            "1) Update-Policy ändern, 2) Automatische Updates aktivieren/deaktivieren, "
            "3) Sicherheits-Best-Practices umsetzen, 4) Compliance-Anforderungen. "
            "Optionen: 'automatic' (empfohlen), 'download_only', 'notify_only', 'disabled'."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["automatic", "download_only", "notify_only", "disabled"],
                    "description": (
                        "Update-Modus: "
                        "automatic = Updates automatisch herunterladen und installieren (empfohlen), "
                        "download_only = Updates herunterladen aber manuell installieren, "
                        "notify_only = Nur benachrichtigen (kein automatischer Download), "
                        "disabled = Automatische Updates komplett deaktivieren (NICHT empfohlen)"
                    )
                }
            },
            "required": ["mode"]
        }

    async def execute(self, **kwargs) -> str:
        """
        Konfiguriert Update-Scheduler

        Args:
            mode: Update-Modus (automatic/download_only/notify_only/disabled)

        Returns:
            Erfolgs-/Fehlermeldung
        """
        mode = kwargs.get("mode")

        if not mode:
            return "❌ Fehler: mode ist erforderlich"

        os_type = platform.system()

        if os_type == "Windows":
            return self._configure_windows_updates(mode)
        elif os_type == "Darwin":
            return self._configure_macos_updates(mode)
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _configure_windows_updates(self, mode: str) -> str:
        """Windows Update Policy konfigurieren"""
        try:
            output = [
                "🔧 Konfiguriere Windows Update Policy",
                ""
            ]

            # Windows Update Policy via Registry (funktioniert auch ohne WSUS)
            # AUOptions: 2=Notify, 3=Auto Download, 4=Auto Install, 1=Disabled

            if mode == "automatic":
                au_option = 4  # Auto Download + Install
                output.append("📋 Modus: Automatisch herunterladen und installieren")

            elif mode == "download_only":
                au_option = 3  # Auto Download, Manual Install
                output.append("📋 Modus: Automatisch herunterladen, manuell installieren")

            elif mode == "notify_only":
                au_option = 2  # Notify before Download
                output.append("📋 Modus: Nur benachrichtigen (kein automatischer Download)")

            elif mode == "disabled":
                au_option = 1  # Disabled
                output.append("📋 Modus: Automatische Updates deaktiviert")
                output.append("⚠️  WARNUNG: Deaktivieren ist ein Sicherheitsrisiko!")

            else:
                return f"❌ Unbekannter Modus: {mode}"

            output.append("")

            # Registry-Pfad erstellen falls nicht vorhanden
            ps_cmd_create = """
            $path = 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU'
            if (-not (Test-Path $path)) {
                New-Item -Path $path -Force | Out-Null
            }
            """
            subprocess.run(
                ["powershell", "-Command", ps_cmd_create],
                capture_output=True,
                text=True,
                timeout=30
            )

            # AUOptions setzen
            ps_cmd = f"""
            Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU' -Name 'NoAutoUpdate' -Value 0 -Type DWord
            Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU' -Name 'AUOptions' -Value {au_option} -Type DWord
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                output.append("✅ Windows Update Policy erfolgreich konfiguriert")
                output.append("")

                # Windows Update Service neu starten
                output.append("🔄 Starte Windows Update Service neu...")
                restart_result = subprocess.run(
                    ["powershell", "-Command", "Restart-Service wuauserv -Force"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if restart_result.returncode == 0:
                    output.append("✅ Service erfolgreich neu gestartet")
                else:
                    output.append("⚠️  Service-Neustart fehlgeschlagen (möglicherweise Admin-Rechte erforderlich)")

                output.append("")
                output.append("─" * 50)
                output.append("💡 Empfehlung:")

                if mode == "automatic":
                    output.append("  • Updates werden automatisch installiert (Best Practice)")
                    output.append("  • System bleibt immer aktuell und sicher")
                elif mode == "download_only":
                    output.append("  • Updates werden heruntergeladen, Installation manuell")
                    output.append("  • Guter Kompromiss zwischen Kontrolle und Sicherheit")
                elif mode == "notify_only":
                    output.append("  • Nur Benachrichtigung, keine automatischen Downloads")
                    output.append("  • Erfordert manuelle Aktion für Updates")
                elif mode == "disabled":
                    output.append("  • ⚠️  Automatische Updates sind deaktiviert!")
                    output.append("  • RISIKO: System bleibt ungepatcht und verwundbar")
                    output.append("  • Manuell nach Updates suchen: Settings → Windows Update")

                output.append("")
                output.append("Überprüfen: Settings → Windows Update → Advanced options")

            else:
                output.append(f"❌ Fehler beim Konfigurieren: {result.stderr}")
                output.append("⚠️  Administrator-Rechte erforderlich!")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Konfigurieren: {str(e)}"

    def _configure_macos_updates(self, mode: str) -> str:
        """macOS Software Update konfigurieren"""
        try:
            output = [
                "🔧 Konfiguriere macOS Software Update",
                ""
            ]

            if mode == "automatic":
                output.append("📋 Modus: Automatische Updates aktiviert")
                output.append("")

                # Automatische Update-Check aktivieren
                commands = [
                    ("softwareupdate --schedule on", "Update-Check aktiviert"),
                    ("defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true", "Automatischer Check: Ein"),
                    ("defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticDownload -bool true", "Automatischer Download: Ein"),
                    ("defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates -bool true", "Automatische Installation: Ein"),
                    ("defaults write /Library/Preferences/com.apple.commerce AutoUpdate -bool true", "App Store Updates: Ein")
                ]

                for cmd, desc in commands:
                    result = subprocess.run(
                        cmd.split(),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        output.append(f"✅ {desc}")
                    else:
                        output.append(f"⚠️  {desc} fehlgeschlagen (sudo erforderlich?)")

                output.append("")
                output.append("─" * 50)
                output.append("💡 Empfehlung:")
                output.append("  • Automatische Updates sind aktiviert (Best Practice)")
                output.append("  • macOS bleibt immer aktuell und sicher")
                output.append("  • Überprüfen: System Settings → Software Update")

            elif mode == "download_only":
                output.append("📋 Modus: Automatisch herunterladen, manuell installieren")
                output.append("")

                commands = [
                    ("softwareupdate --schedule on", "Update-Check aktiviert"),
                    ("defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true", "Automatischer Check: Ein"),
                    ("defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticDownload -bool true", "Automatischer Download: Ein"),
                    ("defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates -bool false", "Automatische Installation: Aus")
                ]

                for cmd, desc in commands:
                    result = subprocess.run(
                        cmd.split(),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        output.append(f"✅ {desc}")
                    else:
                        output.append(f"⚠️  {desc} fehlgeschlagen (sudo erforderlich?)")

                output.append("")
                output.append("💡 Tipp: Updates werden heruntergeladen, Installation manuell über Software Update")

            elif mode == "notify_only":
                output.append("📋 Modus: Nur benachrichtigen (kein automatischer Download)")
                output.append("")

                commands = [
                    ("softwareupdate --schedule on", "Update-Check aktiviert"),
                    ("defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true", "Automatischer Check: Ein"),
                    ("defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticDownload -bool false", "Automatischer Download: Aus"),
                    ("defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates -bool false", "Automatische Installation: Aus")
                ]

                for cmd, desc in commands:
                    result = subprocess.run(
                        cmd.split(),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        output.append(f"✅ {desc}")
                    else:
                        output.append(f"⚠️  {desc} fehlgeschlagen (sudo erforderlich?)")

                output.append("")
                output.append("💡 Tipp: Nur Benachrichtigung, manueller Download und Installation erforderlich")

            elif mode == "disabled":
                output.append("📋 Modus: Automatische Updates deaktiviert")
                output.append("⚠️  WARNUNG: Deaktivieren ist ein Sicherheitsrisiko!")
                output.append("")

                commands = [
                    ("softwareupdate --schedule off", "Update-Check deaktiviert"),
                    ("defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled -bool false", "Automatischer Check: Aus"),
                    ("defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticDownload -bool false", "Automatischer Download: Aus"),
                    ("defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates -bool false", "Automatische Installation: Aus")
                ]

                for cmd, desc in commands:
                    result = subprocess.run(
                        cmd.split(),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        output.append(f"✅ {desc}")
                    else:
                        output.append(f"⚠️  {desc} fehlgeschlagen (sudo erforderlich?)")

                output.append("")
                output.append("⚠️  RISIKO: System bleibt ungepatcht und verwundbar")
                output.append("💡 Manuell nach Updates suchen: System Settings → Software Update")

            else:
                return f"❌ Unbekannter Modus: {mode}"

            output.append("")
            output.append("Überprüfen: System Settings → Software Update")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Konfigurieren: {str(e)}"
