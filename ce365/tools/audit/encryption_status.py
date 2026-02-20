"""
CE365 Agent - Encryption Status Check

BitLocker (Windows) / FileVault (macOS) Status pruefen
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import AuditTool


def _run_cmd(cmd: list, timeout: int = 15) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
    except Exception:
        return ""


class EncryptionStatusTool(AuditTool):
    """BitLocker/FileVault Verschluesselungsstatus pruefen"""

    @property
    def name(self) -> str:
        return "check_encryption_status"

    @property
    def description(self) -> str:
        return (
            "Prueft den Verschluesselungsstatus der Festplatten. "
            "Windows: BitLocker Status. macOS: FileVault Status. "
            "Nutze dies bei: 1) Sicherheits-Audit, 2) Compliance-Check, "
            "3) Vor Festplatten-Entsorgung, 4) Datenschutz-Pruefung."
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
        lines = ["🔐 VERSCHLUESSELUNGSSTATUS", "=" * 50, ""]

        if os_type == "Darwin":
            lines.extend(self._check_macos())
        elif os_type == "Windows":
            lines.extend(self._check_windows())
        else:
            lines.append("❌ Nicht unterstuetztes Betriebssystem")

        return "\n".join(lines)

    def _check_macos(self) -> list:
        lines = []

        # FileVault Status
        output = _run_cmd(["fdesetup", "status"], timeout=10)
        if output:
            if "On" in output or "is On" in output:
                lines.append("✅ FileVault: AKTIVIERT")
                lines.append(f"   {output}")
            elif "Off" in output or "is Off" in output:
                lines.append("🔴 FileVault: DEAKTIVIERT")
                lines.append("   ⚠️  Festplatte ist NICHT verschluesselt!")
                lines.append("   → Empfehlung: FileVault aktivieren unter")
                lines.append("     Systemeinstellungen → Datenschutz & Sicherheit → FileVault")
            else:
                lines.append(f"ℹ️  FileVault Status: {output}")
        else:
            lines.append("⚠️  FileVault Status konnte nicht ermittelt werden")

        lines.append("")

        # APFS Encryption per Volume
        apfs_output = _run_cmd(["diskutil", "apfs", "list"], timeout=10)
        if apfs_output:
            lines.append("📊 APFS Volume Verschluesselung:")
            for line in apfs_output.splitlines():
                stripped = line.strip()
                if "FileVault" in stripped or "Encryption" in stripped or "Encrypted" in stripped:
                    if "Yes" in stripped or "Unlocked" in stripped:
                        lines.append(f"   🔒 {stripped}")
                    elif "No" in stripped:
                        lines.append(f"   🔓 {stripped}")
                    else:
                        lines.append(f"   ℹ️  {stripped}")
                elif "Volume" in stripped and "Name" in stripped:
                    lines.append(f"   {stripped}")

        return lines

    def _check_windows(self) -> list:
        lines = []

        # BitLocker Status via manage-bde
        output = _run_cmd(["manage-bde", "-status"], timeout=15)
        if output:
            current_volume = ""
            for line in output.splitlines():
                stripped = line.strip()

                if "Volume" in stripped and ":" in stripped:
                    current_volume = stripped
                    lines.append(f"💾 {current_volume}")
                elif "Protection Status" in stripped or "Schutzstatus" in stripped:
                    if "Protection On" in stripped or "Schutz aktiviert" in stripped:
                        lines.append(f"   ✅ BitLocker: AKTIVIERT")
                    elif "Protection Off" in stripped or "Schutz deaktiviert" in stripped:
                        lines.append(f"   🔴 BitLocker: DEAKTIVIERT")
                    else:
                        lines.append(f"   ℹ️  {stripped}")
                elif "Encryption Method" in stripped or "Verschluesselungsmethode" in stripped:
                    lines.append(f"   {stripped}")
                elif "Percentage Encrypted" in stripped or "Verschluesselt" in stripped:
                    lines.append(f"   {stripped}")
                elif "Lock Status" in stripped or "Sperrstatus" in stripped:
                    lines.append(f"   {stripped}")

            if not lines:
                lines.append("ℹ️  BitLocker Status:")
                for line in output.splitlines()[:10]:
                    lines.append(f"   {line.strip()}")
        else:
            # Fallback: PowerShell
            ps_cmd = (
                "Get-BitLockerVolume 2>$null | "
                "ForEach-Object { \"$($_.MountPoint)|$($_.ProtectionStatus)|$($_.EncryptionPercentage)|$($_.VolumeStatus)\" }"
            )
            ps_output = _run_cmd(["powershell", "-Command", ps_cmd], timeout=15)

            if ps_output:
                for line in ps_output.splitlines():
                    parts = line.strip().split("|")
                    if len(parts) >= 3:
                        mount = parts[0].strip()
                        protection = parts[1].strip()
                        pct = parts[2].strip()

                        icon = "✅" if protection == "On" else "🔴"
                        lines.append(f"   {icon} {mount} — BitLocker: {protection} ({pct}% verschluesselt)")
            else:
                lines.append("⚠️  BitLocker Status nicht verfuegbar")
                lines.append("   (Erfordert Admin-Rechte oder BitLocker ist nicht installiert)")

        return lines
