"""
CE365 Agent - Task Scheduler Management

Erstellt, loescht, aktiviert und deaktiviert geplante Aufgaben:
- Windows: schtasks.exe (CE365-Ordner im Task Scheduler)
- macOS: LaunchAgents (~/Library/LaunchAgents/)
"""

import os
import platform
import re
import subprocess
from pathlib import Path
from typing import Dict, Any

from ce365.tools.base import RepairTool


def _run_cmd(cmd: list, timeout: int = 30) -> tuple:
    """Gibt (success, output) zurueck"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return False, str(e)


def _sanitize_name(name: str) -> str:
    """Nur alphanumerisch, Bindestrich und Unterstrich erlauben"""
    return re.sub(r"[^a-zA-Z0-9_-]", "", name)


def _build_plist(label: str, command: str, schedule: str,
                 time: str = "", day_of_week: str = "",
                 description: str = "") -> str:
    """Baut eine LaunchAgent plist-XML"""
    # ProgramArguments aus Command-String
    parts = command.split()
    program_args = "\n".join(f"            <string>{p}</string>" for p in parts)

    schedule_block = ""
    if schedule == "hourly":
        schedule_block = """
        <key>StartInterval</key>
        <integer>3600</integer>"""
    elif schedule in ("login", "startup"):
        schedule_block = """
        <key>RunAtLoad</key>
        <true/>"""
    elif schedule in ("daily", "weekly"):
        hour, minute = 9, 0
        if time:
            try:
                h, m = time.split(":")
                hour, minute = int(h), int(m)
            except ValueError:
                pass

        if schedule == "daily":
            schedule_block = f"""
        <key>StartCalendarInterval</key>
        <dict>
            <key>Hour</key>
            <integer>{hour}</integer>
            <key>Minute</key>
            <integer>{minute}</integer>
        </dict>"""
        else:
            # weekly
            day_map = {
                "MON": 1, "TUE": 2, "WED": 3, "THU": 4,
                "FRI": 5, "SAT": 6, "SUN": 7,
            }
            weekday = day_map.get(day_of_week.upper(), 1)
            schedule_block = f"""
        <key>StartCalendarInterval</key>
        <dict>
            <key>Weekday</key>
            <integer>{weekday}</integer>
            <key>Hour</key>
            <integer>{hour}</integer>
            <key>Minute</key>
            <integer>{minute}</integer>
        </dict>"""

    desc_block = ""
    if description:
        desc_block = f"""
        <key>Label</key>
        <string>{label} - {description}</string>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
{program_args}
    </array>{schedule_block}
    <key>StandardOutPath</key>
    <string>/tmp/{label}.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/{label}.err</string>
