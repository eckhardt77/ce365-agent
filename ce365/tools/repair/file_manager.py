"""
CE365 Agent - File Manager

Dateien erstellen, bearbeiten, loeschen und verschieben.
Alle Operationen mit Sicherheitspruefungen und Blocklisten.
"""

import platform
import shutil
from pathlib import Path
from typing import Dict, Any
from ce365.tools.base import RepairTool
from ce365.tools.sanitize import validate_file_path, BLOCKED_READ_PATTERNS


# Zusaetzliche Blocklist fuer Schreibzugriffe (kritische Systemdateien)
BLOCKED_WRITE_PATTERNS = [
    *BLOCKED_READ_PATTERNS,
    # Windows-kritisch
    "*/windows/system32/*",
    "*/windows/syswow64/*",
    "C:\\Windows\\*",
    # macOS-kritisch
    "/System/*",
    "/usr/bin/*",
    "/usr/sbin/*",
    "/usr/lib/*",
    # Boot
    "*/boot/*",
    "*/bootmgr*",
    "*/grub/*",
]

# Maximale Dateigroesse fuer Schreiboperationen: 1 MB
MAX_WRITE_SIZE = 1024 * 1024


def _validate_write_path(path: str) -> str:
    """
    Validiert einen Dateipfad fuer Schreibzugriff.
    Strenger als Lesezugriff — blockiert auch Systemverzeichnisse.
    """
    path = validate_file_path(path)

    from fnmatch import fnmatch
    path_lower = path.lower()
    for pattern in BLOCKED_WRITE_PATTERNS:
        if fnmatch(path_lower, pattern.lower()):
            raise ValueError(
                f"Schreibzugriff auf '{Path(path).name}' ist blockiert (Sicherheitsrichtlinie)"
            )

    return path


class WriteFileTool(RepairTool):
    """Datei erstellen oder ueberschreiben"""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return (
            "Erstellt eine neue Datei oder ueberschreibt eine bestehende. "
            "Nutze dies fuer: Konfigurationsdateien anpassen, Skripte erstellen, "
            "hosts-Eintraege hinzufuegen, etc. "
            "ACHTUNG: Ueberschreibt bestehende Dateien! "
            "Systemdateien und Credentials sind blockiert. "
            "Max 1 MB Inhalt. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Dateipfad (z.B. '/etc/hosts', '~/script.sh', 'C:\\temp\\config.ini')",
                },
                "content": {
                    "type": "string",
                    "description": "Dateiinhalt",
                },
                "append": {
                    "type": "boolean",
                    "description": "An bestehende Datei anhaengen statt ueberschreiben",
                    "default": False,
                },
                "create_dirs": {
                    "type": "boolean",
                    "description": "Fehlende Verzeichnisse automatisch erstellen",
                    "default": False,
                },
            },
            "required": ["path", "content"],
        }

    async def execute(self, **kwargs) -> str:
        path_str = kwargs.get("path", "").strip()
        content = kwargs.get("content", "")
        append = kwargs.get("append", False)
        create_dirs = kwargs.get("create_dirs", False)

        if not path_str:
            return "Dateipfad ist erforderlich"

        # Sicherheitspruefung
        try:
            path_str = _validate_write_path(path_str)
        except ValueError as e:
            return f"Blockiert: {e}"

        # Groessenlimit
        if len(content.encode("utf-8")) > MAX_WRITE_SIZE:
            return f"Inhalt zu gross (max {MAX_WRITE_SIZE // 1024} KB)"

        # Home-Verzeichnis expandieren
        path = Path(path_str).expanduser()

        try:
            # Verzeichnis erstellen falls noetig
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            if not path.parent.exists():
                return f"Verzeichnis existiert nicht: {path.parent}\nNutze create_dirs=true"

            existed = path.exists()
            mode = "a" if append else "w"

            with open(path, mode, encoding="utf-8") as f:
                f.write(content)

            if append:
                return f"Inhalt an '{path}' angehaengt ({len(content)} Bytes)."
            elif existed:
                return f"Datei '{path}' wurde ueberschrieben ({len(content)} Bytes)."
            else:
                return f"Datei '{path}' wurde erstellt ({len(content)} Bytes)."

        except PermissionError:
            return f"Keine Schreibberechtigung fuer '{path}'. Admin/sudo erforderlich."
        except Exception as e:
            return f"Fehler beim Schreiben: {e}"


