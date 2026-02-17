"""
TechCare Bot - Process Monitoring Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Prozess-Analyse:
- Top CPU/RAM Verbraucher finden
- Zombie-Prozesse erkennen
- Service-Status prüfen
"""

import psutil
from typing import Dict, Any, List
from techcare.tools.base import AuditTool


class CheckRunningProcessesTool(AuditTool):
    """
    Analysiert laufende Prozesse nach CPU & RAM-Nutzung

    Zeigt Top-Verbraucher und hilft bei:
    - Langsames System
    - Hohe CPU-Last
    - Speicher-Probleme
    - Unbekannte Prozesse
    """

    @property
    def name(self) -> str:
        return "check_running_processes"

    @property
    def description(self) -> str:
        return (
            "Analysiert laufende Prozesse und zeigt Top CPU/RAM Verbraucher. "
            "Nutze dies bei: 1) Langsames System, 2) Hohe CPU-Last, "
            "3) Speicher-Probleme, 4) Verdächtige Prozesse. "
            "Liefert sortierte Liste mit Prozessnamen, PID, CPU% und RAM%."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "sort_by": {
                    "type": "string",
                    "enum": ["cpu", "memory"],
                    "description": "Sortierung nach CPU oder RAM (Standard: cpu)",
                    "default": "cpu"
                },
                "limit": {
                    "type": "integer",
                    "description": "Anzahl Prozesse (Standard: 15)",
                    "default": 15
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Analysiert Prozesse

        Args:
            sort_by: Sortierung nach "cpu" oder "memory" (default: cpu)
            limit: Anzahl Prozesse (default: 15)

        Returns:
            Formatierte Prozess-Liste mit CPU/RAM
        """
        sort_by = kwargs.get("sort_by", "cpu")
        limit = kwargs.get("limit", 15)

        try:
            # Prozesse sammeln
            processes = []

            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'username']):
                try:
                    pinfo = proc.info
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu': pinfo['cpu_percent'],
                        'memory': pinfo['memory_percent'],
                        'status': pinfo['status'],
                        'username': pinfo['username']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sortieren
            if sort_by == "memory":
                processes.sort(key=lambda x: x['memory'] if x['memory'] else 0, reverse=True)
            else:
                processes.sort(key=lambda x: x['cpu'] if x['cpu'] else 0, reverse=True)

            # Limitieren
            top_processes = processes[:limit]

            # System-Statistiken
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Formatierung
            output = [
                f"🔍 Prozess-Analyse",
                f"",
                f"📊 System-Übersicht:",
                f"   CPU-Auslastung: {cpu_percent}%",
                f"   RAM-Auslastung: {memory_percent}% ({self._format_bytes(memory.used)} / {self._format_bytes(memory.total)})",
                f"",
                f"🔝 Top {limit} Prozesse (nach {sort_by.upper()}):",
                f""
            ]

            # Header
            output.append(f"{'PID':<8} {'CPU%':<8} {'RAM%':<8} {'Status':<12} {'Name'}")
            output.append("-" * 70)

            # Prozesse
            for proc in top_processes:
                cpu = f"{proc['cpu']:.1f}%" if proc['cpu'] else "0.0%"
                mem = f"{proc['memory']:.1f}%" if proc['memory'] else "0.0%"
                status = proc['status'][:10]
                name = proc['name'][:30]
                pid = proc['pid']

                output.append(f"{pid:<8} {cpu:<8} {mem:<8} {status:<12} {name}")

            # Warnungen
            output.append("")
            warnings = self._generate_warnings(top_processes, cpu_percent, memory_percent)
            if warnings:
                output.append("⚠️  Auffälligkeiten:")
                output.extend([f"   {w}" for w in warnings])

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler bei Prozess-Analyse: {str(e)}"

    def _format_bytes(self, bytes_value: int) -> str:
        """Formatiert Bytes zu GB/MB"""
        gb = bytes_value / (1024 ** 3)
        if gb >= 1:
            return f"{gb:.1f} GB"
        mb = bytes_value / (1024 ** 2)
        return f"{mb:.1f} MB"

    def _generate_warnings(self, processes: List[Dict], cpu_percent: float, memory_percent: float) -> List[str]:
        """Generiert Warnungen basierend auf Prozess-Daten"""
        warnings = []

        # Hohe System-Last
        if cpu_percent > 80:
            warnings.append(f"CPU-Auslastung sehr hoch ({cpu_percent}%)")

        if memory_percent > 90:
            warnings.append(f"RAM-Auslastung kritisch ({memory_percent}%)")
        elif memory_percent > 80:
            warnings.append(f"RAM-Auslastung hoch ({memory_percent}%)")

        # Prozess-spezifische Warnungen
        for proc in processes[:5]:  # Top 5 prüfen
            if proc['cpu'] and proc['cpu'] > 50:
                warnings.append(f"{proc['name']} nutzt {proc['cpu']:.1f}% CPU")

            if proc['memory'] and proc['memory'] > 20:
                warnings.append(f"{proc['name']} nutzt {proc['memory']:.1f}% RAM")

        return warnings
