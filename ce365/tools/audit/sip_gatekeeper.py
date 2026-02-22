"""
CE365 Agent - SIP & Gatekeeper Deep Audit

Tiefgehende Pruefung von System Integrity Protection, Gatekeeper,
Notarization und XProtect/MRT Versionen.
Ergaenzt den Basis-Check in security.py um detaillierte Analyse.
"""

import os
import platform
from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.core.command_runner import get_command_runner


def _run_cmd(cmd: list, timeout: int = 15) -> str:
    result = get_command_runner().run_sync(cmd, timeout=timeout)
    return result.output


class SIPGatekeeperAuditTool(AuditTool):
    """SIP & Gatekeeper Deep Audit — detaillierte Sicherheitsanalyse fuer macOS"""

    @property
    def name(self) -> str:
        return "audit_sip_gatekeeper"

    @property
    def description(self) -> str:
        return (
            "Tiefgehender SIP & Gatekeeper Audit fuer macOS. "
            "Prueft: SIP-Status mit einzelnen Schutz-Modulen, Authenticated Root, "
            "Gatekeeper mit Auto-Rearm, XProtect/MRT Versionen, "
            "und Notarization-Status installierter Apps. "
            "Nutze dies bei: 1) Security-Audit, 2) Compliance-Check, "
            "3) Nach Sicherheitsvorfall, 4) Systemhaertung."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "check_apps": {
                    "type": "boolean",
                    "description": "Ob App-Notarization per Stichprobe geprueft werden soll (default: true)",
                }
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        os_type = platform.system()

        if os_type != "Darwin":
            return "❌ Dieses Tool ist nur auf macOS verfuegbar."

        check_apps = kwargs.get("check_apps", True)
        lines = ["🔒 SIP & GATEKEEPER DEEP AUDIT", "=" * 50, ""]

        lines.extend(self._check_sip())
        lines.append("")
        lines.extend(self._check_gatekeeper())
        lines.append("")
        lines.extend(self._check_xprotect_mrt())

        if check_apps:
            lines.append("")
            lines.extend(self._check_notarization())

        lines.append("")
        lines.append("─" * 50)
        lines.extend(self._generate_recommendations())

        return "\n".join(lines)

    def _check_sip(self) -> list:
        lines = ["🛡️  SYSTEM INTEGRITY PROTECTION (SIP)", "─" * 50]

        try:
            output = _run_cmd(["csrutil", "status"], timeout=10)
            if output:
                if "enabled" in output.lower():
                    lines.append("✅ SIP: AKTIVIERT")
                elif "disabled" in output.lower():
                    lines.append("❌ SIP: DEAKTIVIERT")
                    lines.append("   ⚠️  System ist NICHT geschuetzt!")
                else:
                    lines.append(f"ℹ️  SIP Status: {output.strip()}")

                # Einzelne Module parsen
                for line in output.splitlines():
                    stripped = line.strip()
                    if ":" in stripped and stripped != output.splitlines()[0].strip():
                        if "enabled" in stripped.lower():
                            lines.append(f"   ✅ {stripped}")
                        elif "disabled" in stripped.lower():
                            lines.append(f"   ❌ {stripped}")
            else:
                lines.append("⚠️  SIP Status konnte nicht ermittelt werden")
        except Exception as e:
            lines.append(f"⚠️  Fehler bei SIP-Check: {e}")

        # Authenticated Root (Big Sur+)
        try:
            auth_root = _run_cmd(["csrutil", "authenticated-root", "status"], timeout=10)
            if auth_root:
                if "enabled" in auth_root.lower():
                    lines.append("✅ Authenticated Root: AKTIVIERT")
                elif "disabled" in auth_root.lower():
                    lines.append("❌ Authenticated Root: DEAKTIVIERT")
                else:
                    lines.append(f"ℹ️  Authenticated Root: {auth_root.strip()}")
        except Exception:
            lines.append("ℹ️  Authenticated Root: Nicht verfuegbar (vor macOS Big Sur)")

        return lines

    def _check_gatekeeper(self) -> list:
        lines = ["🔐 GATEKEEPER", "─" * 50]

        # Globaler Status
        try:
            output = _run_cmd(["spctl", "--status"], timeout=10)
            if output:
                if "assessments enabled" in output.lower():
                    lines.append("✅ Gatekeeper: AKTIVIERT")
                elif "assessments disabled" in output.lower():
                    lines.append("❌ Gatekeeper: DEAKTIVIERT")
                else:
                    lines.append(f"ℹ️  Gatekeeper Status: {output.strip()}")
            else:
                lines.append("⚠️  Gatekeeper Status nicht ermittelbar")
        except Exception as e:
            lines.append(f"⚠️  Fehler bei Gatekeeper-Check: {e}")

        # Auto-Rearm
        try:
            rearm = _run_cmd(
                ["defaults", "read", "/Library/Preferences/com.apple.security", "GKAutoRearm"],
                timeout=10,
            )
            if rearm:
                if "1" in rearm:
                    lines.append("✅ Auto-Rearm: AKTIVIERT")
                elif "0" in rearm:
                    lines.append("⚠️  Auto-Rearm: DEAKTIVIERT")
                else:
                    lines.append(f"ℹ️  Auto-Rearm: {rearm.strip()}")
            else:
                lines.append("ℹ️  Auto-Rearm: Standard (aktiviert)")
        except Exception:
            lines.append("ℹ️  Auto-Rearm: Standard (aktiviert)")

        return lines

    def _check_xprotect_mrt(self) -> list:
        lines = ["🦠 XPROTECT & MRT", "─" * 50]

        # XProtect Version
        try:
            output = _run_cmd(
                ["system_profiler", "SPInstallHistoryDataType"],
                timeout=30,
            )
            if output:
                xprotect_found = False
                mrt_found = False
                for i, line in enumerate(output.splitlines()):
                    if "XProtect" in line and not xprotect_found:
                        lines.append(f"✅ XProtect: {line.strip()}")
                        xprotect_found = True
                    if "MRT" in line and "Malware" in line and not mrt_found:
                        lines.append(f"✅ MRT: {line.strip()}")
                        mrt_found = True
                if not xprotect_found:
                    lines.append("⚠️  XProtect: Nicht im Installationsverlauf gefunden")
                if not mrt_found:
                    lines.append("ℹ️  MRT: Nicht im Installationsverlauf gefunden")
            else:
                lines.append("⚠️  Installationsverlauf nicht verfuegbar")
        except Exception as e:
            lines.append(f"⚠️  Fehler bei XProtect/MRT-Check: {e}")

        return lines

    def _check_notarization(self) -> list:
        lines = ["📋 NOTARIZATION (Stichprobe)", "─" * 50]

        apps_dir = "/Applications"
        try:
            if not os.path.isdir(apps_dir):
                lines.append("⚠️  /Applications nicht gefunden")
                return lines

            apps = [
                a for a in os.listdir(apps_dir)
                if a.endswith(".app")
            ][:5]

            if not apps:
                lines.append("ℹ️  Keine Apps in /Applications gefunden")
                return lines

            for app in apps:
                app_path = os.path.join(apps_dir, app)
                try:
                    output = _run_cmd(
                        ["spctl", "--assess", "--verbose=4", "--type", "execute", app_path],
                        timeout=15,
                    )
                    if output:
                        if "accepted" in output.lower():
                            if "notarized" in output.lower():
                                lines.append(f"   ✅ {app}: Notarisiert")
                            else:
                                lines.append(f"   ✅ {app}: Akzeptiert ({output.strip()})")
                        elif "rejected" in output.lower():
                            lines.append(f"   ❌ {app}: Abgelehnt")
                        else:
                            lines.append(f"   ℹ️  {app}: {output.strip()}")
                    else:
                        lines.append(f"   ℹ️  {app}: Status nicht ermittelbar")
                except Exception:
                    lines.append(f"   ℹ️  {app}: Check fehlgeschlagen")
        except Exception as e:
            lines.append(f"⚠️  Fehler bei Notarization-Check: {e}")

        return lines

    def _generate_recommendations(self) -> list:
        lines = ["💡 Empfehlungen:"]
        lines.append("  • SIP sollte IMMER aktiviert sein")
        lines.append("  • Gatekeeper nie dauerhaft deaktivieren")
        lines.append("  • XProtect-Updates automatisch installieren lassen")
        lines.append("  • Nur notarisierte Apps aus vertrauenswuerdigen Quellen installieren")
        return lines
