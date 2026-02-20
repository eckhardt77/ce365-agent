"""
CE365 Agent - Software Manager

Software installieren, deinstallieren und aktualisieren.
Windows: winget / choco
macOS: brew
"""

import platform
from typing import Dict, Any
from ce365.tools.base import RepairTool
from ce365.core.command_runner import get_command_runner


class InstallSoftwareTool(RepairTool):
    """Software installieren"""

    @property
    def name(self) -> str:
        return "install_software"

    @property
    def description(self) -> str:
        return (
            "Installiert Software-Pakete. "
            "Windows: winget (bevorzugt) oder chocolatey. "
            "macOS: Homebrew (brew). "
            "ACHTUNG: Installiert Software auf dem System! "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "package_name": {
                    "type": "string",
                    "description": "Paketname (z.B. 'Google Chrome', 'firefox', '7zip', 'vlc')",
                },
                "manager": {
                    "type": "string",
                    "enum": ["auto", "winget", "choco", "brew"],
                    "description": "Paketmanager: auto (erkennt automatisch), winget, choco, brew",
                    "default": "auto",
                },
            },
            "required": ["package_name"],
        }

    async def execute(self, **kwargs) -> str:
        package = kwargs.get("package_name", "").strip()
        manager = kwargs.get("manager", "auto")

        if not package:
            return "Bitte Paketnamen angeben"

        # Paketname sanitizen
        if any(c in package for c in [";", "|", "&", "`", "$", "\n"]):
            return "Ungueltiger Paketname (enthaelt Sonderzeichen)"

        os_type = platform.system()
        runner = get_command_runner()

        if os_type == "Windows":
            return await self._install_windows(runner, package, manager)
        elif os_type == "Darwin":
            return await self._install_macos(runner, package, manager)
        else:
            return f"Software-Installation fuer {os_type} nicht unterstuetzt"

    async def _install_windows(self, runner, package: str, manager: str) -> str:
        # Auto-Detect: winget bevorzugt, Fallback auf choco
        if manager == "auto":
            check = await runner.run(["winget", "--version"], timeout=10)
            if check.success:
                manager = "winget"
            else:
                check = await runner.run(["choco", "--version"], timeout=10)
                if check.success:
                    manager = "choco"
                else:
                    return (
                        "Kein Paketmanager gefunden.\n"
                        "Bitte winget (ab Windows 10 1709) oder "
                        "Chocolatey installieren."
                    )

        if manager == "winget":
            result = await runner.run(
                ["winget", "install", "--id", package, "--accept-source-agreements",
                 "--accept-package-agreements", "--silent"],
                timeout=300,  # 5 Minuten fuer grosse Pakete
            )
        elif manager == "choco":
            result = await runner.run(
                ["choco", "install", package, "-y", "--no-progress"],
                timeout=300,
            )
        else:
            return f"Paketmanager '{manager}' nicht verfuegbar auf Windows"

        if result.success:
            return f"'{package}' wurde erfolgreich installiert.\n\n{result.stdout[:500]}"
        return f"Installation fehlgeschlagen:\n{result.output[:500]}"

    async def _install_macos(self, runner, package: str, manager: str) -> str:
        if manager not in ("auto", "brew"):
            return f"Paketmanager '{manager}' nicht verfuegbar auf macOS. Nutze 'brew'."

        # Pruefen ob brew installiert ist
        check = await runner.run(["brew", "--version"], timeout=10)
        if not check.success:
            return (
                "Homebrew ist nicht installiert.\n"
                "Installation: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            )

        result = await runner.run(
            ["brew", "install", package],
            timeout=300,
        )
        if result.success:
            return f"'{package}' wurde erfolgreich installiert.\n\n{result.stdout[:500]}"

        # Fallback: brew cask fuer GUI-Apps
        result_cask = await runner.run(
            ["brew", "install", "--cask", package],
            timeout=300,
        )
        if result_cask.success:
            return f"'{package}' (GUI-App) wurde erfolgreich installiert.\n\n{result_cask.stdout[:500]}"

        return f"Installation fehlgeschlagen:\n{result.output[:500]}\n\nAuch als Cask versucht:\n{result_cask.output[:500]}"


class UninstallSoftwareTool(RepairTool):
    """Software deinstallieren"""

    @property
    def name(self) -> str:
        return "uninstall_software"

    @property
    def description(self) -> str:
        return (
            "Deinstalliert Software-Pakete. "
            "Windows: winget oder chocolatey. macOS: brew. "
            "ACHTUNG: Entfernt Software vom System! "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "package_name": {
                    "type": "string",
                    "description": "Paketname oder App-Name zum Deinstallieren",
                },
                "manager": {
                    "type": "string",
                    "enum": ["auto", "winget", "choco", "brew"],
                    "description": "Paketmanager (auto erkennt automatisch)",
                    "default": "auto",
                },
            },
            "required": ["package_name"],
        }

    async def execute(self, **kwargs) -> str:
        package = kwargs.get("package_name", "").strip()
        manager = kwargs.get("manager", "auto")

        if not package:
            return "Bitte Paketnamen angeben"

        if any(c in package for c in [";", "|", "&", "`", "$", "\n"]):
            return "Ungueltiger Paketname (enthaelt Sonderzeichen)"

        os_type = platform.system()
        runner = get_command_runner()

        if os_type == "Windows":
            return await self._uninstall_windows(runner, package, manager)
        elif os_type == "Darwin":
            return await self._uninstall_macos(runner, package, manager)
        else:
            return f"Software-Deinstallation fuer {os_type} nicht unterstuetzt"

    async def _uninstall_windows(self, runner, package: str, manager: str) -> str:
        if manager == "auto":
            check = await runner.run(["winget", "--version"], timeout=10)
            if check.success:
                manager = "winget"
            else:
                check = await runner.run(["choco", "--version"], timeout=10)
                if check.success:
                    manager = "choco"
                else:
                    return "Kein Paketmanager gefunden (winget oder choco benoetigt)"

        if manager == "winget":
            result = await runner.run(
                ["winget", "uninstall", "--id", package, "--silent"],
                timeout=120,
            )
        elif manager == "choco":
            result = await runner.run(
                ["choco", "uninstall", package, "-y"],
                timeout=120,
            )
        else:
            return f"Paketmanager '{manager}' nicht verfuegbar"

        if result.success:
            return f"'{package}' wurde erfolgreich deinstalliert.\n\n{result.stdout[:500]}"
        return f"Deinstallation fehlgeschlagen:\n{result.output[:500]}"

    async def _uninstall_macos(self, runner, package: str, manager: str) -> str:
        if manager not in ("auto", "brew"):
            return f"Paketmanager '{manager}' nicht verfuegbar auf macOS"

        # Erst als normales Paket, dann als Cask
        result = await runner.run(["brew", "uninstall", package], timeout=60)
        if result.success:
            return f"'{package}' wurde erfolgreich deinstalliert.\n\n{result.stdout[:500]}"

        result_cask = await runner.run(
            ["brew", "uninstall", "--cask", package], timeout=60,
        )
        if result_cask.success:
            return f"'{package}' (GUI-App) wurde erfolgreich deinstalliert.\n\n{result_cask.stdout[:500]}"

        return f"Deinstallation fehlgeschlagen:\n{result.output[:300]}\n\nAuch als Cask versucht:\n{result_cask.output[:300]}"