</dict>
</plist>
"""


class ManageScheduledTaskTool(RepairTool):
    """Geplante Aufgaben erstellen, loeschen, aktivieren oder deaktivieren"""

    @property
    def name(self) -> str:
        return "manage_scheduled_task"

    @property
    def description(self) -> str:
        return (
            "Erstellt, loescht, aktiviert oder deaktiviert geplante Aufgaben. "
            "Nutze dies fuer: 1) Regelmaessige Wartungsaufgaben planen (Cleanup, Backup, Updates), "
            "2) Bestehende Tasks aktivieren/deaktivieren, "
            "3) Nicht mehr benoetigte Tasks entfernen. "
            "Windows: schtasks.exe (CE365-Ordner), macOS: LaunchAgents. "
            "Erfordert GO REPAIR Freigabe!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "delete", "enable", "disable"],
                    "description": "Aktion: create, delete, enable oder disable",
                },
                "task_name": {
                    "type": "string",
                    "description": "Name der Aufgabe (alphanumerisch, Bindestrich, Unterstrich)",
                },
                "command": {
                    "type": "string",
                    "description": "Befehl der ausgefuehrt wird (Pflicht bei create)",
                },
                "schedule": {
                    "type": "string",
                    "enum": ["daily", "weekly", "hourly", "login", "startup"],
                    "description": "Zeitplan: daily, weekly, hourly, login, startup",
                },
                "time": {
                    "type": "string",
                    "description": "Uhrzeit im Format HH:MM (bei daily/weekly)",
                },
                "day_of_week": {
                    "type": "string",
                    "description": "Wochentag bei weekly: MON, TUE, WED, THU, FRI, SAT, SUN",
                },
                "description": {
                    "type": "string",
                    "description": "Optionale Beschreibung der Aufgabe",
                },
            },
            "required": ["action", "task_name"],
        }

    async def execute(self, **kwargs) -> str:
        action = kwargs.get("action", "")
        task_name = _sanitize_name(kwargs.get("task_name", ""))
        command = kwargs.get("command", "")
        schedule = kwargs.get("schedule", "daily")
        time_str = kwargs.get("time", "")
        day_of_week = kwargs.get("day_of_week", "MON")
        description = kwargs.get("description", "")

        if not task_name:
            return "❌ task_name ist erforderlich (alphanumerisch, Bindestrich, Unterstrich)"

        if action == "create" and not command:
            return "❌ command ist bei create erforderlich"

        system = platform.system()

        if system == "Windows":
            return self._windows(action, task_name, command, schedule,
                                 time_str, day_of_week, description)
        elif system == "Darwin":
            return self._macos(action, task_name, command, schedule,
                               time_str, day_of_week, description)
        else:
            return f"❌ Betriebssystem '{system}' wird nicht unterstuetzt (nur Windows/macOS)"

    # --- Windows -----------------------------------------------------------

    def _windows(self, action: str, name: str, command: str, schedule: str,
                 time_str: str, day_of_week: str, description: str) -> str:
        tn = f"CE365\\{name}"
        lines = ["🔧 TASK SCHEDULER (Windows)", "=" * 50, ""]

        if action == "create":
            args = ["schtasks", "/create", "/tn", tn, "/tr", command, "/f"]

            sc_map = {
                "daily": "daily", "weekly": "weekly", "hourly": "hourly",
                "login": "onlogon", "startup": "onstart",
            }
            args += ["/sc", sc_map.get(schedule, "daily")]

            if schedule in ("daily", "weekly") and time_str:
                args += ["/st", time_str]
            if schedule == "weekly":
                args += ["/d", day_of_week.upper()]

            success, output = _run_cmd(args)
            if success:
                lines.append(f"✅ Task '{tn}' erstellt")
                lines.append(f"   Befehl: {command}")
                lines.append(f"   Zeitplan: {schedule}")
                if time_str:
                    lines.append(f"   Uhrzeit: {time_str}")
            else:
                lines.append(f"❌ Fehler beim Erstellen: {output}")

        elif action == "delete":
            success, output = _run_cmd(["schtasks", "/delete", "/tn", tn, "/f"])
            if success:
                lines.append(f"✅ Task '{tn}' geloescht")
            else:
                lines.append(f"❌ Fehler beim Loeschen: {output}")

        elif action == "enable":
            success, output = _run_cmd(["schtasks", "/change", "/tn", tn, "/enable"])
            if success:
                lines.append(f"✅ Task '{tn}' aktiviert")
            else:
                lines.append(f"❌ Fehler beim Aktivieren: {output}")

        elif action == "disable":
            success, output = _run_cmd(["schtasks", "/change", "/tn", tn, "/disable"])
            if success:
                lines.append(f"✅ Task '{tn}' deaktiviert")
            else:
                lines.append(f"❌ Fehler beim Deaktivieren: {output}")

        else:
            lines.append(f"❌ Unbekannte Aktion: {action}")

        return "\n".join(lines)

    # --- macOS -------------------------------------------------------------

    def _macos(self, action: str, name: str, command: str, schedule: str,
               time_str: str, day_of_week: str, description: str) -> str:
        label = f"com.ce365.{name}"
        agents_dir = Path.home() / "Library" / "LaunchAgents"
        plist_path = agents_dir / f"{label}.plist"
        lines = ["🔧 TASK SCHEDULER (macOS LaunchAgent)", "=" * 50, ""]

        if action == "create":
            # Sicherstellen dass LaunchAgents-Ordner existiert
            agents_dir.mkdir(parents=True, exist_ok=True)

            plist_content = _build_plist(
                label, command, schedule, time_str, day_of_week, description
            )

            try:
                plist_path.write_text(plist_content, encoding="utf-8")
                lines.append(f"✅ Plist geschrieben: {plist_path}")
            except Exception as e:
                lines.append(f"❌ Fehler beim Schreiben: {e}")
                return "\n".join(lines)

            success, output = _run_cmd(["launchctl", "load", str(plist_path)])
            if success:
                lines.append(f"✅ LaunchAgent '{label}' geladen")
                lines.append(f"   Befehl: {command}")
                lines.append(f"   Zeitplan: {schedule}")
                if time_str:
                    lines.append(f"   Uhrzeit: {time_str}")
            else:
                lines.append(f"⚠️ Plist geschrieben, aber launchctl load fehlgeschlagen: {output}")

        elif action == "delete":
            if plist_path.exists():
                _run_cmd(["launchctl", "unload", str(plist_path)])
                try:
                    plist_path.unlink()
                    lines.append(f"✅ LaunchAgent '{label}' entladen und geloescht")
                except Exception as e:
                    lines.append(f"❌ Entladen OK, aber Loeschen fehlgeschlagen: {e}")
            else:
                lines.append(f"❌ Plist nicht gefunden: {plist_path}")

        elif action == "enable":
            if plist_path.exists():
                success, output = _run_cmd(["launchctl", "load", str(plist_path)])
                if success:
                    lines.append(f"✅ LaunchAgent '{label}' aktiviert")
                else:
                    lines.append(f"❌ Fehler beim Aktivieren: {output}")
            else:
                lines.append(f"❌ Plist nicht gefunden: {plist_path}")

        elif action == "disable":
            if plist_path.exists():
                success, output = _run_cmd(["launchctl", "unload", str(plist_path)])
                if success:
                    lines.append(f"✅ LaunchAgent '{label}' deaktiviert")
                else:
                    lines.append(f"❌ Fehler beim Deaktivieren: {output}")
            else:
                lines.append(f"❌ Plist nicht gefunden: {plist_path}")

        else:
            lines.append(f"❌ Unbekannte Aktion: {action}")

        return "\n".join(lines)
