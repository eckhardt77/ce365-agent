"""
CE365 Agent - Startup Programs Audit

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Autostart-Programme auflisten (Windows/macOS)
"""

import platform
import subprocess
import os
from typing import Dict, Any
from pathlib import Path
from ce365.tools.base import AuditTool


class CheckStartupProgramsTool(AuditTool):
    """
    Listet alle Autostart-Programme auf

    Windows: Registry Run Keys, Startup Folder, Task Scheduler
    macOS: Login Items, LaunchAgents, LaunchDaemons
    """

    @property
    def name(self) -> str:
        return "check_startup_programs"

    @property
    def description(self) -> str:
        return (
            "Listet alle Programme auf, die beim System-Start automatisch starten. "
            "Nutze dies bei: 1) Langsames Hochfahren, 2) System-Analyse, "
            "3) Malware-Verdacht, 4) Performance-Optimierung. "
            "Zeigt: Programm-Name, Pfad, Startmethode (Registry/Startup/Task/LaunchAgent)."
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
        Listet Autostart-Programme auf

        Returns:
            Formatierte Liste aller Autostart-Programme
        """
        os_type = platform.system()

        if os_type == "Windows":
            return self._check_windows_startup()
        elif os_type == "Darwin":
            return self._check_macos_startup()
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _check_windows_startup(self) -> str:
        """Windows Autostart-Programme"""
        try:
            output = [
                "🚀 Windows Autostart-Programme",
                ""
            ]

            startup_items = []

            # 1. Registry Run Keys (Current User)
            output.append("📋 Registry Run Keys (Current User):")
            try:
                ps_cmd = """
                Get-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' |
                Select-Object * -ExcludeProperty PS* |
                Format-List
                """
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.stdout.strip():
                    lines = result.stdout.strip().split("\n")
                    current_item = None
                    for line in lines:
                        if ":" in line and not line.startswith(" "):
                            parts = line.split(":", 1)
                            name = parts[0].strip()
                            value = parts[1].strip() if len(parts) > 1 else ""
                            if name and value and name not in ["PSPath", "PSParentPath", "PSChildName", "PSDrive", "PSProvider"]:
                                output.append(f"  • {name}")
                                output.append(f"    Pfad: {value}")
                                startup_items.append({"name": name, "path": value, "type": "Registry (HKCU Run)"})
                else:
                    output.append("  (keine Einträge)")

            except Exception as e:
                output.append(f"  ⚠️  Konnte nicht geprüft werden: {str(e)}")

            output.append("")

            # 2. Registry Run Keys (Local Machine)
            output.append("📋 Registry Run Keys (Local Machine):")
            try:
                ps_cmd = """
                Get-ItemProperty -Path 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' |
                Select-Object * -ExcludeProperty PS* |
                Format-List
                """
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.stdout.strip():
                    lines = result.stdout.strip().split("\n")
                    for line in lines:
                        if ":" in line and not line.startswith(" "):
                            parts = line.split(":", 1)
                            name = parts[0].strip()
                            value = parts[1].strip() if len(parts) > 1 else ""
                            if name and value and name not in ["PSPath", "PSParentPath", "PSChildName", "PSDrive", "PSProvider"]:
                                output.append(f"  • {name}")
                                output.append(f"    Pfad: {value}")
                                startup_items.append({"name": name, "path": value, "type": "Registry (HKLM Run)"})
                else:
                    output.append("  (keine Einträge)")

            except Exception as e:
                output.append(f"  ⚠️  Konnte nicht geprüft werden: {str(e)}")

            output.append("")

            # 3. Startup Folder (Current User)
            output.append("📁 Startup Folder (Current User):")
            try:
                startup_folder = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

                if startup_folder.exists():
                    items = list(startup_folder.glob("*"))
                    if items:
                        for item in items:
                            output.append(f"  • {item.name}")
                            output.append(f"    Pfad: {item}")
                            startup_items.append({"name": item.name, "path": str(item), "type": "Startup Folder (User)"})
                    else:
                        output.append("  (keine Einträge)")
                else:
                    output.append("  (Ordner nicht gefunden)")

            except Exception as e:
                output.append(f"  ⚠️  Konnte nicht geprüft werden: {str(e)}")

            output.append("")

            # 4. Task Scheduler (Autostart Tasks)
            output.append("⏰ Task Scheduler (Autostart bei Login):")
            try:
                ps_cmd = """
                Get-ScheduledTask | Where-Object {
                    $_.Triggers.CimClass.CimClassName -eq 'MSFT_TaskLogonTrigger'
                } | Select-Object TaskName, State, TaskPath | Format-Table -AutoSize
                """
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.stdout.strip():
                    lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
                    if len(lines) > 2:  # Header + Separator + Data
                        for line in lines[2:]:  # Skip header
                            parts = line.split()
                            if parts:
                                task_name = parts[0]
                                state = parts[1] if len(parts) > 1 else "Unknown"
                                output.append(f"  • {task_name} ({state})")
                                startup_items.append({"name": task_name, "path": "Task Scheduler", "type": "Scheduled Task"})
                    else:
                        output.append("  (keine Einträge)")
                else:
                    output.append("  (keine Einträge)")

            except Exception as e:
                output.append(f"  ⚠️  Konnte nicht geprüft werden: {str(e)}")

            output.append("")

            # Zusammenfassung
            output.append("─" * 50)
            output.append(f"📊 Gesamt: {len(startup_items)} Autostart-Programme gefunden")
            output.append("")
            output.append("💡 Tipp:")
            output.append("  • Viele Autostart-Programme verlangsamen den System-Start")
            output.append("  • Deaktiviere ungenutzte Programme mit disable_startup_program")
            output.append("  • Malware versteckt sich oft in Autostart-Einträgen")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Autostart-Check: {str(e)}"

    def _check_macos_startup(self) -> str:
        """macOS Autostart-Programme"""
        try:
            output = [
                "🚀 macOS Autostart-Programme",
                ""
            ]

            startup_items = []

            # 1. Login Items (System Preferences)
            output.append("👤 Login Items (Benutzer):")
            try:
                # osascript to get Login Items
                applescript = '''
                tell application "System Events"
                    get the name of every login item
                end tell
                '''
                result = subprocess.run(
                    ["osascript", "-e", applescript],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.stdout.strip():
                    items = result.stdout.strip().split(", ")
                    for item in items:
                        output.append(f"  • {item}")
                        startup_items.append({"name": item, "path": "Login Items", "type": "Login Item"})
                else:
                    output.append("  (keine Einträge)")

            except Exception as e:
                output.append(f"  ⚠️  Konnte nicht geprüft werden: {str(e)}")

            output.append("")

            # 2. LaunchAgents (User)
            output.append("🔧 LaunchAgents (Benutzer):")
            try:
                launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
                if launch_agents_dir.exists():
                    agents = list(launch_agents_dir.glob("*.plist"))
                    if agents:
                        for agent in agents:
                            output.append(f"  • {agent.name}")
                            startup_items.append({"name": agent.name, "path": str(agent), "type": "LaunchAgent (User)"})
                    else:
                        output.append("  (keine Einträge)")
                else:
                    output.append("  (Ordner nicht gefunden)")

            except Exception as e:
                output.append(f"  ⚠️  Konnte nicht geprüft werden: {str(e)}")

            output.append("")

            # 3. LaunchAgents (System)
            output.append("🔧 LaunchAgents (System):")
            try:
                system_agents_dir = Path("/Library/LaunchAgents")
                if system_agents_dir.exists():
                    agents = list(system_agents_dir.glob("*.plist"))
                    if agents:
                        for agent in agents:
                            output.append(f"  • {agent.name}")
                            startup_items.append({"name": agent.name, "path": str(agent), "type": "LaunchAgent (System)"})
                    else:
                        output.append("  (keine Einträge)")
                else:
                    output.append("  (Ordner nicht gefunden)")

            except Exception as e:
                output.append(f"  ⚠️  Konnte nicht geprüft werden: {str(e)}")

            output.append("")

            # 4. LaunchDaemons (System)
            output.append("⚙️  LaunchDaemons (System):")
            try:
                daemons_dir = Path("/Library/LaunchDaemons")
                if daemons_dir.exists():
                    daemons = list(daemons_dir.glob("*.plist"))
                    if daemons:
                        for daemon in daemons:
                            output.append(f"  • {daemon.name}")
                            startup_items.append({"name": daemon.name, "path": str(daemon), "type": "LaunchDaemon"})
                    else:
                        output.append("  (keine Einträge)")
                else:
                    output.append("  (Ordner nicht gefunden)")

            except Exception as e:
                output.append(f"  ⚠️  Konnte nicht geprüft werden: {str(e)}")

            output.append("")

            # Zusammenfassung
            output.append("─" * 50)
            output.append(f"📊 Gesamt: {len(startup_items)} Autostart-Programme gefunden")
            output.append("")
            output.append("💡 Tipp:")
            output.append("  • Zu viele Autostart-Programme verlangsamen den Start")
            output.append("  • Login Items: System Preferences → Users & Groups → Login Items")
            output.append("  • LaunchAgents/Daemons: Nur ändern wenn du weißt was du tust")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Autostart-Check: {str(e)}"
