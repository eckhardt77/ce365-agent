"""
CE365 Agent - Update Check Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Update-Status prüfen:
- Windows: Windows Update (PSWindowsUpdate oder WUAPI)
- macOS: Software Update
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import AuditTool


class CheckSystemUpdatesTool(AuditTool):
    """
    Prüft auf verfügbare System-Updates

    Windows: Windows Update
    macOS: Software Update
    """

    @property
    def name(self) -> str:
        return "check_system_updates"

    @property
    def description(self) -> str:
        return (
            "Prüft auf verfügbare System-Updates (Windows Update / macOS Software Update). "
            "Nutze dies bei: 1) Regelmäßiger Wartung, 2) Sicherheitsupdates, "
            "3) Vor größeren Änderungen, 4) Performance-Problemen. "
            "Zeigt verfügbare Updates mit Details (Größe, Typ, KB-Nummer)."
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
        Prüft System-Updates

        Returns:
            Liste verfügbarer Updates oder "Aktuell"
        """
        os_type = platform.system()

        if os_type == "Windows":
            return self._check_windows_updates()
        elif os_type == "Darwin":
            return self._check_macos_updates()
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _check_windows_updates(self) -> str:
        """Windows Update Status prüfen"""
        try:
            # Methode 1: PowerShell Get-WindowsUpdate (erfordert PSWindowsUpdate Modul)
            ps_cmd = """
            if (Get-Module -ListAvailable -Name PSWindowsUpdate) {
                Import-Module PSWindowsUpdate
                Get-WindowsUpdate -MicrosoftUpdate |
                Select-Object KB, Title, Size, IsDownloaded, IsInstalled |
                ConvertTo-Json
            } else {
                Write-Output "PSWindowsUpdate_NOT_INSTALLED"
            }
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=60
            )

            # PSWindowsUpdate Modul fehlt?
            if "PSWindowsUpdate_NOT_INSTALLED" in result.stdout:
                return self._check_windows_updates_fallback()

            # Parse JSON
            import json
            try:
                updates = json.loads(result.stdout)

                if not updates:
                    return (
                        "✅ Windows Update Status\n\n"
                        "Keine Updates verfügbar.\n"
                        "System ist aktuell."
                    )

                # Sicherstellen dass updates Liste ist
                if not isinstance(updates, list):
                    updates = [updates]

                output = [
                    "🔄 Windows Update Status",
                    f"📊 {len(updates)} Update(s) verfügbar\n"
                ]

                for update in updates:
                    kb = update.get("KB", "Unbekannt")
                    title = update.get("Title", "Unbekannt")
                    size_mb = update.get("Size", 0) / (1024 * 1024) if update.get("Size") else 0
                    downloaded = "✓" if update.get("IsDownloaded") else "○"

                    output.append(f"📦 KB{kb}")
                    output.append(f"   {title}")
                    output.append(f"   Größe: {size_mb:.1f} MB | Download: {downloaded}")
                    output.append("")

                output.append("💡 Tipp: Nutze 'install_system_updates' zum Installieren")

                return "\n".join(output)

            except json.JSONDecodeError:
                return self._check_windows_updates_fallback()

        except subprocess.TimeoutExpired:
            return "❌ Timeout bei Update-Check (>60s)"
        except Exception as e:
            return f"❌ Fehler bei Update-Check: {str(e)}"

    def _check_windows_updates_fallback(self) -> str:
        """Fallback ohne PSWindowsUpdate Modul"""
        try:
            # Methode 2: Windows Update Service Status prüfen
            ps_cmd = """
            $updateSession = New-Object -ComObject Microsoft.Update.Session
            $updateSearcher = $updateSession.CreateUpdateSearcher()
            $searchResult = $updateSearcher.Search("IsInstalled=0")

            if ($searchResult.Updates.Count -eq 0) {
                Write-Output "NO_UPDATES"
            } else {
                Write-Output "UPDATES_AVAILABLE:$($searchResult.Updates.Count)"
                foreach ($update in $searchResult.Updates) {
                    Write-Output "---"
                    Write-Output "Title:$($update.Title)"
                    Write-Output "KB:$($update.KBArticleIDs -join ',')"
                    Write-Output "Size:$([math]::Round($update.MaxDownloadSize / 1MB, 1)) MB"
                }
            }
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=120
            )

            if "NO_UPDATES" in result.stdout:
                return (
                    "✅ Windows Update Status\n\n"
                    "Keine Updates verfügbar.\n"
                    "System ist aktuell."
                )

            # Parse Output
            lines = result.stdout.strip().split("\n")
            updates = []
            current_update = {}

            for line in lines:
                if line.startswith("UPDATES_AVAILABLE:"):
                    count = line.split(":")[1]
                    continue
                elif line == "---":
                    if current_update:
                        updates.append(current_update)
                        current_update = {}
                elif ":" in line:
                    key, value = line.split(":", 1)
                    current_update[key] = value

            if current_update:
                updates.append(current_update)

            output = [
                "🔄 Windows Update Status",
                f"📊 {len(updates)} Update(s) verfügbar\n"
            ]

            for update in updates:
                title = update.get("Title", "Unbekannt")
                kb = update.get("KB", "Unbekannt")
                size = update.get("Size", "Unbekannt")

                output.append(f"📦 {title}")
                if kb != "Unbekannt":
                    output.append(f"   KB: {kb}")
                output.append(f"   Größe: {size}")
                output.append("")

            output.append("💡 Tipp: Nutze 'install_system_updates' zum Installieren")

            return "\n".join(output)

        except Exception as e:
            return (
                "⚠️  Windows Update Check (Fallback-Methode)\n\n"
                f"Konnte Update-Status nicht ermitteln: {str(e)}\n\n"
                "Empfehlung: Prüfe Windows Update manuell (Settings → Update & Security)"
            )

    def _check_macos_updates(self) -> str:
        """macOS Software Update Status prüfen"""
        try:
            # softwareupdate -l
            result = subprocess.run(
                ["softwareupdate", "-l"],
                capture_output=True,
                text=True,
                timeout=60
            )

            output_text = result.stdout

            # Keine Updates?
            if "No new software available" in output_text or "No updates are available" in output_text:
                return (
                    "✅ macOS Software Update Status\n\n"
                    "Keine Updates verfügbar.\n"
                    "System ist aktuell."
                )

            # Parse Updates
            lines = output_text.split("\n")
            updates = []

            for line in lines:
                line = line.strip()
                if line.startswith("*") or line.startswith("-"):
                    # Update gefunden
                    update_line = line.lstrip("*- ")
                    if update_line:
                        updates.append(update_line)

            if not updates:
                return (
                    "✅ macOS Software Update Status\n\n"
                    "Keine Updates verfügbar.\n"
                    "System ist aktuell."
                )

            output = [
                "🔄 macOS Software Update Status",
                f"📊 {len(updates)} Update(s) verfügbar\n"
            ]

            for update in updates:
                output.append(f"📦 {update}")

            output.append("")
            output.append("💡 Tipp: Nutze 'install_system_updates' zum Installieren")

            return "\n".join(output)

        except subprocess.TimeoutExpired:
            return "❌ Timeout bei Update-Check (>60s)"
        except Exception as e:
            return f"❌ Fehler bei Update-Check: {str(e)}"
