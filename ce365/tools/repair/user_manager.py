"""
CE365 Agent - User Account Manager

Benutzerkonten verwalten: anlegen, loeschen, Passwort aendern, aktivieren/deaktivieren.
Windows: net user / PowerShell
macOS: dscl / sysadminctl
"""

import platform
from typing import Dict, Any
from ce365.tools.base import RepairTool
from ce365.core.command_runner import get_command_runner


class CreateUserTool(RepairTool):
    """Neuen Benutzer anlegen"""

    @property
    def name(self) -> str:
        return "create_user"

    @property
    def description(self) -> str:
        return (
            "Legt einen neuen Benutzer an. "
            "Windows: net user / PowerShell. macOS: sysadminctl. "
            "ACHTUNG: Erstellt ein neues Benutzerkonto auf dem System! "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Benutzername (alphanumerisch, keine Leerzeichen)",
                },
                "password": {
                    "type": "string",
                    "description": "Passwort fuer den neuen Benutzer",
                },
                "full_name": {
                    "type": "string",
                    "description": "Vollstaendiger Name (optional)",
                    "default": "",
                },
                "is_admin": {
                    "type": "boolean",
                    "description": "Benutzer als Administrator anlegen",
                    "default": False,
                },
            },
            "required": ["username", "password"],
        }

    async def execute(self, **kwargs) -> str:
        username = kwargs.get("username", "").strip()
        password = kwargs.get("password", "")
        full_name = kwargs.get("full_name", "").strip()
        is_admin = kwargs.get("is_admin", False)

        if not username or not password:
            return "Benutzername und Passwort sind erforderlich"

        if not username.isalnum() and "_" not in username and "-" not in username:
            return "Ungueltiger Benutzername (nur Buchstaben, Zahlen, _ und - erlaubt)"

        if len(password) < 8:
            return "Passwort muss mindestens 8 Zeichen lang sein"

        os_type = platform.system()
        runner = get_command_runner()

        if os_type == "Windows":
            return await self._create_windows(runner, username, password, full_name, is_admin)
        elif os_type == "Darwin":
            return await self._create_macos(runner, username, password, full_name, is_admin)
        else:
            return f"Benutzerverwaltung fuer {os_type} nicht unterstuetzt"

    async def _create_windows(self, runner, username, password, full_name, is_admin) -> str:
        # Benutzer anlegen
        cmd = ["net", "user", username, password, "/add"]
        if full_name:
            cmd.extend(["/fullname:" + full_name])
        cmd.append("/y")

        result = await runner.run(cmd, timeout=30)
        if not result.success:
            return f"Fehler beim Anlegen des Benutzers:\n{result.output}"

        lines = [f"Benutzer '{username}' wurde angelegt."]

        # Admin-Rechte
        if is_admin:
            admin_result = await runner.run(
                ["net", "localgroup", "Administrators", username, "/add"],
                timeout=15,
            )
            if admin_result.success:
                lines.append("Administrator-Rechte wurden zugewiesen.")
            else:
                # Deutsches Windows: Administratoren
                admin_result2 = await runner.run(
                    ["net", "localgroup", "Administratoren", username, "/add"],
                    timeout=15,
                )
                if admin_result2.success:
                    lines.append("Administrator-Rechte wurden zugewiesen.")
                else:
                    lines.append(f"Admin-Zuweisung fehlgeschlagen: {admin_result.output}")

        return "\n".join(lines)

    async def _create_macos(self, runner, username, password, full_name, is_admin) -> str:
        display_name = full_name if full_name else username
        admin_flag = "-admin" if is_admin else ""

        cmd = ["sudo", "sysadminctl", "-addUser", username,
               "-fullName", display_name, "-password", password]
        if admin_flag:
            cmd.append(admin_flag)

        result = await runner.run(cmd, timeout=30)
        if result.success or "created" in result.output.lower():
            admin_text = " (Administrator)" if is_admin else ""
            return f"Benutzer '{username}'{admin_text} wurde angelegt."
        return f"Fehler beim Anlegen des Benutzers:\n{result.output}"


