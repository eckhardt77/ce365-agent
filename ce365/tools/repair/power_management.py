"""
CE365 Agent - Power Management

Neustart / Herunterfahren / Abmelden
Plattformuebergreifend: Windows + macOS
"""

import platform
from typing import Dict, Any
from ce365.tools.base import RepairTool
from ce365.core.command_runner import get_command_runner


class RebootTool(RepairTool):
    """System neustarten oder herunterfahren"""

    @property
    def name(self) -> str:
        return "reboot_shutdown"

    @property
    def description(self) -> str:
        return (
            "Startet das System neu, faehrt es herunter oder meldet den User ab. "
            "Optionaler Countdown (Sekunden) gibt dem User Zeit zum Speichern. "
            "ACHTUNG: Nicht gespeicherte Arbeit geht verloren! "
            "Immer vorher den Techniker warnen. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["reboot", "shutdown", "logout"],
                    "description": "Aktion: reboot (Neustart), shutdown (Herunterfahren), logout (Abmelden)",
                },
                "delay_seconds": {
                    "type": "integer",
                    "description": "Verzoegerung in Sekunden (Standard: 60). Gibt dem User Zeit zum Speichern.",
                    "default": 60,
                },
                "reason": {
                    "type": "string",
                    "description": "Grund fuer den Neustart/Shutdown (wird geloggt)",
                    "default": "CE365 Agent - Geplanter Neustart",
                },
                "force": {
                    "type": "boolean",
                    "description": "Erzwingt sofortigen Neustart/Shutdown ohne auf Apps zu warten",
                    "default": False,
                },
            },
            "required": ["action"],
        }

    async def execute(self, **kwargs) -> str:
        action = kwargs.get("action", "reboot")
        delay = kwargs.get("delay_seconds", 60)
        reason = kwargs.get("reason", "CE365 Agent - Geplanter Neustart")
        force = kwargs.get("force", False)

        if delay < 0:
            delay = 0
        if delay > 3600:
            delay = 3600  # Max 1 Stunde

        # Reason sanitizen
        reason = reason.replace('"', '').replace("'", "").replace(";", "")[:200]

        os_type = platform.system()

        if os_type == "Windows":
            return await self._execute_windows(action, delay, reason, force)
        elif os_type == "Darwin":
            return await self._execute_macos(action, delay, force)
        else:
            return f"Power Management fuer {os_type} nicht unterstuetzt"

    async def _execute_windows(self, action: str, delay: int, reason: str, force: bool) -> str:
        runner = get_command_runner()

        if action == "logout":
            cmd = ["shutdown", "/l"]
            if force:
                cmd.append("/f")
            result = await runner.run(cmd, timeout=10)
            if result.success:
                return "Benutzer wird abgemeldet..."
            return f"Fehler beim Abmelden: {result.stderr}"

        if action == "reboot":
            cmd = ["shutdown", "/r", "/t", str(delay), "/c", reason]
        else:  # shutdown
            cmd = ["shutdown", "/s", "/t", str(delay), "/c", reason]

        if force:
            cmd.append("/f")

        result = await runner.run(cmd, timeout=10)
        if result.success:
            action_label = "Neustart" if action == "reboot" else "Herunterfahren"
            if delay > 0:
                return (
                    f"{action_label} in {delay} Sekunden geplant.\n"
                    f"Grund: {reason}\n"
                    f"Abbrechen mit: shutdown /a"
                )
            return f"{action_label} wird ausgefuehrt..."
        return f"Fehler: {result.stderr}"

    async def _execute_macos(self, action: str, delay: int, force: bool) -> str:
        runner = get_command_runner()

        if action == "logout":
            cmd = ["osascript", "-e", 'tell application "System Events" to log out']
            result = await runner.run(cmd, timeout=10)
            if result.success:
                return "Benutzer wird abgemeldet..."
            return f"Fehler beim Abmelden: {result.stderr}"

        # macOS shutdown/reboot braucht sudo
        delay_minutes = max(1, delay // 60) if delay > 0 else 0

        if action == "reboot":
            if delay_minutes > 0:
                cmd = ["sudo", "shutdown", "-r", f"+{delay_minutes}"]
            else:
                cmd = ["sudo", "shutdown", "-r", "now"]
        else:  # shutdown
            if delay_minutes > 0:
                cmd = ["sudo", "shutdown", "-h", f"+{delay_minutes}"]
            else:
                cmd = ["sudo", "shutdown", "-h", "now"]

        result = await runner.run(cmd, timeout=10)
        if result.success:
            action_label = "Neustart" if action == "reboot" else "Herunterfahren"
            if delay_minutes > 0:
                return (
                    f"{action_label} in {delay_minutes} Minute(n) geplant.\n"
                    f"Abbrechen mit: sudo killall shutdown"
                )
            return f"{action_label} wird ausgefuehrt..."
        return f"Fehler: {result.stderr}"


class CancelShutdownTool(RepairTool):
    """Geplanten Neustart/Shutdown abbrechen"""

    @property
    def name(self) -> str:
        return "cancel_shutdown"

    @property
    def description(self) -> str:
        return (
            "Bricht einen geplanten Neustart oder Shutdown ab. "
            "Nur noetig wenn ein Countdown laeuft."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        runner = get_command_runner()
        os_type = platform.system()

        if os_type == "Windows":
            result = await runner.run(["shutdown", "/a"], timeout=10)
        elif os_type == "Darwin":
            result = await runner.run(["sudo", "killall", "shutdown"], timeout=10)
        else:
            return f"Nicht unterstuetzt auf {os_type}"

        if result.success:
            return "Geplanter Neustart/Shutdown wurde abgebrochen."
        return f"Kein geplanter Shutdown aktiv oder Fehler: {result.stderr}"
