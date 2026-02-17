"""
CE365 Agent - Security Status Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Sicherheits-Status prüfen:
- Windows: Firewall, Defender
- macOS: Firewall, Gatekeeper, XProtect
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import AuditTool


class CheckSecurityStatusTool(AuditTool):
    """
    Prüft Sicherheits-Status des Systems

    Windows: Firewall + Windows Defender
    macOS: Firewall + Gatekeeper + XProtect
    """

    @property
    def name(self) -> str:
        return "check_security_status"

    @property
    def description(self) -> str:
        return (
            "Prüft Sicherheits-Status (Firewall, Antivirus, Security Features). "
            "Nutze dies bei: 1) Sicherheits-Check, 2) Nach Malware-Verdacht, "
            "3) Regelmäßige Wartung, 4) Compliance-Checks. "
            "Zeigt: Firewall-Status, Antivirus-Status, letzte Scans."
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
        Prüft Security-Status

        Returns:
            Security-Status Report
        """
        os_type = platform.system()

        if os_type == "Windows":
            return self._check_windows_security()
        elif os_type == "Darwin":
            return self._check_macos_security()
        else:
            return f"❌ Nicht unterstütztes OS: {os_type}"

    def _check_windows_security(self) -> str:
        """Windows Security Status"""
        try:
            output = [
                "🛡️  Windows Security Status",
                ""
            ]

            # 1. Windows Firewall
            output.append("🔥 Windows Firewall:")
            try:
                result = subprocess.run(
                    ["netsh", "advfirewall", "show", "allprofiles", "state"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                fw_output = result.stdout

                # Parse Profile States
                profiles = ["Domain", "Private", "Public"]
                for profile in profiles:
                    if f"{profile} Profile" in fw_output:
                        # Find State after profile
                        lines = fw_output.split("\n")
                        for i, line in enumerate(lines):
                            if f"{profile} Profile" in line:
                                # Next line should have State
                                if i + 1 < len(lines) and "State" in lines[i + 1]:
                                    state_line = lines[i + 1]
                                    if "ON" in state_line.upper():
                                        output.append(f"  • {profile}: ✅ Aktiv")
                                    else:
                                        output.append(f"  • {profile}: ❌ Deaktiviert")
                                    break

            except Exception as e:
                output.append(f"  ⚠️  Konnte nicht geprüft werden: {str(e)}")

            output.append("")

            # 2. Windows Defender
            output.append("🛡️  Windows Defender:")
            try:
                ps_cmd = "Get-MpComputerStatus | Select-Object RealTimeProtectionEnabled, AntivirusEnabled, LastQuickScanTime, LastFullScanTime | Format-List"

                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                defender_output = result.stdout

                if "RealTimeProtectionEnabled" in defender_output:
                    if "True" in defender_output.split("RealTimeProtectionEnabled")[1].split("\n")[0]:
                        output.append("  • Real-Time Protection: ✅ Aktiv")
                    else:
                        output.append("  • Real-Time Protection: ❌ Deaktiviert")

                if "AntivirusEnabled" in defender_output:
                    if "True" in defender_output.split("AntivirusEnabled")[1].split("\n")[0]:
                        output.append("  • Antivirus: ✅ Aktiv")
                    else:
                        output.append("  • Antivirus: ❌ Deaktiviert")

                # Letzte Scans
                if "LastQuickScanTime" in defender_output:
                    scan_line = defender_output.split("LastQuickScanTime")[1].split("\n")[0]
                    output.append(f"  • Letzter Quick Scan: {scan_line.strip()}")

                if "LastFullScanTime" in defender_output:
                    scan_line = defender_output.split("LastFullScanTime")[1].split("\n")[0]
                    output.append(f"  • Letzter Full Scan: {scan_line.strip()}")

            except Exception as e:
                output.append(f"  ⚠️  Konnte nicht geprüft werden: {str(e)}")

            output.append("")

            # Zusammenfassung
            output.append("─" * 50)
            output.append("💡 Empfehlung:")
            output.append("  • Firewall sollte in allen Profilen aktiv sein")
            output.append("  • Windows Defender Real-Time Protection aktivieren")
            output.append("  • Regelmäßige Scans durchführen")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Security-Check: {str(e)}"

    def _check_macos_security(self) -> str:
        """macOS Security Status"""
        try:
            output = [
                "🛡️  macOS Security Status",
                ""
            ]

            # 1. Firewall
            output.append("🔥 macOS Firewall:")
            try:
                result = subprocess.run(
                    ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if "enabled" in result.stdout.lower():
                    output.append("  ✅ Firewall ist aktiv")
                else:
                    output.append("  ❌ Firewall ist deaktiviert")

            except Exception as e:
                output.append(f"  ⚠️  Konnte nicht geprüft werden: {str(e)}")

            output.append("")

            # 2. Gatekeeper
            output.append("🔐 Gatekeeper:")
            try:
                result = subprocess.run(
                    ["spctl", "--status"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if "assessments enabled" in result.stdout.lower():
                    output.append("  ✅ Gatekeeper ist aktiv")
                else:
                    output.append("  ❌ Gatekeeper ist deaktiviert")

            except Exception as e:
                output.append(f"  ⚠️  Konnte nicht geprüft werden")

            output.append("")

            # 3. XProtect (Malware Scanner)
            output.append("🦠 XProtect (Malware Protection):")
            try:
                # Check if XProtect plist exists
                import os
                xprotect_path = "/Library/Apple/System/Library/CoreServices/XProtect.bundle"

                if os.path.exists(xprotect_path):
                    output.append("  ✅ XProtect ist installiert")
                else:
                    output.append("  ⚠️  XProtect nicht gefunden")

            except:
                output.append("  ⚠️  Konnte nicht geprüft werden")

            output.append("")

            # 4. SIP (System Integrity Protection)
            output.append("🔒 System Integrity Protection (SIP):")
            try:
                result = subprocess.run(
                    ["csrutil", "status"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if "enabled" in result.stdout.lower():
                    output.append("  ✅ SIP ist aktiv")
                else:
                    output.append("  ⚠️  SIP ist deaktiviert (nicht empfohlen)")

            except:
                output.append("  ⚠️  Konnte nicht geprüft werden")

            output.append("")

            # Zusammenfassung
            output.append("─" * 50)
            output.append("💡 Empfehlung:")
            output.append("  • Firewall aktivieren (System Settings → Network → Firewall)")
            output.append("  • Gatekeeper sollte immer aktiv sein")
            output.append("  • SIP nicht deaktivieren (nur für Entwicklung)")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Security-Check: {str(e)}"
