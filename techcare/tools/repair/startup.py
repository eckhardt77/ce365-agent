"""
TechCare Bot - Startup Programs Management

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Autostart-Programme aktivieren/deaktivieren (Windows/macOS)
"""

import platform
import subprocess
import os
from typing import Dict, Any
from pathlib import Path
from techcare.tools.base import RepairTool
from techcare.tools.sanitize import (
    sanitize_powershell_string,
    sanitize_applescript_string,
    validate_program_name,
    validate_file_path,
)


class DisableStartupProgramTool(RepairTool):
    """
    Deaktiviert ein Autostart-Programm

    Windows: Registry Run Keys löschen, Startup Folder Items deaktivieren, Tasks deaktivieren
    macOS: Login Items entfernen, LaunchAgent/Daemon deaktivieren
    """

    @property
    def name(self) -> str:
        return "disable_startup_program"

    @property
    def description(self) -> str:
        return (
            "Deaktiviert ein Programm im Autostart. Nutze dies bei: "
            "1) Langsames Hochfahren, 2) Performance-Optimierung, "
            "3) Unerwünschte Programme entfernen, 4) Malware-Verdacht. "
            "WICHTIG: Prüfe zuerst mit check_startup_programs welche Programme existieren!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "program_name": {
                    "type": "string",
                    "description": "Name des Programms (exakt wie bei check_startup_programs angezeigt)"
                },
                "startup_type": {
                    "type": "string",
                    "enum": ["registry_hkcu", "registry_hklm", "startup_folder", "task_scheduler", "login_item", "launch_agent_user", "launch_agent_system", "launch_daemon"],
                    "description": "Typ des Autostart-Eintrags (siehe check_startup_programs Output)"
                }
            },
            "required": ["program_name", "startup_type"]
        }

    async def execute(self, **kwargs) -> str:
        """
        Deaktiviert Autostart-Programm

        Args:
            program_name: Name des Programms
            startup_type: Typ des Autostart-Eintrags

        Returns:
            Erfolgs-/Fehlermeldung
        """
        program_name = kwargs.get("program_name")
        startup_type = kwargs.get("startup_type")

        if not program_name or not startup_type:
            return "❌ Fehler: program_name und startup_type sind erforderlich"

        os_type = platform.system()

        if os_type == "Windows":
            return self._disable_windows_startup(program_name, startup_type)
        elif os_type == "Darwin":
            return self._disable_macos_startup(program_name, startup_type)
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _disable_windows_startup(self, program_name: str, startup_type: str) -> str:
        """Windows Autostart deaktivieren"""
        try:
            output = [
                f"🔧 Deaktiviere Autostart: {program_name}",
                ""
            ]

            safe_name = sanitize_powershell_string(validate_program_name(program_name))

            if startup_type == "registry_hkcu":
                # Registry HKCU Run Key löschen
                ps_cmd = f"Remove-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name '{safe_name}' -ErrorAction Stop"
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    output.append("✅ Registry-Eintrag (HKCU Run) erfolgreich entfernt")
                else:
                    output.append(f"❌ Fehler beim Entfernen: {result.stderr}")

            elif startup_type == "registry_hklm":
                # Registry HKLM Run Key löschen (Administrator-Rechte erforderlich)
                ps_cmd = f"Remove-ItemProperty -Path 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name '{safe_name}' -ErrorAction Stop"
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    output.append("✅ Registry-Eintrag (HKLM Run) erfolgreich entfernt")
                else:
                    output.append(f"❌ Fehler beim Entfernen: {result.stderr}")
                    output.append("⚠️  Administrator-Rechte erforderlich!")

            elif startup_type == "startup_folder":
                # Startup Folder Item löschen
                startup_folder = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
                target_file = startup_folder / program_name

                if target_file.exists():
                    target_file.unlink()
                    output.append(f"✅ Verknüpfung erfolgreich entfernt: {target_file}")
                else:
                    output.append(f"❌ Datei nicht gefunden: {target_file}")

            elif startup_type == "task_scheduler":
                # Task Scheduler Task deaktivieren
                result = subprocess.run(
                    ["schtasks", "/Change", "/TN", program_name, "/DISABLE"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    output.append(f"✅ Scheduled Task '{program_name}' erfolgreich deaktiviert")
                else:
                    output.append(f"❌ Fehler beim Deaktivieren: {result.stderr}")

            else:
                output.append(f"❌ Unbekannter startup_type: {startup_type}")

            output.append("")
            output.append("💡 Tipp: Neustart erforderlich damit Änderungen wirksam werden")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Deaktivieren: {str(e)}"

    def _disable_macos_startup(self, program_name: str, startup_type: str) -> str:
        """macOS Autostart deaktivieren"""
        try:
            output = [
                f"🔧 Deaktiviere Autostart: {program_name}",
                ""
            ]

            safe_name_as = sanitize_applescript_string(validate_program_name(program_name))

            if startup_type == "login_item":
                # Login Item entfernen
                applescript = f'''
                tell application "System Events"
                    delete login item "{safe_name_as}"
                end tell
                '''
                result = subprocess.run(
                    ["osascript", "-e", applescript],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    output.append(f"✅ Login Item '{program_name}' erfolgreich entfernt")
                else:
                    output.append(f"❌ Fehler beim Entfernen: {result.stderr}")

            elif startup_type == "launch_agent_user":
                # LaunchAgent (User) deaktivieren
                agent_path = Path.home() / "Library" / "LaunchAgents" / program_name

                if agent_path.exists():
                    # Unload Agent
                    result = subprocess.run(
                        ["launchctl", "unload", str(agent_path)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        output.append(f"✅ LaunchAgent '{program_name}' erfolgreich deaktiviert")
                    else:
                        output.append(f"⚠️  Agent konnte nicht unloaded werden: {result.stderr}")

                    # Optional: Agent-Datei umbenennen (deaktiviert dauerhaft)
                    disabled_path = agent_path.with_suffix(".plist.disabled")
                    agent_path.rename(disabled_path)
                    output.append(f"✅ Agent-Datei umbenannt: {disabled_path.name}")
                else:
                    output.append(f"❌ Agent nicht gefunden: {agent_path}")

            elif startup_type in ["launch_agent_system", "launch_daemon"]:
                # System LaunchAgent/Daemon (erfordert sudo)
                if startup_type == "launch_agent_system":
                    agent_path = Path("/Library/LaunchAgents") / program_name
                else:
                    agent_path = Path("/Library/LaunchDaemons") / program_name

                if agent_path.exists():
                    output.append(f"⚠️  System-Agent gefunden: {agent_path}")
                    output.append("⚠️  Deaktivierung erfordert Administrator-Rechte (sudo)")
                    output.append("")
                    output.append("Manuell deaktivieren:")
                    output.append(f"  sudo launchctl unload {agent_path}")
                    output.append(f"  sudo mv {agent_path} {agent_path}.disabled")
                else:
                    output.append(f"❌ Agent nicht gefunden: {agent_path}")

            else:
                output.append(f"❌ Unbekannter startup_type: {startup_type}")

            output.append("")
            output.append("💡 Tipp: Neustart empfohlen damit Änderungen wirksam werden")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Deaktivieren: {str(e)}"


class EnableStartupProgramTool(RepairTool):
    """
    Aktiviert ein deaktiviertes Autostart-Programm

    Windows: Registry Run Key hinzufügen, Task aktivieren
    macOS: Login Item hinzufügen, LaunchAgent/Daemon aktivieren
    """

    @property
    def name(self) -> str:
        return "enable_startup_program"

    @property
    def description(self) -> str:
        return (
            "Aktiviert ein Programm im Autostart. Nutze dies bei: "
            "1) Wichtige Programme fehlen beim Start, 2) Nach versehentlichem Deaktivieren, "
            "3) System-Dienste reaktivieren. "
            "WICHTIG: Benötigt Programm-Pfad!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "program_name": {
                    "type": "string",
                    "description": "Name des Programms"
                },
                "program_path": {
                    "type": "string",
                    "description": "Vollständiger Pfad zur ausführbaren Datei"
                },
                "startup_type": {
                    "type": "string",
                    "enum": ["registry_hkcu", "registry_hklm", "task_scheduler", "login_item", "launch_agent_user"],
                    "description": "Typ des Autostart-Eintrags"
                }
            },
            "required": ["program_name", "program_path", "startup_type"]
        }

    async def execute(self, **kwargs) -> str:
        """
        Aktiviert Autostart-Programm

        Args:
            program_name: Name des Programms
            program_path: Pfad zur .exe/.app
            startup_type: Typ des Autostart-Eintrags

        Returns:
            Erfolgs-/Fehlermeldung
        """
        program_name = kwargs.get("program_name")
        program_path = kwargs.get("program_path")
        startup_type = kwargs.get("startup_type")

        if not program_name or not program_path or not startup_type:
            return "❌ Fehler: program_name, program_path und startup_type sind erforderlich"

        os_type = platform.system()

        if os_type == "Windows":
            return self._enable_windows_startup(program_name, program_path, startup_type)
        elif os_type == "Darwin":
            return self._enable_macos_startup(program_name, program_path, startup_type)
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _enable_windows_startup(self, program_name: str, program_path: str, startup_type: str) -> str:
        """Windows Autostart aktivieren"""
        try:
            safe_name = sanitize_powershell_string(validate_program_name(program_name))
            safe_path = sanitize_powershell_string(validate_file_path(program_path))

            output = [
                f"🔧 Aktiviere Autostart: {program_name}",
                ""
            ]

            if startup_type == "registry_hkcu":
                # Registry HKCU Run Key hinzufügen
                ps_cmd = f"Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name '{safe_name}' -Value '{safe_path}'"
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    output.append("✅ Registry-Eintrag (HKCU Run) erfolgreich hinzugefügt")
                    output.append(f"   Pfad: {program_path}")
                else:
                    output.append(f"❌ Fehler beim Hinzufügen: {result.stderr}")

            elif startup_type == "registry_hklm":
                # Registry HKLM Run Key hinzufügen (Administrator-Rechte erforderlich)
                ps_cmd = f"Set-ItemProperty -Path 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name '{safe_name}' -Value '{safe_path}'"
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    output.append("✅ Registry-Eintrag (HKLM Run) erfolgreich hinzugefügt")
                    output.append(f"   Pfad: {program_path}")
                else:
                    output.append(f"❌ Fehler beim Hinzufügen: {result.stderr}")
                    output.append("⚠️  Administrator-Rechte erforderlich!")

            elif startup_type == "task_scheduler":
                # Task Scheduler Task aktivieren
                result = subprocess.run(
                    ["schtasks", "/Change", "/TN", program_name, "/ENABLE"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    output.append(f"✅ Scheduled Task '{program_name}' erfolgreich aktiviert")
                else:
                    output.append(f"❌ Fehler beim Aktivieren: {result.stderr}")

            else:
                output.append(f"❌ Unbekannter startup_type: {startup_type}")

            output.append("")
            output.append("💡 Tipp: Programm startet beim nächsten Login automatisch")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Aktivieren: {str(e)}"

    def _enable_macos_startup(self, program_name: str, program_path: str, startup_type: str) -> str:
        """macOS Autostart aktivieren"""
        try:
            safe_path_as = sanitize_applescript_string(validate_file_path(program_path))

            output = [
                f"🔧 Aktiviere Autostart: {program_name}",
                ""
            ]

            if startup_type == "login_item":
                # Login Item hinzufügen
                applescript = f'''
                tell application "System Events"
                    make login item at end with properties {{path:"{safe_path_as}", hidden:false}}
                end tell
                '''
                result = subprocess.run(
                    ["osascript", "-e", applescript],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    output.append(f"✅ Login Item '{program_name}' erfolgreich hinzugefügt")
                    output.append(f"   Pfad: {program_path}")
                else:
                    output.append(f"❌ Fehler beim Hinzufügen: {result.stderr}")

            elif startup_type == "launch_agent_user":
                # LaunchAgent (User) aktivieren
                agent_path = Path.home() / "Library" / "LaunchAgents" / program_name
                disabled_path = agent_path.with_suffix(".plist.disabled")

                # Wenn disabled Datei existiert, umbenennen
                if disabled_path.exists():
                    disabled_path.rename(agent_path)
                    output.append(f"✅ Agent-Datei reaktiviert: {agent_path.name}")

                if agent_path.exists():
                    # Load Agent
                    result = subprocess.run(
                        ["launchctl", "load", str(agent_path)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0:
                        output.append(f"✅ LaunchAgent '{program_name}' erfolgreich aktiviert")
                    else:
                        output.append(f"⚠️  Agent konnte nicht geladen werden: {result.stderr}")
                else:
                    output.append(f"❌ Agent nicht gefunden: {agent_path}")

            else:
                output.append(f"❌ Unbekannter startup_type: {startup_type}")

            output.append("")
            output.append("💡 Tipp: Programm startet beim nächsten Login automatisch")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Aktivieren: {str(e)}"
