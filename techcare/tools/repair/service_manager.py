import platform
import subprocess
from techcare.tools.base import RepairTool


class ServiceManagerTool(RepairTool):
    """
    Service Management (Windows/macOS)

    Windows: sc.exe (sc start/stop/query)
    macOS: launchctl (start/stop/kickstart)
    """

    @property
    def name(self) -> str:
        return "manage_service"

    @property
    def description(self) -> str:
        return (
            "Verwaltet System-Services (Start, Stop, Restart, Status). "
            "Windows: sc.exe, macOS: launchctl. "
            "⚠️ REPAIR-TOOL - Benötigt GO REPAIR Freigabe!"
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name des Services (z.B. 'wuauserv' für Windows Update)",
                },
                "action": {
                    "type": "string",
                    "enum": ["start", "stop", "restart", "status"],
                    "description": "Aktion: start, stop, restart, status",
                },
            },
            "required": ["service_name", "action"],
        }

    async def execute(self, service_name: str, action: str) -> str:
        """Service Management ausführen"""
        os_type = platform.system()

        if os_type == "Windows":
            return await self._manage_windows_service(service_name, action)
        elif os_type == "Darwin":  # macOS
            return await self._manage_macos_service(service_name, action)
        else:
            return f"❌ Service Management für {os_type} noch nicht implementiert"

    async def _manage_windows_service(self, service_name: str, action: str) -> str:
        """Windows Service Management via sc.exe"""
        try:
            if action == "status":
                result = subprocess.run(
                    ["sc", "query", service_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    return f"✓ Service Status:\n{result.stdout}"
                else:
                    return f"❌ Service nicht gefunden: {result.stderr}"

            elif action == "start":
                result = subprocess.run(
                    ["sc", "start", service_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return f"✓ Service '{service_name}' erfolgreich gestartet"
                else:
                    return f"❌ Fehler beim Starten: {result.stderr}"

            elif action == "stop":
                result = subprocess.run(
                    ["sc", "stop", service_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return f"✓ Service '{service_name}' erfolgreich gestoppt"
                else:
                    return f"❌ Fehler beim Stoppen: {result.stderr}"

            elif action == "restart":
                # Stop
                subprocess.run(
                    ["sc", "stop", service_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                # Wait
                import time
                time.sleep(2)
                # Start
                result = subprocess.run(
                    ["sc", "start", service_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return f"✓ Service '{service_name}' erfolgreich neugestartet"
                else:
                    return f"❌ Fehler beim Neustarten: {result.stderr}"

        except subprocess.TimeoutExpired:
            return f"❌ Timeout bei Service-Operation (>30s)"
        except Exception as e:
            return f"❌ Fehler: {str(e)}"

    async def _manage_macos_service(self, service_name: str, action: str) -> str:
        """macOS Service Management via launchctl"""
        try:
            if action == "status":
                result = subprocess.run(
                    ["launchctl", "list", service_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    return f"✓ Service Status:\n{result.stdout}"
                else:
                    return f"❌ Service nicht gefunden: {result.stderr}"

            elif action == "start":
                result = subprocess.run(
                    ["launchctl", "start", service_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return f"✓ Service '{service_name}' erfolgreich gestartet"
                else:
                    return f"❌ Fehler beim Starten: {result.stderr}"

            elif action == "stop":
                result = subprocess.run(
                    ["launchctl", "stop", service_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return f"✓ Service '{service_name}' erfolgreich gestoppt"
                else:
                    return f"❌ Fehler beim Stoppen: {result.stderr}"

            elif action == "restart":
                # Stop
                subprocess.run(
                    ["launchctl", "stop", service_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                # Start
                result = subprocess.run(
                    ["launchctl", "start", service_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return f"✓ Service '{service_name}' erfolgreich neugestartet"
                else:
                    return f"❌ Fehler beim Neustarten: {result.stderr}"

        except subprocess.TimeoutExpired:
            return f"❌ Timeout bei Service-Operation (>30s)"
        except Exception as e:
            return f"❌ Fehler: {str(e)}"
