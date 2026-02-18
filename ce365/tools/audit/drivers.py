"""
CE365 Agent - Driver Check Audit Tool

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Integriert Driver-Prüfung in CE365 Agent Tool-System
"""

from ce365.tools.base import AuditTool
from ce365.tools.drivers.driver_manager import DriverManager


class CheckDriversTool(AuditTool):
    """
    Audit Tool: Treiber-Status prüfen

    Prüft alle installierten Treiber und empfiehlt Updates

    Returns:
        JSON-formatierter Report mit:
        - Anzahl installierter Treiber
        - Liste veralteter Treiber
        - Empfehlungen für Updates
    """

    name = "check_drivers"
    description = """Prüft Status aller installierten Treiber und empfiehlt Updates.

Zeigt:
- Anzahl installierter Treiber
- Veraltete Treiber mit verfügbaren Updates
- Kritische vs. empfohlene Updates
- Installations-Anweisungen

Quelle: Windows Update / macOS Software Update"""

    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }

    async def execute(self, **kwargs) -> str:
        """
        Führt Driver-Check aus

        Returns:
            Formatierter Report-String
        """
        try:
            manager = DriverManager()
            result = await manager.check_all_drivers()

            # Fehler-Handling
            if "error" in result:
                return f"❌ Fehler: {result['error']}"

            # Report formatieren
            output = []
            output.append("=" * 60)
            output.append("TREIBER-STATUS BERICHT")
            output.append("=" * 60)
            output.append("")

            # Statistik
            output.append(f"📊 Statistik:")
            if result.get("total_drivers"):
                output.append(f"   • Installierte Treiber: {result['total_drivers']}")
            output.append(f"   • Veraltete Treiber: {len(result['outdated_drivers'])}")
            output.append(f"   • Kritische Updates: {result['critical_count']}")
            output.append(f"   • Empfohlene Updates: {result['recommended_count']}")
            output.append("")

            # Veraltete Treiber
            if result["outdated_drivers"]:
                output.append("🔄 VERFÜGBARE UPDATES:")
                output.append("")

                for i, driver in enumerate(result["outdated_drivers"], 1):
                    severity_icon = "🔴" if driver["severity"] == "critical" else "🟡"
                    output.append(f"{severity_icon} {i}. {driver['name']}")
                    output.append(f"   Aktuell: {driver['current_version']}")
                    output.append(f"   Verfügbar: {driver['available_version']}")
                    output.append(f"   Wichtigkeit: {driver['severity'].upper()}")
                    output.append(f"   Quelle: {driver['source']}")
                    if driver.get("install_command"):
                        output.append(f"   Installation: {driver['install_command']}")
                    output.append("")
            else:
                output.append("✅ ALLE TREIBER AKTUELL!")
                output.append("")
                output.append("   Keine Updates verfügbar.")
                output.append("")

            # Empfehlungen
            if result["critical_count"] > 0:
                output.append("⚠️  EMPFEHLUNG:")
                output.append(f"   Installiere {result['critical_count']} kritische Treiber-Updates!")
                output.append("")

            output.append("=" * 60)

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Driver-Check: {str(e)}"
