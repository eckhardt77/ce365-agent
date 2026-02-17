"""
TechCare Bot - Driver Manager

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Prüft Treiber-Status und empfiehlt Updates aus mehreren Quellen:
- Windows Update API (Windows)
- Apple Software Update (macOS)
- Custom Driver Database (JSON-basiert)
"""

import platform
import subprocess
import json
from techcare.tools.sanitize import sanitize_powershell_string, validate_program_name
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class DriverManager:
    """
    Driver Management System

    Features:
    - Treiber-Erkennung via OS-APIs
    - Update-Prüfung via Windows Update / macOS SoftwareUpdate
    - Empfehlungen für Driver-Updates
    """

    def __init__(self):
        self.os_type = platform.system().lower()
        self.driver_db_path = Path(__file__).parent / "driver_database.json"

    async def check_all_drivers(self) -> Dict:
        """
        Prüft alle installierten Treiber

        Returns:
            {
                "total_drivers": 150,
                "outdated_drivers": [
                    {
                        "name": "NVIDIA GeForce RTX 3080",
                        "current_version": "512.95",
                        "available_version": "528.49",
                        "severity": "recommended",  # "critical" | "recommended" | "optional"
                        "source": "windows_update",  # "windows_update" | "vendor" | "custom_db"
                        "install_command": "pnputil /add-driver driver.inf /install"
                    }
                ],
                "critical_count": 2,
                "recommended_count": 5
            }
        """
        if self.os_type == "windows":
            return await self._check_windows_drivers()
        elif self.os_type == "darwin":
            return await self._check_macos_drivers()
        else:
            return {
                "error": f"Driver-Prüfung nicht unterstützt für {self.os_type}"
            }

    async def _check_windows_drivers(self) -> Dict:
        """Windows Driver Check via DISM und Windows Update"""
        outdated_drivers = []

        try:
            # 1. Alle installierten Treiber via DISM
            result = subprocess.run(
                [
                    "dism",
                    "/online",
                    "/get-drivers",
                    "/format:table"
                ],
                capture_output=True,
                text=True,
                timeout=60
            )

            # Parse DISM Output
            lines = result.stdout.split("\n")
            driver_count = 0
            for line in lines:
                if "Published Name" in line:
                    driver_count += 1

            # 2. Prüfe Windows Update für Treiber-Updates
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    """
                    $UpdateSession = New-Object -ComObject Microsoft.Update.Session
                    $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
                    $SearchResult = $UpdateSearcher.Search("IsInstalled=0 and Type='Driver'")
                    $SearchResult.Updates | Select-Object Title,
                        @{Name='DriverClass';Expression={$_.DriverClass}},
                        @{Name='DriverVerDate';Expression={$_.DriverVerDate}},
                        @{Name='IsMandatory';Expression={$_.IsMandatory}} | ConvertTo-Json
                    """
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.stdout.strip():
                try:
                    updates = json.loads(result.stdout)

                    # Single object zu Liste konvertieren
                    if isinstance(updates, dict):
                        updates = [updates]

                    for update in updates:
                        severity = "critical" if update.get("IsMandatory") else "recommended"

                        outdated_drivers.append({
                            "name": update.get("Title", "Unknown Driver"),
                            "current_version": "Unknown",
                            "available_version": update.get("DriverVerDate", "Unknown"),
                            "severity": severity,
                            "source": "windows_update",
                            "install_command": "Install via Windows Update"
                        })
                except json.JSONDecodeError:
                    pass

            # 3. Custom Database Check (optional)
            db_drivers = self._load_driver_database()
            # TODO: Hardware-ID Detection + Matching gegen DB

            critical = sum(1 for d in outdated_drivers if d["severity"] == "critical")
            recommended = sum(1 for d in outdated_drivers if d["severity"] == "recommended")

            return {
                "total_drivers": driver_count,
                "outdated_drivers": outdated_drivers,
                "critical_count": critical,
                "recommended_count": recommended
            }

        except Exception as e:
            return {
                "error": f"Fehler bei Driver-Check: {str(e)}"
            }

    async def _check_macos_drivers(self) -> Dict:
        """macOS Driver Check via softwareupdate"""
        outdated_drivers = []

        try:
            # macOS Software Update für Treiber-Updates
            result = subprocess.run(
                ["softwareupdate", "-l"],
                capture_output=True,
                text=True,
                timeout=60
            )

            # Parse Output für Driver-Updates
            lines = result.stdout.split("\n")
            for line in lines:
                if "Driver" in line or "Firmware" in line:
                    # Extrahiere Update-Info
                    parts = line.strip().split("*")
                    if len(parts) > 1:
                        name = parts[1].strip()

                        outdated_drivers.append({
                            "name": name,
                            "current_version": "Unknown",
                            "available_version": "Latest",
                            "severity": "recommended",
                            "source": "apple_software_update",
                            "install_command": f"sudo softwareupdate -i '{name}'"
                        })

            return {
                "total_drivers": 0,  # macOS zeigt keine Gesamtanzahl
                "outdated_drivers": outdated_drivers,
                "critical_count": 0,
                "recommended_count": len(outdated_drivers)
            }

        except Exception as e:
            return {
                "error": f"Fehler bei Driver-Check: {str(e)}"
            }

    def _load_driver_database(self) -> List[Dict]:
        """
        Lädt Custom Driver Database

        Format:
        [
            {
                "hardware_id": "PCI\\VEN_10DE&DEV_2206",
                "name": "NVIDIA GeForce RTX 3080",
                "vendor": "NVIDIA",
                "latest_version": "528.49",
                "release_date": "2023-02-14",
                "download_url": "https://..."
            }
        ]
        """
        if not self.driver_db_path.exists():
            return []

        try:
            with open(self.driver_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    async def install_driver_update(self, driver_name: str, source: str) -> Dict:
        """
        Installiert Driver-Update

        Args:
            driver_name: Driver Name
            source: "windows_update" | "apple_software_update" | "custom"

        Returns:
            {"success": bool, "message": str}
        """
        try:
            if source == "windows_update":
                # Windows Update Installation via PowerShell
                result = subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        f"""
                        $UpdateSession = New-Object -ComObject Microsoft.Update.Session
                        $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
                        $SearchResult = $UpdateSearcher.Search("IsInstalled=0 and Type='Driver' and Title like '*{sanitize_powershell_string(validate_program_name(driver_name))}*'")

                        if ($SearchResult.Updates.Count -eq 0) {{
                            Write-Host "Kein Update gefunden"
                            exit 1
                        }}

                        $UpdatesToInstall = New-Object -ComObject Microsoft.Update.UpdateColl
                        $SearchResult.Updates | ForEach-Object {{ $UpdatesToInstall.Add($_) }}

                        $Installer = $UpdateSession.CreateUpdateInstaller()
                        $Installer.Updates = $UpdatesToInstall
                        $InstallResult = $Installer.Install()

                        Write-Host "Installation abgeschlossen"
                        """
                    ],
                    capture_output=True,
                    text=True,
                    timeout=600
                )

                if result.returncode == 0:
                    return {
                        "success": True,
                        "message": f"Treiber '{driver_name}' erfolgreich installiert"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Fehler bei Installation: {result.stderr}"
                    }

            elif source == "apple_software_update":
                # macOS softwareupdate Installation
                result = subprocess.run(
                    ["sudo", "softwareupdate", "-i", driver_name],
                    capture_output=True,
                    text=True,
                    timeout=600
                )

                if result.returncode == 0:
                    return {
                        "success": True,
                        "message": f"Update '{driver_name}' erfolgreich installiert"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Fehler bei Installation: {result.stderr}"
                    }

            else:
                return {
                    "success": False,
                    "message": f"Installation-Quelle '{source}' nicht unterstützt"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler: {str(e)}"
            }


# Convenience Function
async def check_drivers() -> Dict:
    """Helper-Funktion für Driver-Check"""
    manager = DriverManager()
    return await manager.check_all_drivers()
