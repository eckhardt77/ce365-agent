"""
CE365 Agent - System Sensor / Monitoring Module

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Background-Service der System-Metriken sammelt und an Backend sendet:
- CPU/RAM/Disk Usage
- Kritische Service-Status
- Pending Updates
- Event Log Errors
- SMART Disk Health
"""

import asyncio
import platform
import psutil
import httpx
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class SystemSensor:
    """
    System Monitoring Sensor

    Sammelt Metriken und sendet sie periodisch an Backend
    """

    def __init__(
        self,
        backend_url: str,
        api_key: str,
        interval: int = 300,  # 5 Minuten
        hostname: Optional[str] = None
    ):
        """
        Args:
            backend_url: URL zum Backend
            api_key: API Key für Authentifizierung
            interval: Interval in Sekunden (Standard: 5 Min)
            hostname: Hostname (optional, wird automatisch erkannt)
        """
        self.backend_url = backend_url.rstrip("/")
        self.api_key = api_key
        self.interval = interval
        self.hostname = hostname or platform.node()
        self.os_type = platform.system().lower()

        # Critical Services (OS-spezifisch)
        self.critical_services = self._get_critical_services()

    def _get_critical_services(self) -> List[str]:
        """Gibt kritische Services zurück (OS-abhängig)"""
        if self.os_type == "windows":
            return [
                "wuauserv",  # Windows Update
                "mpssvc",    # Windows Firewall
                "Windefend", # Windows Defender
                "Spooler",   # Print Spooler
                "Dnscache",  # DNS Client
            ]
        elif self.os_type == "darwin":  # macOS
            return [
                "com.apple.softwareupdate",
                "com.apple.Firewall",
                "com.apple.ManagedClient",
            ]
        else:  # Linux
            return [
                "ssh",
                "ufw",
                "systemd-resolved",
            ]

    async def collect_metrics(self) -> Dict:
        """
        Sammelt aktuelle System-Metriken

        Returns:
            {
                "timestamp": "2026-02-17T10:30:00",
                "hostname": "DESKTOP-123",
                "os": "windows",
                "cpu_percent": 45.2,
                "ram_percent": 62.1,
                "disk_percent": 78.3,
                "critical_services": {...},
                "pending_updates": 5,
                "recent_errors": [...],
                "disk_health": "healthy" | "warning" | "critical"
            }
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "hostname": self.hostname,
            "os": self.os_type,
            "cpu_percent": psutil.cpu_percent(interval=1),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "critical_services": await self._check_services(),
            "pending_updates": await self._check_updates(),
            "recent_errors": await self._get_event_log_errors(),
            "disk_health": await self._check_smart_status(),
        }

        return metrics

    async def _check_services(self) -> Dict[str, str]:
        """
        Prüft Status kritischer Services

        Returns:
            {"service_name": "running" | "stopped" | "unknown"}
        """
        services_status = {}

        if self.os_type == "windows":
            # Windows Services via sc.exe prüfen
            import subprocess
            for service in self.critical_services:
                try:
                    result = subprocess.run(
                        ["sc", "query", service],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if "RUNNING" in result.stdout:
                        services_status[service] = "running"
                    elif "STOPPED" in result.stdout:
                        services_status[service] = "stopped"
                    else:
                        services_status[service] = "unknown"

                except Exception:
                    services_status[service] = "unknown"

        elif self.os_type == "darwin":  # macOS
            # macOS Services via launchctl
            import subprocess
            for service in self.critical_services:
                try:
                    result = subprocess.run(
                        ["launchctl", "list", service],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0:
                        services_status[service] = "running"
                    else:
                        services_status[service] = "stopped"

                except Exception:
                    services_status[service] = "unknown"

        else:  # Linux
            # systemctl status
            import subprocess
            for service in self.critical_services:
                try:
                    result = subprocess.run(
                        ["systemctl", "is-active", service],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    services_status[service] = result.stdout.strip()

                except Exception:
                    services_status[service] = "unknown"

        return services_status

    async def _check_updates(self) -> int:
        """
        Prüft Anzahl ausstehender Updates

        Returns:
            Anzahl Updates
        """
        try:
            if self.os_type == "windows":
                # Windows Update API via PowerShell
                import subprocess
                result = subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "(New-Object -ComObject Microsoft.Update.Searcher).Search('IsInstalled=0').Updates.Count"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                return int(result.stdout.strip() or 0)

            elif self.os_type == "darwin":  # macOS
                # softwareupdate -l
                import subprocess
                result = subprocess.run(
                    ["softwareupdate", "-l"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Count lines with "*" (pending updates)
                return result.stdout.count("*")

            else:  # Linux (apt-based)
                import subprocess
                result = subprocess.run(
                    ["apt", "list", "--upgradable"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Count lines (minus header)
                return max(0, len(result.stdout.split("\n")) - 2)

        except Exception:
            return 0

    async def _get_event_log_errors(self) -> List[str]:
        """
        Holt letzte Fehler aus Event Log (Windows) / System Log (macOS/Linux)

        Returns:
            Liste der letzten 5 Fehler
        """
        errors = []

        try:
            if self.os_type == "windows":
                # Windows Event Log via PowerShell
                import subprocess
                result = subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "Get-EventLog -LogName System -EntryType Error -Newest 5 | Select-Object -Property TimeGenerated, Source, Message | ConvertTo-Json"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                import json
                events = json.loads(result.stdout)
                if isinstance(events, dict):
                    events = [events]

                for event in events:
                    errors.append(
                        f"{event['TimeGenerated']}: {event['Source']} - {event['Message'][:100]}"
                    )

            elif self.os_type == "darwin":  # macOS
                # macOS Unified Log
                import subprocess
                result = subprocess.run(
                    ["log", "show", "--predicate", "messageType == 'Error'", "--last", "1h"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                lines = result.stdout.split("\n")[:5]
                errors = [line[:200] for line in lines if line.strip()]

            else:  # Linux
                # journalctl
                import subprocess
                result = subprocess.run(
                    ["journalctl", "-p", "err", "-n", "5", "--no-pager"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                errors = [line[:200] for line in result.stdout.split("\n") if line.strip()]

        except Exception:
            pass

        return errors

    async def _check_smart_status(self) -> str:
        """
        Prüft SMART-Status der Festplatten

        Returns:
            "healthy" | "warning" | "critical" | "unknown"
        """
        try:
            if self.os_type == "windows":
                # Windows: wmic via PowerShell
                import subprocess
                result = subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "Get-WmiObject -Namespace root\\wmi -Class MSStorageDriver_FailurePredictStatus | Select-Object PredictFailure"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if "True" in result.stdout:
                    return "critical"
                else:
                    return "healthy"

            elif self.os_type == "darwin":  # macOS
                # macOS: diskutil
                import subprocess
                result = subprocess.run(
                    ["diskutil", "info", "disk0"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if "S.M.A.R.T. Status: Verified" in result.stdout:
                    return "healthy"
                elif "S.M.A.R.T. Status: Failing" in result.stdout:
                    return "critical"
                else:
                    return "unknown"

            else:  # Linux
                # smartctl
                import subprocess
                result = subprocess.run(
                    ["smartctl", "-H", "/dev/sda"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if "PASSED" in result.stdout:
                    return "healthy"
                elif "FAILED" in result.stdout:
                    return "critical"
                else:
                    return "unknown"

        except Exception:
            return "unknown"

    async def send_metrics(self, metrics: Dict) -> bool:
        """
        Sendet Metriken an Backend

        Args:
            metrics: Metriken-Dict

        Returns:
            True wenn erfolgreich
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.backend_url}/api/monitoring/metrics",
                    json=metrics,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )

                return response.status_code == 200

        except Exception as e:
            print(f"❌ Fehler beim Senden der Metriken: {str(e)}")
            return False

    async def run(self):
        """
        Main Loop: Sammelt und sendet Metriken periodisch

        Läuft endlos bis KeyboardInterrupt
        """
        print(f"🔍 CE365 Sensor gestartet (Interval: {self.interval}s)")
        print(f"📡 Backend: {self.backend_url}")
        print(f"💻 Hostname: {self.hostname}")
        print()

        while True:
            try:
                # Metriken sammeln
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Sammle Metriken...")
                metrics = await self.collect_metrics()

                # An Backend senden
                success = await self.send_metrics(metrics)

                if success:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Metriken gesendet")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Fehler beim Senden")

                # Warten bis nächster Interval
                await asyncio.sleep(self.interval)

            except KeyboardInterrupt:
                print("\n\n👋 Sensor beendet")
                break
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Fehler: {str(e)}")
                await asyncio.sleep(self.interval)


# CLI Entry Point für Sensor-Mode
async def main():
    """Main Entry für Sensor-Mode"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    backend_url = os.getenv("BACKEND_URL")
    api_key = os.getenv("ANTHROPIC_API_KEY")  # Oder separater SENSOR_API_KEY

    if not backend_url:
        print("❌ BACKEND_URL nicht gesetzt in .env")
        return

    if not api_key:
        print("❌ API_KEY nicht gesetzt in .env")
        return

    # Interval aus Env (Standard: 5 Min)
    interval = int(os.getenv("SENSOR_INTERVAL", "300"))

    # Sensor starten
    sensor = SystemSensor(
        backend_url=backend_url,
        api_key=api_key,
        interval=interval
    )

    await sensor.run()


if __name__ == "__main__":
    asyncio.run(main())
