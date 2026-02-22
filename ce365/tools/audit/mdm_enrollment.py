"""
CE365 Agent - MDM & Enrollment Audit

Prueft MDM-Enrollment, Konfigurationsprofile und DEP-Status.
"""

import platform
from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.core.command_runner import get_command_runner


def _run_cmd(cmd: list, timeout: int = 15) -> str:
    result = get_command_runner().run_sync(cmd, timeout=timeout)
    return result.output


class MDMEnrollmentAuditTool(AuditTool):
    """MDM & Enrollment Audit — prueft MDM-Status, Profile und DEP-Enrollment"""

    @property
    def name(self) -> str:
        return "audit_mdm_enrollment"

    @property
    def description(self) -> str:
        return (
            "Prueft MDM-Enrollment und Konfigurationsprofile auf macOS. "
            "Zeigt: DEP-Status, MDM-Server, installierte Profile, Zertifikate, "
            "Ablaufdaten. "
            "Nutze dies bei: 1) Geraeteverwaltungs-Audit, 2) Compliance-Check, "
            "3) Vor Geraete-Rueckgabe, 4) Enrollment-Diagnose. "
            "Windows: Hinweis auf Intune/GPO."
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

        if os_type == "Windows":
            return (
                "ℹ️  MDM-Audit auf Windows:\n"
                "   Verwende stattdessen:\n"
                "   • dsregcmd /status — Azure AD / Intune Enrollment\n"
                "   • gpresult /R — Gruppenrichtlinien\n"
                "   • mdmdiagnosticstool — MDM-Diagnose"
            )

        if os_type != "Darwin":
            return "❌ Dieses Tool ist nur auf macOS und Windows verfuegbar."

        lines = ["📱 MDM & ENROLLMENT AUDIT", "=" * 50, ""]

        lines.extend(self._check_enrollment_status())
        lines.append("")
        lines.extend(self._check_dep_status())
        lines.append("")
        lines.extend(self._list_profiles())
        lines.append("")
        lines.extend(self._check_profile_details())
        lines.append("")
        lines.append("─" * 50)
        lines.extend(self._generate_recommendations())

        return "\n".join(lines)

    def _check_enrollment_status(self) -> list:
        lines = ["📋 ENROLLMENT STATUS", "─" * 50]

        try:
            output = _run_cmd(["profiles", "status", "-type", "enrollment"], timeout=15)
            if output:
                for line in output.splitlines():
                    stripped = line.strip()
                    if not stripped:
                        continue
                    if "enroll" in stripped.lower():
                        if "yes" in stripped.lower() or "true" in stripped.lower():
                            lines.append(f"   ✅ {stripped}")
                        elif "no" in stripped.lower() or "false" in stripped.lower():
                            lines.append(f"   ℹ️  {stripped}")
                        else:
                            lines.append(f"   ℹ️  {stripped}")
                    elif "mdm" in stripped.lower() or "server" in stripped.lower():
                        lines.append(f"   🔗 {stripped}")
                    else:
                        lines.append(f"   {stripped}")
            else:
                lines.append("   ℹ️  Kein MDM-Enrollment erkannt")
        except Exception as e:
            lines.append(f"   ⚠️  Fehler bei Enrollment-Check: {e}")

        return lines

    def _check_dep_status(self) -> list:
        lines = ["🏢 DEP / AUTOMATED DEVICE ENROLLMENT", "─" * 50]

        try:
            output = _run_cmd(
                ["profiles", "show", "-type", "enrollment"],
                timeout=15,
            )
            if output:
                mdm_server = None
                dep_enrolled = False

                for line in output.splitlines():
                    stripped = line.strip()
                    if "server" in stripped.lower() and "url" in stripped.lower():
                        mdm_server = stripped
                    if "dep" in stripped.lower() or "automated" in stripped.lower():
                        dep_enrolled = True
                    if stripped:
                        lines.append(f"   {stripped}")

                if mdm_server:
                    lines.append(f"\n   🔗 MDM-Server: {mdm_server}")
                if dep_enrolled:
                    lines.append("   ✅ Geraet ist DEP-enrolled")
                elif not any("✅" in l for l in lines):
                    lines.append("   ℹ️  Kein DEP-Enrollment erkannt")
            else:
                lines.append("   ℹ️  Keine Enrollment-Details verfuegbar")
        except Exception as e:
            lines.append(f"   ⚠️  Fehler bei DEP-Check: {e}")

        return lines

    def _list_profiles(self) -> list:
        lines = ["📄 INSTALLIERTE PROFILE", "─" * 50]

        try:
            output = _run_cmd(["profiles", "list"], timeout=15)
            if output:
                profile_count = 0
                for line in output.splitlines():
                    stripped = line.strip()
                    if not stripped:
                        continue
                    if "profileidentifier" in stripped.lower() or "attribute" in stripped.lower():
                        lines.append(f"      {stripped}")
                    elif stripped.startswith("_") or ":" in stripped:
                        lines.append(f"   {stripped}")
                        profile_count += 1
                    else:
                        lines.append(f"   {stripped}")

                if profile_count == 0 and len(output.strip()) > 0:
                    lines.append(f"   {output.strip()[:200]}")
            else:
                lines.append("   ℹ️  Keine Konfigurationsprofile installiert")
        except Exception as e:
            lines.append(f"   ⚠️  Fehler bei Profil-Auflistung: {e}")

        return lines

    def _check_profile_details(self) -> list:
        lines = ["🔍 PROFIL-DETAILS", "─" * 50]

        try:
            output = _run_cmd(
                ["profiles", "list", "-type", "configuration"],
                timeout=15,
            )
            if output:
                for line in output.splitlines():
                    stripped = line.strip()
                    if not stripped:
                        continue
                    if "expir" in stripped.lower() or "ablauf" in stripped.lower():
                        lines.append(f"   ⏰ {stripped}")
                    elif "certificate" in stripped.lower() or "zertifikat" in stripped.lower():
                        lines.append(f"   🔑 {stripped}")
                    elif stripped:
                        lines.append(f"   {stripped}")
            else:
                lines.append("   ℹ️  Keine Konfigurationsprofile gefunden")
        except Exception as e:
            lines.append(f"   ⚠️  Fehler bei Profil-Details: {e}")

        return lines

    def _generate_recommendations(self) -> list:
        lines = ["💡 Empfehlungen:"]
        lines.append("  • MDM-Profile regelmaessig auf Aktualitaet pruefen")
        lines.append("  • Unbekannte Profile entfernen oder Administrator kontaktieren")
        lines.append("  • Vor Geraete-Rueckgabe: MDM-Enrollment pruefen")
        lines.append("  • Zertifikats-Ablaufdaten im Auge behalten")
        return lines
