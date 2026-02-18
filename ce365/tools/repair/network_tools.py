"""
CE365 Agent - Network Repair Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Netzwerk-Reparatur:
- DNS Cache Flush
- Network Stack Reset (Windows)
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import RepairTool


class FlushDNSCacheTool(RepairTool):
    """
    Leert DNS Cache

    Hilft bei:
    - Netzwerk-Verbindungsproblemen
    - "Server nicht gefunden" Fehlern
    - Nach DNS-Server Änderungen
    - Langsame Webseiten
    """

    @property
    def name(self) -> str:
        return "flush_dns_cache"

    @property
    def description(self) -> str:
        return (
            "Leert den DNS Cache. Nutze dies bei: "
            "1) Netzwerk-Verbindungsproblemen, "
            "2) 'Server nicht gefunden' Fehlern, "
            "3) Nach DNS-Änderungen, "
            "4) Langsamen Webseiten. "
            "WICHTIG: Erfordert GO REPAIR Freigabe!"
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
        Leert DNS Cache

        Returns:
            Erfolgsmeldung oder Fehler
        """
        os_type = platform.system()

        if os_type == "Windows":
            return self._flush_windows()
        elif os_type == "Darwin":
            return self._flush_macos()
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _flush_windows(self) -> str:
        """Windows DNS Cache leeren"""
        try:
            result = subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return (
                    "✅ DNS Cache geleert\n\n"
                    "Windows DNS Resolver Cache wurde erfolgreich geleert.\n"
                    "Netzwerk-Verbindungen sollten jetzt aktuelle DNS-Einträge nutzen."
                )
            else:
                return f"❌ Fehler beim Leeren: {result.stderr}"

        except subprocess.TimeoutExpired:
            return "❌ Timeout beim DNS Flush (>10s)"
        except Exception as e:
            return f"❌ Fehler: {str(e)}"

    def _flush_macos(self) -> str:
        """macOS DNS Cache leeren"""
        try:
            # macOS erfordert mehrere Kommandos
            commands = [
                ["sudo", "dscacheutil", "-flushcache"],
                ["sudo", "killall", "-HUP", "mDNSResponder"]
            ]

            for cmd in commands:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode != 0:
                    return f"❌ Fehler bei: {' '.join(cmd)}\n{result.stderr}"

            return (
                "✅ DNS Cache geleert\n\n"
                "macOS DNS Cache und mDNSResponder wurden zurückgesetzt.\n"
                "Netzwerk-Verbindungen sollten jetzt aktuelle DNS-Einträge nutzen.\n\n"
                "Hinweis: Erfordert Administrator-Rechte (sudo)."
            )

        except subprocess.TimeoutExpired:
            return "❌ Timeout beim DNS Flush (>10s)"
        except Exception as e:
            return f"❌ Fehler: {str(e)}"


class ResetNetworkStackTool(RepairTool):
    """
    Reset Network Stack (nur Windows)

    Setzt Winsock und TCP/IP Stack zurück
    Hilft bei schwerwiegenden Netzwerk-Problemen
    """

    @property
    def name(self) -> str:
        return "reset_network_stack"

    @property
    def description(self) -> str:
        return (
            "Setzt Windows Network Stack zurück (Winsock + TCP/IP). "
            "Nutze dies NUR bei schwerwiegenden Netzwerk-Problemen: "
            "1) Keine Netzwerk-Verbindung möglich, "
            "2) Nach Malware-Entfernung, "
            "3) Fehlerhafte Netzwerk-Treiber. "
            "ACHTUNG: Erfordert Neustart! "
            "WICHTIG: Nur für Windows, erfordert GO REPAIR!"
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
        Reset Network Stack

        Returns:
            Erfolgsmeldung mit Neustart-Hinweis
        """
        os_type = platform.system()

        if os_type != "Windows":
            return "❌ Dieses Tool ist nur für Windows verfügbar"

        try:
            commands = [
                ["netsh", "winsock", "reset"],
                ["netsh", "int", "ip", "reset"]
            ]

            results = []

            for cmd in commands:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                cmd_name = " ".join(cmd)
                if result.returncode == 0:
                    results.append(f"✓ {cmd_name}")
                else:
                    results.append(f"✗ {cmd_name}: {result.stderr}")

            output = [
                "⚠️  Network Stack Reset durchgeführt",
                "",
                "Ausgeführte Kommandos:"
            ]
            output.extend([f"  {r}" for r in results])

            output.append("")
            output.append("🔄 NEUSTART ERFORDERLICH!")
            output.append("")
            output.append("Führe einen Neustart durch, damit die Änderungen wirksam werden.")
            output.append("Nach dem Neustart sollten Netzwerk-Probleme behoben sein.")

            return "\n".join(output)

        except subprocess.TimeoutExpired:
            return "❌ Timeout beim Network Stack Reset (>30s)"
        except Exception as e:
            return f"❌ Fehler: {str(e)}"
