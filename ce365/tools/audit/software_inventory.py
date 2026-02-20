"""
CE365 Agent - Software Inventory

Alle installierten Programme auflisten
macOS: system_profiler SPApplicationsDataType
Windows: wmic product / Registry
"""

import platform
from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.core.command_runner import get_command_runner


def _run_cmd(cmd: list, timeout: int = 30) -> str:
    result = get_command_runner().run_sync(cmd, timeout=timeout)
    return result.stdout if result.success else ""


class SoftwareInventoryTool(AuditTool):
    """Listet alle installierten Programme auf"""

    @property
    def name(self) -> str:
        return "list_installed_software"

    @property
    def description(self) -> str:
        return (
            "Listet alle installierten Programme/Anwendungen auf. "
            "Nutze dies bei: 1) Software-Audit, 2) Suche nach bestimmter Software, "
            "3) Veraltete Programme identifizieren, 4) Lizenz-Inventur, "
            "5) Vor System-Migration. "
            "Zeigt Name, Version und Hersteller."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "description": "Filtert nach Name (z.B. 'Microsoft', 'Adobe', 'Chrome')",
                    "default": "",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        name_filter = kwargs.get("filter", "").lower()
        os_type = platform.system()

        lines = ["📦 INSTALLIERTE SOFTWARE", "=" * 50, ""]

        if os_type == "Darwin":
            apps = self._get_macos_apps(name_filter)
        elif os_type == "Windows":
            apps = self._get_windows_apps(name_filter)
        else:
            return "❌ Nicht unterstuetztes Betriebssystem"

        if not apps:
            if name_filter:
                lines.append(f"Keine Software mit '{name_filter}' gefunden.")
            else:
                lines.append("Keine installierte Software gefunden.")
            return "\n".join(lines)

        # Sortiert nach Name
        apps.sort(key=lambda x: x.get("name", "").lower())

        for app in apps:
            name = app.get("name", "Unbekannt")
            version = app.get("version", "")
            vendor = app.get("vendor", "")

            line = f"  • {name}"
            if version:
                line += f" (v{version})"
            if vendor:
                line += f" — {vendor}"
            lines.append(line)

        lines.append("")
        lines.append(f"Gesamt: {len(apps)} Programme")
        if name_filter:
            lines.append(f"Filter: '{name_filter}'")

        return "\n".join(lines)

    def _get_macos_apps(self, name_filter: str) -> list:
        """macOS: system_profiler SPApplicationsDataType"""
        apps = []

        output = _run_cmd(
            ["system_profiler", "SPApplicationsDataType", "-detailLevel", "mini"],
            timeout=30,
        )

        if not output:
            return apps

        current_app = {}
        for line in output.splitlines():
            stripped = line.strip()

            if stripped.endswith(":") and not stripped.startswith(("Version", "Location", "Obtained", "Last Modified", "Kind", "Signed", "Get Info")):
                # Neue App
                if current_app.get("name"):
                    if not name_filter or name_filter in current_app["name"].lower():
                        apps.append(current_app)
                current_app = {"name": stripped.rstrip(":")}
            elif stripped.startswith("Version:"):
                current_app["version"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("Obtained from:"):
                current_app["vendor"] = stripped.split(":", 1)[1].strip()

        # Letzte App
        if current_app.get("name"):
            if not name_filter or name_filter in current_app["name"].lower():
                apps.append(current_app)

        return apps

    def _get_windows_apps(self, name_filter: str) -> list:
        """Windows: Registry-basiert (schneller als wmic product)"""
        apps = []

        # PowerShell Registry-Abfrage (viel schneller als wmic product)
        ps_cmd = (
            "Get-ItemProperty "
            "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*, "
            "HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* "
            "2>$null | "
            "Where-Object { $_.DisplayName -ne $null } | "
            "Select-Object DisplayName, DisplayVersion, Publisher | "
            "Sort-Object DisplayName | "
            "ForEach-Object { \"$($_.DisplayName)|$($_.DisplayVersion)|$($_.Publisher)\" }"
        )

        output = _run_cmd(["powershell", "-Command", ps_cmd], timeout=30)

        if not output:
            return apps

        seen = set()
        for line in output.splitlines():
            parts = line.strip().split("|")
            if len(parts) >= 1 and parts[0]:
                name = parts[0].strip()
                if name in seen:
                    continue
                seen.add(name)

                if name_filter and name_filter not in name.lower():
                    continue

                app = {"name": name}
                if len(parts) >= 2 and parts[1].strip():
                    app["version"] = parts[1].strip()
                if len(parts) >= 3 and parts[2].strip():
                    app["vendor"] = parts[2].strip()
                apps.append(app)

        return apps