class EditFileTool(RepairTool):
    """Zeilen in einer Datei suchen und ersetzen"""

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return (
            "Sucht und ersetzt Text in einer Datei. "
            "Ideal fuer: Konfigurationen aendern, Zeilen auskommentieren, "
            "Werte in Config-Dateien anpassen. "
            "Systemdateien und Credentials sind blockiert. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Dateipfad",
                },
                "search": {
                    "type": "string",
                    "description": "Text der gesucht werden soll (exakter Match)",
                },
                "replace": {
                    "type": "string",
                    "description": "Ersetzungstext",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Alle Vorkommen ersetzen (default: nur das erste)",
                    "default": False,
                },
            },
            "required": ["path", "search", "replace"],
        }

    async def execute(self, **kwargs) -> str:
        path_str = kwargs.get("path", "").strip()
        search = kwargs.get("search", "")
        replace = kwargs.get("replace", "")
        replace_all = kwargs.get("replace_all", False)

        if not path_str or not search:
            return "Dateipfad und Suchtext sind erforderlich"

        try:
            path_str = _validate_write_path(path_str)
        except ValueError as e:
            return f"Blockiert: {e}"

        path = Path(path_str).expanduser()

        if not path.exists():
            return f"Datei nicht gefunden: {path}"

        try:
            content = path.read_text(encoding="utf-8", errors="replace")

            count = content.count(search)
            if count == 0:
                return f"Suchtext nicht gefunden in '{path.name}'"

            if replace_all:
                new_content = content.replace(search, replace)
                replaced = count
            else:
                new_content = content.replace(search, replace, 1)
                replaced = 1

            path.write_text(new_content, encoding="utf-8")
            return f"{replaced} Stelle(n) in '{path.name}' ersetzt."

        except PermissionError:
            return f"Keine Schreibberechtigung fuer '{path}'. Admin/sudo erforderlich."
        except Exception as e:
            return f"Fehler beim Bearbeiten: {e}"


class DeleteFileTool(RepairTool):
    """Datei oder Ordner loeschen"""

    @property
    def name(self) -> str:
        return "delete_file"

    @property
    def description(self) -> str:
        return (
            "Loescht eine Datei oder einen Ordner. "
            "ACHTUNG: Daten sind danach weg! "
            "Systemdateien und Credentials sind blockiert. "
            "Ordner werden nur geloescht wenn recursive=true. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Pfad zur Datei oder zum Ordner",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Ordner rekursiv loeschen (alle Inhalte!)",
                    "default": False,
                },
            },
            "required": ["path"],
        }

    async def execute(self, **kwargs) -> str:
        path_str = kwargs.get("path", "").strip()
        recursive = kwargs.get("recursive", False)

        if not path_str:
            return "Dateipfad ist erforderlich"

        try:
            path_str = _validate_write_path(path_str)
        except ValueError as e:
            return f"Blockiert: {e}"

        path = Path(path_str).expanduser()

        if not path.exists():
            return f"Pfad existiert nicht: {path}"

        # Zusaetzlicher Schutz: kritische Verzeichnisse
        critical_dirs = [
            "/", "/Users", "/home", "/var", "/etc", "/tmp",
            "C:\\", "C:\\Users", "C:\\Windows", "C:\\Program Files",
        ]
        if str(path) in critical_dirs or str(path).rstrip("/\\") in critical_dirs:
            return f"Loeschen von '{path}' ist blockiert (kritisches Verzeichnis)!"

        try:
            if path.is_file():
                size = path.stat().st_size
                path.unlink()
                return f"Datei '{path.name}' geloescht ({size:,} Bytes)."
            elif path.is_dir():
                if not recursive:
                    return (
                        f"'{path.name}' ist ein Ordner. "
                        f"Nutze recursive=true um den Ordner und alle Inhalte zu loeschen."
                    )
                # Groesse und Dateianzahl ermitteln
                file_count = sum(1 for _ in path.rglob("*") if _.is_file())
                shutil.rmtree(path)
                return f"Ordner '{path.name}' geloescht ({file_count} Dateien)."
            else:
                return f"Unbekannter Pfadtyp: {path}"

        except PermissionError:
            return f"Keine Berechtigung zum Loeschen von '{path}'. Admin/sudo erforderlich."
        except Exception as e:
            return f"Fehler beim Loeschen: {e}"


class MoveFileTool(RepairTool):
    """Datei oder Ordner verschieben/umbenennen"""

    @property
    def name(self) -> str:
        return "move_file"

    @property
    def description(self) -> str:
        return (
            "Verschiebt oder benennt eine Datei/einen Ordner um. "
            "Systemdateien sind blockiert. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Quellpfad (Datei oder Ordner)",
                },
                "destination": {
                    "type": "string",
                    "description": "Zielpfad",
                },
            },
            "required": ["source", "destination"],
        }

    async def execute(self, **kwargs) -> str:
        source = kwargs.get("source", "").strip()
        destination = kwargs.get("destination", "").strip()

        if not source or not destination:
            return "Quell- und Zielpfad sind erforderlich"

        try:
            source = _validate_write_path(source)
            destination = _validate_write_path(destination)
        except ValueError as e:
            return f"Blockiert: {e}"

        src = Path(source).expanduser()
        dst = Path(destination).expanduser()

        if not src.exists():
            return f"Quelle existiert nicht: {src}"

        try:
            shutil.move(str(src), str(dst))
            return f"'{src.name}' wurde nach '{dst}' verschoben."
        except PermissionError:
            return f"Keine Berechtigung. Admin/sudo erforderlich."
        except Exception as e:
            return f"Fehler beim Verschieben: {e}"
