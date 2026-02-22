"""
CE365 Agent - Apple Intelligence & Shortcuts Audit

Prueft Apple Intelligence Verfuegbarkeit, Siri-Einstellungen,
Shortcuts und Automator-Workflows.
"""

import platform
import os
from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.core.command_runner import get_command_runner


def _run_cmd(cmd: list, timeout: int = 15) -> str:
    result = get_command_runner().run_sync(cmd, timeout=timeout)
    return result.output


class AppleIntelligenceAuditTool(AuditTool):
    """Apple Intelligence & Shortcuts Audit — AI-Features, Siri, Kurzbefehle, Automator"""

    @property
    def name(self) -> str:
        return "audit_apple_intelligence"

    @property
    def description(self) -> str:
        return (
            "Prueft Apple Intelligence, Siri-Einstellungen, Shortcuts und "
            "Automator-Workflows auf macOS. "
            "Zeigt: AI-Verfuegbarkeit (M1+ & macOS 15+), Siri-Status, "
            "installierte Kurzbefehle, Automator-Workflows. "
            "Nutze dies bei: 1) System-Inventur, 2) Automatisierungs-Audit, "
            "3) Privacy-Check (AI-Features), 4) Workflow-Dokumentation."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        os_type = platform.system()

        if os_type != "Darwin":
            return "❌ Dieses Tool ist nur auf macOS verfuegbar."

        lines = ["🤖 APPLE INTELLIGENCE & SHORTCUTS AUDIT", "=" * 50, ""]

        lines.extend(self._check_apple_intelligence())
        lines.append("")
        lines.extend(self._check_siri())
        lines.append("")
        lines.extend(self._check_shortcuts())
        lines.append("")
        lines.extend(self._check_automator())
        lines.append("")
        lines.append("─" * 50)
        lines.extend(self._generate_recommendations())

        return "\n".join(lines)

    def _check_apple_intelligence(self) -> list:
        lines = ["🧠 APPLE INTELLIGENCE", "─" * 50]

        # Chip pruefen (M1+ erforderlich)
        try:
            chip_output = _run_cmd(["sysctl", "-n", "machdep.cpu.brand_string"], timeout=10)
            if chip_output:
                lines.append(f"   Prozessor: {chip_output.strip()}")
                is_apple_silicon = "apple" in chip_output.lower()
            else:
                is_apple_silicon = False
                lines.append("   ⚠️  Prozessor nicht ermittelbar")
        except Exception:
            is_apple_silicon = False
            lines.append("   ⚠️  Prozessor-Check fehlgeschlagen")

        # macOS Version pruefen (15+ erforderlich)
        try:
            version_output = _run_cmd(["sw_vers", "-productVersion"], timeout=10)
            if version_output:
                lines.append(f"   macOS Version: {version_output.strip()}")
                major_version = int(version_output.strip().split(".")[0])
                is_macos_15_plus = major_version >= 15
            else:
                is_macos_15_plus = False
        except Exception:
            is_macos_15_plus = False

        if is_apple_silicon and is_macos_15_plus:
            lines.append("   ✅ Apple Intelligence: Hardware kompatibel (Apple Silicon + macOS 15+)")
        elif not is_apple_silicon:
            lines.append("   ❌ Apple Intelligence: Nicht verfuegbar (Intel Mac)")
        elif not is_macos_15_plus:
            lines.append("   ❌ Apple Intelligence: Nicht verfuegbar (macOS < 15)")

        # Writing Tools / AI Einstellungen
        try:
            ai_output = _run_cmd(
                ["defaults", "read", "com.apple.assistant.support", "Assistant Enabled"],
                timeout=10,
            )
            if ai_output:
                if "1" in ai_output:
                    lines.append("   ✅ Assistant: Aktiviert")
                elif "0" in ai_output:
                    lines.append("   ❌ Assistant: Deaktiviert")
                else:
                    lines.append(f"   ℹ️  Assistant: {ai_output.strip()}")
        except Exception:
            lines.append("   ℹ️  Assistant-Status nicht ermittelbar")

        return lines

    def _check_siri(self) -> list:
        lines = ["🗣️  SIRI", "─" * 50]

        try:
            siri_output = _run_cmd(
                ["defaults", "read", "com.apple.Siri"],
                timeout=10,
            )
            if siri_output:
                for line in siri_output.splitlines():
                    stripped = line.strip()
                    if "StatusMenuVisible" in stripped:
                        if "1" in stripped:
                            lines.append("   ✅ Siri in Menueleiste: Sichtbar")
                        else:
                            lines.append("   ℹ️  Siri in Menueleiste: Ausgeblendet")
                    elif "VoiceTriggerEnabled" in stripped:
                        if "1" in stripped:
                            lines.append("   ✅ Hey Siri: Aktiviert")
                        else:
                            lines.append("   ℹ️  Hey Siri: Deaktiviert")
                    elif "TypeToSiriEnabled" in stripped:
                        if "1" in stripped:
                            lines.append("   ✅ Siri tippen: Aktiviert")
                        else:
                            lines.append("   ℹ️  Siri tippen: Deaktiviert")

                if not any("Siri" in l for l in lines[2:]):
                    lines.append(f"   ℹ️  Siri Einstellungen vorhanden")
            else:
                lines.append("   ℹ️  Siri-Einstellungen nicht lesbar (evtl. Standard)")
        except Exception:
            lines.append("   ℹ️  Siri-Status nicht ermittelbar")

        return lines

    def _check_shortcuts(self) -> list:
        lines = ["⚡ KURZBEFEHLE (SHORTCUTS)", "─" * 50]

        try:
            output = _run_cmd(["shortcuts", "list"], timeout=20)
            if output:
                shortcuts = [s.strip() for s in output.splitlines() if s.strip()]
                lines.append(f"   📊 Anzahl installierter Kurzbefehle: {len(shortcuts)}")
                lines.append("")

                for shortcut in shortcuts[:20]:
                    lines.append(f"   • {shortcut}")

                if len(shortcuts) > 20:
                    lines.append(f"   ... und {len(shortcuts) - 20} weitere")
            else:
                lines.append("   ℹ️  Keine Kurzbefehle installiert")
        except Exception:
            lines.append("   ℹ️  Kurzbefehle-App nicht verfuegbar")

        return lines

    def _check_automator(self) -> list:
        lines = ["🔧 AUTOMATOR WORKFLOWS", "─" * 50]

        workflow_dirs = [
            os.path.expanduser("~/Library/Services"),
            "/Library/Services",
            os.path.expanduser("~/Library/Workflows"),
        ]

        total_workflows = 0
        for dir_path in workflow_dirs:
            if os.path.isdir(dir_path):
                workflows = [
                    f for f in os.listdir(dir_path)
                    if f.endswith(".workflow")
                ]
                if workflows:
                    lines.append(f"\n   📂 {dir_path}:")
                    for wf in workflows:
                        lines.append(f"      • {wf}")
                        total_workflows += 1

        if total_workflows == 0:
            lines.append("   ℹ️  Keine Automator-Workflows gefunden")
        else:
            lines.append(f"\n   📊 Gesamt: {total_workflows} Workflow(s)")

        return lines

    def _generate_recommendations(self) -> list:
        lines = ["💡 Empfehlungen:"]
        lines.append("  • Apple Intelligence Datenschutz-Einstellungen pruefen")
        lines.append("  • Unbekannte Shortcuts auf verdaechtige Aktionen pruefen")
        lines.append("  • Automator-Workflows dokumentieren fuer Uebergaben")
        lines.append("  • Siri-Verlauf regelmaessig loeschen bei Datenschutz-Bedenken")
        return lines
