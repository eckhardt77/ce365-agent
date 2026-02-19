"""
CE365 Agent - Consult Specialist Tool

Ermöglicht Steve, spezialisierte Agenten zu konsultieren.
Jeder Spezialist hat einen fokussierten System-Prompt und eigene Tools.
"""

from typing import Dict, Any
from ce365.tools.base import AuditTool


class ConsultSpecialistTool(AuditTool):
    """
    Tool zum Konsultieren eines Spezialisten.

    Steve (Orchestrator) delegiert an einen Spezialisten für
    Tiefendiagnose in einem bestimmten Bereich.
    """

    @property
    def name(self) -> str:
        return "consult_specialist"

    @property
    def description(self) -> str:
        return (
            "Konsultiere einen Spezialisten-Agenten für eine Tiefendiagnose. "
            "Verfügbare Spezialisten:\n"
            "- 'windows': WindowsDoc — Windows Event-Logs, Registry, Dienste, BSOD, Updates, Energie\n"
            "- 'macos': MacDoc — system_profiler, Unified Logging, APFS, LaunchAgents, TCC\n"
            "- 'network': NetDoc — DNS, DHCP, WLAN, Firewall, VPN, Latenz, Paketverlust\n"
            "- 'security': SecurityDoc — Malware, Autostart, Zertifikate, verdächtige Prozesse\n"
            "- 'performance': PerfDoc — CPU, RAM, Disk I/O, Thermal Throttling, Bottleneck\n\n"
            "Der Spezialist führt eine eigenständige Diagnose durch und liefert einen strukturierten Bericht zurück. "
            "Nutze dies für komplexe Probleme die Expertenwissen erfordern. "
            "Du kannst mehrere Spezialisten nacheinander konsultieren."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "specialist": {
                    "type": "string",
                    "enum": ["windows", "macos", "network", "security", "performance"],
                    "description": "Welcher Spezialist konsultiert werden soll",
                },
                "task": {
                    "type": "string",
                    "description": (
                        "Aufgabe/Frage an den Spezialisten. Sei spezifisch: "
                        "Was soll diagnostiziert werden? Welche Symptome gibt es?"
                    ),
                },
                "context": {
                    "type": "string",
                    "description": (
                        "Zusätzlicher Kontext: bisherige Diagnose-Ergebnisse, "
                        "Kundenaussagen, bereits geprüfte Dinge. Optional."
                    ),
                    "default": "",
                },
            },
            "required": ["specialist", "task"],
        }

    async def execute(
        self,
        specialist: str = "",
        task: str = "",
        context: str = "",
        **kwargs
    ) -> str:
        """Spezialist konsultieren — wird von bot.py überschrieben/aufgerufen"""
        # Placeholder — die eigentliche Ausführung passiert in bot.py
        # weil der Agent Zugriff auf den LLM-Client und die Tool-Registry braucht
        return f"[DELEGATE:{specialist}] {task}"
