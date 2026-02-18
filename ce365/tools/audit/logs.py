"""
CE365 Agent - Log Analysis Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

System-Logs analysieren:
- Windows: Event Viewer (System + Application)
- macOS: Unified Logging System
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import AuditTool


class CheckSystemLogsTool(AuditTool):
    """
    Analysiert System-Logs nach Fehlern der letzten 24h

    Windows: Event Viewer (System-Log)
    macOS: Unified Logging mit log show
    """

    @property
    def name(self) -> str:
        return "check_system_logs"

    @property
    def description(self) -> str:
        return (
            "Analysiert System-Logs der letzten 24 Stunden auf Fehler. "
            "Nutze dies bei: 1) Unklaren Problemen, 2) System-Crashes, "
            "3) Service-Fehlern, 4) Boot-Problemen. "
            "Liefert die wichtigsten Fehler-Meldungen mit Timestamps."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "Zeitraum in Stunden (Standard: 24)",
                    "default": 24
                },
                "max_entries": {
                    "type": "integer",
                    "description": "Maximale Anzahl Einträge (Standard: 50)",
                    "default": 50
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Analysiert System-Logs

        Args:
            hours: Zeitraum in Stunden (default: 24)
            max_entries: Max. Anzahl Einträge (default: 50)

        Returns:
            Formatierte Log-Einträge mit Fehler-Level
        """
        hours = kwargs.get("hours", 24)
        max_entries = kwargs.get("max_entries", 50)

        os_type = platform.system()

        if os_type == "Windows":
            return self._check_windows_logs(hours, max_entries)
        elif os_type == "Darwin":
            return self._check_macos_logs(hours, max_entries)
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _check_windows_logs(self, hours: int, max_entries: int) -> str:
        """Windows Event Viewer Fehler"""
        try:
            # PowerShell Kommando für Event Log
            ps_cmd = f"""
            Get-EventLog -LogName System -EntryType Error -Newest {max_entries} |
            Where-Object {{$_.TimeGenerated -gt (Get-Date).AddHours(-{hours})}} |
            Select-Object TimeGenerated, Source, EventID, Message |
            ConvertTo-Json
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return f"❌ Fehler beim Auslesen: {result.stderr}"

            # Parse und formatiere
            import json
            try:
                events = json.loads(result.stdout)
                if not events:
                    return f"✓ Keine Fehler in den letzten {hours}h gefunden"

                # Sicherstellen dass events Liste ist
                if not isinstance(events, list):
                    events = [events]

                output = [
                    f"🔍 Windows Event Log - Fehler der letzten {hours}h",
                    f"📊 {len(events)} Fehler gefunden\n"
                ]

                for event in events[:max_entries]:
                    time = event.get("TimeGenerated", "Unknown")
                    source = event.get("Source", "Unknown")
                    event_id = event.get("EventID", "Unknown")
                    message = event.get("Message", "No message")[:200]

                    output.append(f"⚠️  {time}")
                    output.append(f"   Source: {source}")
                    output.append(f"   Event ID: {event_id}")
                    output.append(f"   {message}...")
                    output.append("")

                return "\n".join(output)

            except json.JSONDecodeError:
                # Fallback: Raw output
                return f"🔍 Windows Event Log (letzten {hours}h):\n\n{result.stdout[:2000]}"

        except subprocess.TimeoutExpired:
            return "❌ Timeout beim Auslesen der Event Logs (>30s)"
        except Exception as e:
            return f"❌ Fehler: {str(e)}"

    def _check_macos_logs(self, hours: int, max_entries: int) -> str:
        """macOS Unified Logging"""
        try:
            # log show mit Fehler-Filter
            cmd = [
                "log", "show",
                "--predicate", 'messageType == "Error" or messageType == "Fault"',
                "--style", "compact",
                "--last", f"{hours}h"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return f"❌ Fehler beim Auslesen: {result.stderr}"

            lines = result.stdout.strip().split("\n")

            if not lines or len(lines) == 0:
                return f"✓ Keine Fehler in den letzten {hours}h gefunden"

            # Limitiere Ausgabe
            lines = lines[:max_entries]

            output = [
                f"🔍 macOS System Log - Fehler der letzten {hours}h",
                f"📊 {len(lines)} Fehler gefunden\n"
            ]

            for line in lines:
                if line.strip():
                    output.append(f"⚠️  {line}")

            return "\n".join(output)

        except subprocess.TimeoutExpired:
            return "❌ Timeout beim Auslesen der Logs (>30s)"
        except Exception as e:
            return f"❌ Fehler: {str(e)}"
