"""
CE365 Agent - Scheduled Tasks Audit

Geplante Aufgaben auflisten
Windows: schtasks / Task Scheduler
macOS: launchd (LaunchAgents/LaunchDaemons) + crontab
"""

import platform
import os
from pathlib import Path
from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.core.command_runner import get_command_runner


def _run_cmd(cmd: list, timeout: int = 15) -> str:
    result = get_command_runner().run_sync(cmd, timeout=timeout)
    return result.stdout if result.success else ""


class ScheduledTasksAuditTool(AuditTool):
    """Alle geplanten Aufgaben / Tasks auflisten"""

    @property
    def name(self) -> str:
        return "audit_scheduled_tasks"

    @property
    def description(self) -> str:
        return (
            "Listet alle geplanten Aufgaben auf dem System. "
            "Windows: Task Scheduler Aufgaben. "
            "macOS: LaunchAgents, LaunchDaemons, Cron-Jobs. "
            "Nutze dies bei: 1) Unerwartete Hintergrund-Aktivitaet, "
            "2) Sicherheits-Audit, 3) Performance-Probleme, "
            "4) Verdaechtige geplante Tasks identifizieren."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "description": "Filter nach Name (z.B. 'Microsoft', 'Google')",
                    "default": "",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        name_filter = kwargs.get("filter", "").lower()
        os_type = platform.system()
        lines = ["📋 GEPLANTE AUFGABEN", "=" * 50, ""]

        if os_type == "Windows":
            lines.extend(self._audit_windows(name_filter))
        elif os_type == "Darwin":
            lines.extend(self._audit_macos(name_filter))
        else:
            lines.append("❌ Nicht unterstuetztes Betriebssystem")

        return "\n".join(lines)

    def _audit_windows(self, name_filter: str) -> list:
        lines = []

        # schtasks im CSV-Format
        output = _run_cmd(
            ["schtasks", "/Query", "/FO", "CSV", "/NH", "/V"],
            timeout=30,
        )

        if not output:
            # Fallback: einfaches Format
            output = _run_cmd(["schtasks", "/Query", "/FO", "TABLE"], timeout=30)
            if output:
                for line in output.splitlines()[:50]:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("="):
                        if name_filter and name_filter not in stripped.lower():
                            continue
                        lines.append(f"   {stripped}")
            else:
                lines.append("❌ Konnte Tasks nicht auflisten (Admin-Rechte erforderlich?)")
            return lines

        # CSV parsen
        tasks = []
        for line in output.splitlines():
            # CSV: "HostName","TaskName","Next Run","Status","Logon Mode",...
            parts = line.strip().strip('"').split('","')
            if len(parts) >= 4:
                task_name = parts[1] if len(parts) > 1 else ""
                next_run = parts[2] if len(parts) > 2 else ""
                status = parts[3] if len(parts) > 3 else ""

                if name_filter and name_filter not in task_name.lower():
                    continue

                # System-Tasks filtern (nur Top-Level zeigen)
                if task_name.startswith("\\Microsoft\\") and not name_filter:
                    continue  # Microsoft System-Tasks ausblenden

                tasks.append({
                    "name": task_name,
                    "next_run": next_run,
                    "status": status,
                })

        if tasks:
            for task in tasks[:50]:
                status_icon = "🟢" if task["status"] == "Ready" else "⚪"
                lines.append(f"   {status_icon} {task['name']}")
                if task["next_run"] and task["next_run"] != "N/A":
                    lines.append(f"      Naechste Ausfuehrung: {task['next_run']}")
        else:
            lines.append("   Keine benutzerdefinierten Tasks gefunden.")
            if not name_filter:
                lines.append("   (Microsoft System-Tasks werden standardmaessig ausgeblendet)")

        lines.append("")
        lines.append(f"Gesamt: {len(tasks)} Tasks angezeigt")

        return lines

    def _audit_macos(self, name_filter: str) -> list:
        lines = []
        total = 0

        # 1. User LaunchAgents
        user_agents_dir = Path.home() / "Library/LaunchAgents"
        lines.append("👤 User LaunchAgents:")
        user_count = self._list_launchd_dir(user_agents_dir, lines, name_filter)
        total += user_count
        lines.append("")

        # 2. System LaunchAgents
        sys_agents_dir = Path("/Library/LaunchAgents")
        lines.append("🖥️  System LaunchAgents:")
        sys_count = self._list_launchd_dir(sys_agents_dir, lines, name_filter)
        total += sys_count
        lines.append("")

        # 3. System LaunchDaemons
        sys_daemons_dir = Path("/Library/LaunchDaemons")
        lines.append("⚙️  System LaunchDaemons:")
        daemon_count = self._list_launchd_dir(sys_daemons_dir, lines, name_filter)
        total += daemon_count
        lines.append("")

        # 4. Cron-Jobs
        lines.append("⏰ Cron-Jobs:")
        cron_output = _run_cmd(["crontab", "-l"], timeout=5)
        cron_count = 0
        if cron_output and "no crontab" not in cron_output.lower():
            for line in cron_output.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    if name_filter and name_filter not in stripped.lower():
                        continue
                    lines.append(f"   ⏰ {stripped}")
                    cron_count += 1
                    total += 1
        if cron_count == 0:
            lines.append("   Keine Cron-Jobs")

        lines.append("")
        lines.append(f"Gesamt: {total} geplante Aufgaben")

        return lines

    def _list_launchd_dir(self, directory: Path, lines: list, name_filter: str) -> int:
        count = 0
        if not directory.exists():
            lines.append("   (Verzeichnis existiert nicht)")
            return 0

        try:
            plists = sorted(directory.glob("*.plist"))
            for plist in plists:
                label = plist.stem
                if name_filter and name_filter not in label.lower():
                    continue

                # Pruefen ob geladen
                launchctl_out = _run_cmd(["launchctl", "list", label], timeout=3)
                is_loaded = bool(launchctl_out) and "Could not find" not in launchctl_out

                icon = "🟢" if is_loaded else "⚪"
                status = "Geladen" if is_loaded else "Nicht geladen"
                lines.append(f"   {icon} {label} [{status}]")
                count += 1

            if count == 0:
                lines.append("   (Leer)")
        except PermissionError:
            lines.append("   ❌ Keine Berechtigung")

        return count
