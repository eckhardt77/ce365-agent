"""
CE365 Agent - TCC Privacy Audit

Prueft welche Apps welche Datenschutz-Berechtigungen haben
(Kamera, Mikrofon, Bildschirmaufnahme, Full Disk Access, etc.)
via TCC.db (read-only).
"""

import platform
import os
from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.core.command_runner import get_command_runner


def _run_cmd(cmd: list, timeout: int = 15) -> str:
    result = get_command_runner().run_sync(cmd, timeout=timeout)
    return result.output


# TCC Service-Namen → lesbare Bezeichnungen
TCC_SERVICES = {
    "kTCCServiceCamera": "Kamera",
    "kTCCServiceMicrophone": "Mikrofon",
    "kTCCServiceScreenCapture": "Bildschirmaufnahme",
    "kTCCServiceAccessibility": "Bedienungshilfen",
    "kTCCServiceSystemPolicyAllFiles": "Full Disk Access",
    "kTCCServiceSystemPolicySysAdminFiles": "Systemadmin-Dateien",
    "kTCCServiceAddressBook": "Kontakte",
    "kTCCServiceCalendar": "Kalender",
    "kTCCServiceReminders": "Erinnerungen",
    "kTCCServicePhotos": "Fotos",
    "kTCCServiceMediaLibrary": "Mediathek",
    "kTCCServiceListenEvent": "Tastatureingaben",
    "kTCCServicePostEvent": "Eingabeueberwachung",
}

# auth_value Mapping
AUTH_VALUES = {
    0: ("❌", "Verweigert"),
    1: ("⚠️", "Unbekannt"),
    2: ("✅", "Erlaubt"),
    3: ("⏳", "Eingeschraenkt"),
}


class TCCPrivacyAuditTool(AuditTool):
    """TCC Privacy Audit — prueft App-Berechtigungen fuer Kamera, Mikrofon, etc."""

    @property
    def name(self) -> str:
        return "audit_tcc_privacy"

    @property
    def description(self) -> str:
        return (
            "Prueft welche Apps welche Datenschutz-Berechtigungen haben (TCC). "
            "Zeigt: Kamera, Mikrofon, Bildschirmaufnahme, Full Disk Access, "
            "Bedienungshilfen und weitere Berechtigungen. "
            "Nutze dies bei: 1) Privacy-Audit, 2) Verdacht auf Spyware, "
            "3) Compliance-Check, 4) Berechtigungs-Inventur."
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

        lines = ["🔏 TCC PRIVACY AUDIT", "=" * 50, ""]

        lines.extend(self._check_user_tcc())
        lines.append("")
        lines.extend(self._check_system_tcc())
        lines.append("")
        lines.append("─" * 50)
        lines.extend(self._generate_recommendations())

        return "\n".join(lines)

    def _check_user_tcc(self) -> list:
        lines = ["👤 BENUTZER-BERECHTIGUNGEN (User TCC)", "─" * 50]

        home = os.path.expanduser("~")
        db_path = os.path.join(home, "Library/Application Support/com.apple.TCC/TCC.db")

        if not os.path.exists(db_path):
            lines.append("⚠️  User TCC.db nicht gefunden")
            return lines

        return self._query_tcc_db(db_path, lines)

    def _check_system_tcc(self) -> list:
        lines = ["🖥️  SYSTEM-BERECHTIGUNGEN (System TCC)", "─" * 50]

        db_path = "/Library/Application Support/com.apple.TCC/TCC.db"

        if not os.path.exists(db_path):
            lines.append("⚠️  System TCC.db nicht gefunden (Root-Rechte erforderlich)")
            return lines

        return self._query_tcc_db(db_path, lines)

    def _query_tcc_db(self, db_path: str, lines: list) -> list:
        try:
            query = "SELECT service, client, auth_value FROM access ORDER BY service, client"
            output = _run_cmd(
                ["sqlite3", db_path, query],
                timeout=10,
            )

            if not output:
                lines.append("ℹ️  Keine Eintraege gefunden oder Zugriff verweigert")
                return lines

            entries = self._parse_tcc_output(output)
            if not entries:
                lines.append("ℹ️  Keine Eintraege gefunden")
                return lines

            current_service = ""
            for service, client, auth_value in entries:
                service_label = TCC_SERVICES.get(service, service)
                if service != current_service:
                    lines.append(f"\n   📌 {service_label}:")
                    current_service = service

                icon, status = AUTH_VALUES.get(auth_value, ("❓", f"Wert {auth_value}"))
                app_name = client.split(".")[-1] if "." in client else client
                lines.append(f"      {icon} {app_name} ({client}) — {status}")

        except Exception as e:
            lines.append(f"⚠️  Fehler beim Lesen der TCC.db: {e}")

        return lines

    def _parse_tcc_output(self, output: str) -> list:
        entries = []
        for line in output.splitlines():
            parts = line.strip().split("|")
            if len(parts) >= 3:
                service = parts[0].strip()
                client = parts[1].strip()
                try:
                    auth_value = int(parts[2].strip())
                except ValueError:
                    auth_value = -1
                entries.append((service, client, auth_value))
        return entries

    def _generate_recommendations(self) -> list:
        lines = ["💡 Empfehlungen:"]
        lines.append("  • Unbekannte Apps mit Kamera/Mikrofon-Zugriff pruefen")
        lines.append("  • Bildschirmaufnahme nur fuer vertrauenswuerdige Apps erlauben")
        lines.append("  • Full Disk Access minimieren — nur fuer Backup/Security-Tools")
        lines.append("  • Berechtigungen regelmaessig unter Systemeinstellungen → Datenschutz pruefen")
        return lines