class DeleteUserTool(RepairTool):
    """Benutzer loeschen"""

    @property
    def name(self) -> str:
        return "delete_user"

    @property
    def description(self) -> str:
        return (
            "Loescht einen Benutzer. "
            "ACHTUNG: Entfernt das Benutzerkonto! "
            "Optional wird auch das Home-Verzeichnis geloescht. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Benutzername zum Loeschen",
                },
                "delete_home": {
                    "type": "boolean",
                    "description": "Home-Verzeichnis mitloeschen (VORSICHT: Datenverlust!)",
                    "default": False,
                },
            },
            "required": ["username"],
        }

    async def execute(self, **kwargs) -> str:
        username = kwargs.get("username", "").strip()
        delete_home = kwargs.get("delete_home", False)

        if not username:
            return "Benutzername ist erforderlich"

        # Schutz: Systember nicht loeschen
        protected = ["root", "administrator", "admin", "system", "defaultuser0"]
        if username.lower() in protected:
            return f"Benutzer '{username}' ist ein Systemkonto und darf nicht geloescht werden!"

        os_type = platform.system()
        runner = get_command_runner()

        if os_type == "Windows":
            result = await runner.run(["net", "user", username, "/delete"], timeout=30)
            if result.success:
                return f"Benutzer '{username}' wurde geloescht."
            return f"Fehler:\n{result.output}"

        elif os_type == "Darwin":
            cmd = ["sudo", "sysadminctl", "-deleteUser", username]
            if delete_home:
                cmd.append("-secure")
            result = await runner.run(cmd, timeout=60)
            if result.success or "deleted" in result.output.lower():
                home_text = " (inkl. Home-Verzeichnis)" if delete_home else ""
                return f"Benutzer '{username}'{home_text} wurde geloescht."
            return f"Fehler:\n{result.output}"

        return f"Benutzerverwaltung fuer {os_type} nicht unterstuetzt"


class ChangePasswordTool(RepairTool):
    """Benutzer-Passwort aendern"""

    @property
    def name(self) -> str:
        return "change_user_password"

    @property
    def description(self) -> str:
        return (
            "Aendert das Passwort eines Benutzers. "
            "Nuetzlich wenn ein Benutzer sein Passwort vergessen hat. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Benutzername",
                },
                "new_password": {
                    "type": "string",
                    "description": "Neues Passwort (min. 8 Zeichen)",
                },
            },
            "required": ["username", "new_password"],
        }

    async def execute(self, **kwargs) -> str:
        username = kwargs.get("username", "").strip()
        new_password = kwargs.get("new_password", "")

        if not username or not new_password:
            return "Benutzername und neues Passwort sind erforderlich"

        if len(new_password) < 8:
            return "Passwort muss mindestens 8 Zeichen lang sein"

        os_type = platform.system()
        runner = get_command_runner()

        if os_type == "Windows":
            result = await runner.run(
                ["net", "user", username, new_password],
                timeout=15,
            )
            if result.success:
                return f"Passwort fuer '{username}' wurde geaendert."
            return f"Fehler:\n{result.output}"

        elif os_type == "Darwin":
            result = await runner.run(
                ["sudo", "sysadminctl", "-resetPasswordFor", username,
                 "-newPassword", new_password],
                timeout=15,
            )
            if result.success or "password" in result.output.lower():
                return f"Passwort fuer '{username}' wurde geaendert."
            return f"Fehler:\n{result.output}"

        return f"Benutzerverwaltung fuer {os_type} nicht unterstuetzt"


class ToggleUserTool(RepairTool):
    """Benutzer aktivieren oder deaktivieren"""

    @property
    def name(self) -> str:
        return "toggle_user"

    @property
    def description(self) -> str:
        return (
            "Aktiviert oder deaktiviert ein Benutzerkonto. "
            "Deaktivierte Benutzer koennen sich nicht anmelden. "
            "Nuetzlich bei Sicherheitsvorfaellen oder temporaerer Sperrung. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Benutzername",
                },
                "action": {
                    "type": "string",
                    "enum": ["enable", "disable"],
                    "description": "enable (aktivieren) oder disable (deaktivieren)",
                },
            },
            "required": ["username", "action"],
        }

    async def execute(self, **kwargs) -> str:
        username = kwargs.get("username", "").strip()
        action = kwargs.get("action", "")

        if not username or not action:
            return "Benutzername und Aktion sind erforderlich"

        os_type = platform.system()
        runner = get_command_runner()

        if os_type == "Windows":
            flag = "/active:yes" if action == "enable" else "/active:no"
            result = await runner.run(
                ["net", "user", username, flag],
                timeout=15,
            )
            if result.success:
                state = "aktiviert" if action == "enable" else "deaktiviert"
                return f"Benutzer '{username}' wurde {state}."
            return f"Fehler:\n{result.output}"

        elif os_type == "Darwin":
            # macOS: Shell auf /usr/bin/false setzen = deaktivieren
            if action == "disable":
                result = await runner.run(
                    ["sudo", "dscl", ".", "-create",
                     f"/Users/{username}", "UserShell", "/usr/bin/false"],
                    timeout=15,
                )
            else:
                result = await runner.run(
                    ["sudo", "dscl", ".", "-create",
                     f"/Users/{username}", "UserShell", "/bin/zsh"],
                    timeout=15,
                )
            if result.success:
                state = "aktiviert" if action == "enable" else "deaktiviert"
                return f"Benutzer '{username}' wurde {state}."
            return f"Fehler:\n{result.output}"

        return f"Benutzerverwaltung fuer {os_type} nicht unterstuetzt"
