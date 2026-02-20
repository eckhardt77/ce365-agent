"""
CE365 Agent - User Account Audit

Alle Benutzerkonten, Admin-Status, deaktivierte Konten, letzter Login
macOS: dscl / dscacheutil
Windows: net user / PowerShell Get-LocalUser
"""

import platform
import subprocess
from typing import Dict, Any
from ce365.tools.base import AuditTool


def _run_cmd(cmd: list, timeout: int = 10) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


class UserAccountAuditTool(AuditTool):
    """Alle Benutzerkonten auflisten und pruefen"""

    @property
    def name(self) -> str:
        return "audit_user_accounts"

    @property
    def description(self) -> str:
        return (
            "Listet alle Benutzerkonten mit Details: Admin-Status, aktiv/deaktiviert, "
            "letzter Login, Passwort-Ablauf. "
            "Nutze dies bei: 1) Sicherheits-Audit, 2) Unbekannte Benutzer identifizieren, "
            "3) Admin-Rechte pruefen, 4) Deaktivierte Konten finden, "
            "5) Compliance-Check."
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
        lines = ["👥 BENUTZERKONTEN-AUDIT", "=" * 50, ""]

        if os_type == "Darwin":
            lines.extend(self._audit_macos())
        elif os_type == "Windows":
            lines.extend(self._audit_windows())
        else:
            lines.append("❌ Nicht unterstuetztes Betriebssystem")

        return "\n".join(lines)

    def _audit_macos(self) -> list:
        lines = []

        # Alle echten Benutzer (UID >= 500, nicht System)
        output = _run_cmd([
            "dscl", ".", "-list", "/Users", "UniqueID"
        ], timeout=10)

        if not output:
            lines.append("❌ Konnte Benutzer nicht auflisten")
            return lines

        users = []
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                username = parts[0]
                uid = int(parts[-1])
                # Nur echte Benutzer (UID >= 500), nicht _Dienste
                if uid >= 500 and not username.startswith("_"):
                    users.append((username, uid))

        # Admin-Gruppe pruefen
        admin_output = _run_cmd(["dscl", ".", "-read", "/Groups/admin", "GroupMembership"], timeout=5)
        admin_users = set()
        if admin_output:
            parts = admin_output.split(":", 1)
            if len(parts) > 1:
                admin_users = set(parts[1].strip().split())

        for username, uid in users:
            is_admin = username in admin_users
            role = "👑 Admin" if is_admin else "👤 Standard"

            # Letzte Login-Info
            last_login = _run_cmd(["last", "-1", username], timeout=5)
            login_info = ""
            if last_login:
                first_line = last_login.splitlines()[0] if last_login.splitlines() else ""
                if first_line and "still logged in" in first_line:
                    login_info = "✅ Aktuell eingeloggt"
                elif first_line and username in first_line:
                    # Datum extrahieren
                    parts = first_line.split()
                    if len(parts) >= 4:
                        login_info = " ".join(parts[2:6])

            line = f"   {role} {username} (UID: {uid})"
            if login_info:
                line += f" — Letzter Login: {login_info}"
            lines.append(line)

        # Home-Verzeichnisse ohne zugehoerigen User (verwaist)
        import os
        users_dir = "/Users"
        known_users = {u[0] for u in users}
        known_users.update({"Shared", ".localized"})

        try:
            for entry in os.listdir(users_dir):
                full_path = os.path.join(users_dir, entry)
                if os.path.isdir(full_path) and entry not in known_users and not entry.startswith("."):
                    lines.append(f"   ⚠️  Verwaistes Home-Verzeichnis: /Users/{entry}")
        except:
            pass

        lines.append("")
        lines.append(f"Gesamt: {len(users)} Benutzer, {len([u for u in users if u[0] in admin_users])} Admins")

        return lines

    def _audit_windows(self) -> list:
        lines = []

        # PowerShell Get-LocalUser (Windows 10+)
        ps_cmd = (
            "Get-LocalUser | ForEach-Object { "
            "\"$($_.Name)|$($_.Enabled)|$($_.LastLogon)|$($_.PasswordExpires)|$($_.Description)\" }"
        )
        output = _run_cmd(["powershell", "-Command", ps_cmd], timeout=15)

        if not output:
            # Fallback: net user
            return self._audit_windows_fallback()

        # Admin-Gruppe
        admin_cmd = (
            "Get-LocalGroupMember -Group 'Administrators' 2>$null | "
            "ForEach-Object { $_.Name.Split('\\')[-1] }"
        )
        admin_output = _run_cmd(["powershell", "-Command", admin_cmd], timeout=10)
        admin_users = set(admin_output.splitlines()) if admin_output else set()

        for line in output.splitlines():
            parts = line.strip().split("|")
            if len(parts) < 3:
                continue

            username = parts[0].strip()
            enabled = parts[1].strip().lower() == "true"
            last_logon = parts[2].strip() if len(parts) > 2 else ""
            pw_expires = parts[3].strip() if len(parts) > 3 else ""
            description = parts[4].strip() if len(parts) > 4 else ""

            is_admin = username in admin_users
            role = "👑 Admin" if is_admin else "👤 Standard"
            status = "✅ Aktiv" if enabled else "🔴 Deaktiviert"

            line_text = f"   {role} {username} — {status}"
            if description:
                line_text += f" ({description})"
            lines.append(line_text)

            details = []
            if last_logon and last_logon != "":
                details.append(f"Letzter Login: {last_logon}")
            if pw_expires and pw_expires != "":
                details.append(f"PW-Ablauf: {pw_expires}")

            if details:
                lines.append(f"      {' | '.join(details)}")

        # Zaehlung
        all_users = output.strip().splitlines()
        enabled_count = sum(1 for l in all_users if "|True|" in l)
        disabled_count = sum(1 for l in all_users if "|False|" in l)

        lines.append("")
        lines.append(f"Gesamt: {len(all_users)} Benutzer, {enabled_count} aktiv, {disabled_count} deaktiviert, {len(admin_users)} Admins")

        return lines

    def _audit_windows_fallback(self) -> list:
        """Fallback via net user"""
        lines = []

        output = _run_cmd(["net", "user"], timeout=10)
        if output:
            for line in output.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("-") and "command" not in stripped.lower() and "User accounts" not in stripped:
                    # Benutzer-Zeilen haben mehrere Namen mit Leerzeichen getrennt
                    for name in stripped.split():
                        if name:
                            lines.append(f"   👤 {name}")

        return lines