class UpdateSoftwareTool(RepairTool):
    """Einzelne Software oder alle Pakete aktualisieren"""

    @property
    def name(self) -> str:
        return "update_software"

    @property
    def description(self) -> str:
        return (
            "Aktualisiert Software-Pakete. "
            "Kann ein einzelnes Paket oder alle installierten Pakete aktualisieren. "
            "Windows: winget / choco. macOS: brew. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "package_name": {
                    "type": "string",
                    "description": "Paketname zum Aktualisieren. Leer lassen fuer 'alle aktualisieren'.",
                    "default": "",
                },
                "manager": {
                    "type": "string",
                    "enum": ["auto", "winget", "choco", "brew"],
                    "description": "Paketmanager (auto erkennt automatisch)",
                    "default": "auto",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        package = kwargs.get("package_name", "").strip()
        manager = kwargs.get("manager", "auto")

        if package and any(c in package for c in [";", "|", "&", "`", "$", "\n"]):
            return "Ungueltiger Paketname"

        os_type = platform.system()
        runner = get_command_runner()

        if os_type == "Windows":
            return await self._update_windows(runner, package, manager)
        elif os_type == "Darwin":
            return await self._update_macos(runner, package)
        else:
            return f"Software-Update fuer {os_type} nicht unterstuetzt"

    async def _update_windows(self, runner, package: str, manager: str) -> str:
        if manager == "auto":
            check = await runner.run(["winget", "--version"], timeout=10)
            manager = "winget" if check.success else "choco"

        if manager == "winget":
            if package:
                cmd = ["winget", "upgrade", "--id", package, "--accept-source-agreements", "--silent"]
            else:
                cmd = ["winget", "upgrade", "--all", "--accept-source-agreements", "--silent"]
        elif manager == "choco":
            if package:
                cmd = ["choco", "upgrade", package, "-y", "--no-progress"]
            else:
                cmd = ["choco", "upgrade", "all", "-y", "--no-progress"]
        else:
            return f"Paketmanager '{manager}' nicht verfuegbar"

        result = await runner.run(cmd, timeout=600)  # 10 Min fuer Upgrade all
        if result.success:
            label = f"'{package}'" if package else "Alle Pakete"
            return f"{label} erfolgreich aktualisiert.\n\n{result.stdout[:800]}"
        return f"Update fehlgeschlagen:\n{result.output[:500]}"

    async def _update_macos(self, runner, package: str) -> str:
        if package:
            result = await runner.run(["brew", "upgrade", package], timeout=300)
        else:
            # brew update (Index) + brew upgrade (Pakete)
            await runner.run(["brew", "update"], timeout=120)
            result = await runner.run(["brew", "upgrade"], timeout=600)

        if result.success:
            label = f"'{package}'" if package else "Alle Pakete"
            return f"{label} erfolgreich aktualisiert.\n\n{result.stdout[:800]}"
        return f"Update fehlgeschlagen:\n{result.output[:500]}"
