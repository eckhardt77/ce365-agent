"""
TechCare Bot - Root Cause Analysis Tool

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

AI-gesteuerte Ursachenanalyse:
- Korreliert Event Logs, Services, System Metrics
- Identifiziert ROOT CAUSE statt nur Symptome
- Gibt Confidence Score und Beweise
"""

import asyncio
import json
import platform
import subprocess
from datetime import datetime, timedelta
from typing import Optional

from techcare.tools.base import AuditTool
from techcare.i18n import get_translator


class RootCauseAnalyzer(AuditTool):
    """
    AI Root Cause Analysis

    Analysiert IT-Probleme und findet die wahre Ursache
    """

    name = "analyze_root_cause"
    description = "AI-powered root cause analysis for IT problems"

    input_schema = {
        "type": "object",
        "properties": {
            "problem_description": {
                "type": "string",
                "description": "User's description of the problem (e.g., 'Windows Update not working')"
            },
            "timeframe_hours": {
                "type": "integer",
                "description": "How far back to analyze (in hours, default: 24)",
                "default": 24
            },
            "include_metrics": {
                "type": "boolean",
                "description": "Include system metrics (CPU/RAM/Disk) in analysis",
                "default": True
            }
        },
        "required": ["problem_description"]
    }

    def __init__(self):
        super().__init__()
        self.t = get_translator()
        self.os_type = platform.system()

    async def execute(
        self,
        problem_description: str,
        timeframe_hours: int = 24,
        include_metrics: bool = True
    ) -> dict:
        """
        Führt Root-Cause-Analyse durch

        Args:
            problem_description: Problem-Beschreibung vom User
            timeframe_hours: Analyse-Zeitraum (default 24h)
            include_metrics: System-Metriken einbeziehen

        Returns:
            Root Cause mit Confidence Score, Beweisen, Lösungs-Vorschlag
        """

        print(self.t.t("root_cause.analyzing"))

        # 1. Daten parallel sammeln
        data = await self._collect_diagnostic_data(timeframe_hours, include_metrics)

        # 2. AI-Analyse vorbereiten
        analysis_prompt = self._build_analysis_prompt(problem_description, data)

        # 3. Claude API für Analyse nutzen (wird vom Bot selbst aufgerufen)
        # Hier geben wir nur strukturierte Daten zurück, die Claude dann analysiert
        return {
            "status": "ready_for_analysis",
            "problem": problem_description,
            "timeframe_hours": timeframe_hours,
            "data_collected": {
                "event_logs": len(data.get("event_logs", [])),
                "services": len(data.get("services", [])),
                "recent_changes": len(data.get("recent_changes", [])),
                "metrics": data.get("metrics") if include_metrics else None
            },
            "analysis_prompt": analysis_prompt,
            "raw_data": data
        }

    async def _collect_diagnostic_data(self, timeframe_hours: int, include_metrics: bool) -> dict:
        """
        Sammelt Diagnose-Daten parallel

        Returns:
            Dict mit Event Logs, Services, Changes, Metrics
        """

        tasks = [
            self._collect_event_logs(timeframe_hours),
            self._collect_service_states(),
            self._collect_recent_changes(timeframe_hours)
        ]

        if include_metrics:
            tasks.append(self._collect_system_metrics())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "event_logs": results[0] if not isinstance(results[0], Exception) else [],
            "services": results[1] if not isinstance(results[1], Exception) else [],
            "recent_changes": results[2] if not isinstance(results[2], Exception) else [],
            "metrics": results[3] if len(results) > 3 and not isinstance(results[3], Exception) else None
        }

    async def _collect_event_logs(self, timeframe_hours: int) -> list:
        """Sammelt Event Logs (plattform-spezifisch)"""

        if self.os_type == "Windows":
            return await self._collect_windows_event_logs(timeframe_hours)
        elif self.os_type == "Darwin":  # macOS
            return await self._collect_macos_logs(timeframe_hours)
        elif self.os_type == "Linux":
            return await self._collect_linux_logs(timeframe_hours)
        else:
            return []

    async def _collect_windows_event_logs(self, timeframe_hours: int) -> list:
        """
        Windows Event Logs (Application, System, Security)
        """

        cutoff_time = datetime.now() - timedelta(hours=timeframe_hours)
        cutoff_str = cutoff_time.strftime("%Y-%m-%dT%H:%M:%S")

        # PowerShell Command für Event Logs
        cmd = f"""
        Get-EventLog -LogName Application,System -After "{cutoff_str}" -EntryType Error,Warning |
        Select-Object -First 100 TimeGenerated, Source, EventID, EntryType, Message |
        ConvertTo-Json -Compress
        """

        try:
            result = subprocess.run(
                ["powershell", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                logs = json.loads(result.stdout)
                return logs if isinstance(logs, list) else [logs]
            else:
                return []

        except Exception as e:
            print(f"⚠️  Event Log collection failed: {e}")
            return []

    async def _collect_macos_logs(self, timeframe_hours: int) -> list:
        """
        macOS System Logs (via log show)
        """

        cutoff_time = datetime.now() - timedelta(hours=timeframe_hours)
        cutoff_str = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")

        cmd = [
            "log", "show",
            "--predicate", "(eventType == 'logEvent' OR eventType == 'activityCreateEvent') AND processImagePath CONTAINS[c] 'system'",
            "--style", "json",
            "--start", cutoff_str,
            "--last", "100"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                # Parse JSON Lines Format
                logs = []
                for line in result.stdout.strip().split('\n'):
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                return logs[:100]  # Limit to 100

            return []

        except Exception as e:
            print(f"⚠️  Log collection failed: {e}")
            return []

    async def _collect_linux_logs(self, timeframe_hours: int) -> list:
        """
        Linux System Logs (via journalctl)
        """

        cmd = [
            "journalctl",
            "-p", "err",  # Priority: error
            "--since", f"{timeframe_hours} hours ago",
            "--lines", "100",
            "--output", "json"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                logs = []
                for line in result.stdout.strip().split('\n'):
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                return logs

            return []

        except Exception as e:
            print(f"⚠️  Log collection failed: {e}")
            return []

    async def _collect_service_states(self) -> list:
        """Sammelt Status aller Services"""

        if self.os_type == "Windows":
            return await self._collect_windows_services()
        elif self.os_type == "Darwin":
            return await self._collect_macos_services()
        elif self.os_type == "Linux":
            return await self._collect_linux_services()
        else:
            return []

    async def _collect_windows_services(self) -> list:
        """Windows Services via PowerShell"""

        cmd = """
        Get-Service | Where-Object {$_.Status -ne 'Running' -or $_.StartType -eq 'Automatic'} |
        Select-Object Name, DisplayName, Status, StartType |
        ConvertTo-Json -Compress
        """

        try:
            result = subprocess.run(
                ["powershell", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0 and result.stdout.strip():
                services = json.loads(result.stdout)
                return services if isinstance(services, list) else [services]

            return []

        except Exception:
            return []

    async def _collect_macos_services(self) -> list:
        """macOS LaunchDaemons/Agents"""

        cmd = ["launchctl", "list"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )

            services = []
            for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 3:
                    services.append({
                        "PID": parts[0],
                        "Status": parts[1],
                        "Label": parts[2]
                    })

            return services

        except Exception:
            return []

    async def _collect_linux_services(self) -> list:
        """Linux systemd Services"""

        cmd = ["systemctl", "list-units", "--type=service", "--state=failed", "--no-pager", "--output=json"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)

            return []

        except Exception:
            return []

    async def _collect_recent_changes(self, timeframe_hours: int) -> list:
        """Sammelt kürzliche System-Änderungen"""

        changes = []

        # Windows Updates (Windows only)
        if self.os_type == "Windows":
            cmd = """
            Get-HotFix | Where-Object {$_.InstalledOn -gt (Get-Date).AddHours(-{hours})} |
            Select-Object HotFixID, Description, InstalledOn |
            ConvertTo-Json -Compress
            """.format(hours=timeframe_hours)

            try:
                result = subprocess.run(
                    ["powershell", "-Command", cmd],
                    capture_output=True,
                    text=True,
                    timeout=15
                )

                if result.returncode == 0 and result.stdout.strip():
                    updates = json.loads(result.stdout)
                    changes.extend(updates if isinstance(updates, list) else [updates])

            except Exception:
                pass

        return changes

    async def _collect_system_metrics(self) -> dict:
        """Sammelt aktuelle System-Metriken"""

        try:
            import psutil

            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "processes": len(psutil.pids()),
                "uptime_hours": (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds() / 3600
            }

        except Exception:
            return {}

    def _build_analysis_prompt(self, problem: str, data: dict) -> str:
        """
        Baut Analyse-Prompt für Claude

        Returns:
            Detaillierter Prompt mit allen gesammelten Daten
        """

        lang = self.t.language

        if lang == "de":
            prompt = f"""
Du bist ein IT-Experte und analysierst ein Problem. Finde die ROOT CAUSE (nicht nur Symptome).

PROBLEM:
{problem}

GESAMMELTE DATEN:
"""
        else:  # en
            prompt = f"""
You are an IT expert analyzing a problem. Find the ROOT CAUSE (not just symptoms).

PROBLEM:
{problem}

COLLECTED DATA:
"""

        # Event Logs
        if data.get("event_logs"):
            prompt += f"\n\nEVENT LOGS (last {len(data['event_logs'])} errors/warnings):\n"
            for log in data["event_logs"][:20]:  # Top 20
                prompt += f"- {log}\n"

        # Services
        if data.get("services"):
            prompt += f"\n\nSERVICE STATUS:\n"
            for service in data["services"][:30]:  # Top 30
                prompt += f"- {service}\n"

        # Recent Changes
        if data.get("recent_changes"):
            prompt += f"\n\nRECENT CHANGES:\n"
            for change in data["recent_changes"]:
                prompt += f"- {change}\n"

        # Metrics
        if data.get("metrics"):
            prompt += f"\n\nSYSTEM METRICS:\n{json.dumps(data['metrics'], indent=2)}\n"

        if lang == "de":
            prompt += """

AUFGABE:
1. Identifiziere die ROOT CAUSE (nicht nur Symptome)
2. Zeige BEWEISE (Event-IDs, Timestamps, Korrelationen)
3. Gib CONFIDENCE SCORE (0-100%)
4. Schlage KONKRETE Lösung vor
5. Format: Strukturierte Ausgabe

FORMAT:
╔══════════════════════════════════════════════╗
║  🎯 ROOT CAUSE GEFUNDEN                      ║
╠══════════════════════════════════════════════╣
║  Ursache: [Kurze Beschreibung]              ║
║  Confidence: [XX%]                           ║
║                                              ║
║  Beweise:                                    ║
║  ✓ [Beweis 1]                               ║
║  ✓ [Beweis 2]                               ║
║                                              ║
║  Lösung:                                     ║
║  1. [Schritt 1]                             ║
║  2. [Schritt 2]                             ║
╚══════════════════════════════════════════════╝
"""
        else:  # en
            prompt += """

TASK:
1. Identify the ROOT CAUSE (not just symptoms)
2. Show EVIDENCE (Event IDs, Timestamps, Correlations)
3. Give CONFIDENCE SCORE (0-100%)
4. Suggest CONCRETE solution
5. Format: Structured output

FORMAT:
╔══════════════════════════════════════════════╗
║  🎯 ROOT CAUSE FOUND                         ║
╠══════════════════════════════════════════════╣
║  Cause: [Brief description]                 ║
║  Confidence: [XX%]                           ║
║                                              ║
║  Evidence:                                   ║
║  ✓ [Evidence 1]                             ║
║  ✓ [Evidence 2]                             ║
║                                              ║
║  Solution:                                   ║
║  1. [Step 1]                                ║
║  2. [Step 2]                                ║
╚══════════════════════════════════════════════╝
"""

        return prompt
