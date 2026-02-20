"""
CE365 Agent - File Reading Tools

Dateien lesen, durchsuchen und Log-Tails fuer Diagnose.
Pro-Feature: Erfordert "file_reading" Feature-Flag.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.tools.sanitize import validate_read_path


class ReadFileTool(AuditTool):
    """Datei lesen mit Groessenlimit"""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Liest eine Datei und gibt den Inhalt zurueck. "
            "Max. 200 Zeilen und 1 MB. Nutze dies um Konfigurationsdateien, "
            "Logs oder andere Textdateien zu inspizieren. "
            "Blockierte Pfade: /etc/shadow, *.pem, *.key, .ssh/id_*, .env, credentials*"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absoluter Pfad zur Datei",
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximale Anzahl Zeilen (Standard: 200)",
                    "default": 200,
                },
            },
            "required": ["path"],
        }

    async def execute(self, **kwargs) -> str:
        path_str = kwargs.get("path", "")
        max_lines = kwargs.get("max_lines", 200)

        # Sicherheitspruefung
        try:
            validate_read_path(path_str)
        except ValueError as e:
            return f"Zugriff verweigert: {e}"

        path = Path(path_str)
        if not path.exists():
            return f"Datei nicht gefunden: {path_str}"
        if not path.is_file():
            return f"Kein regulaere Datei: {path_str}"

        # Groessenlimit: 1 MB
        file_size = path.stat().st_size
        if file_size > 1_048_576:
            return (
                f"Datei zu gross: {file_size / 1024:.0f} KB (Max: 1024 KB). "
                "Nutze 'tail_log' fuer grosse Dateien."
            )

        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except PermissionError:
            return f"Keine Leseberechtigung: {path_str}"
        except Exception as e:
            return f"Fehler beim Lesen: {e}"

        total_lines = len(lines)
        truncated = total_lines > max_lines
        display_lines = lines[:max_lines]

        result = [f"Datei: {path_str}"]
        result.append(f"Groesse: {file_size} Bytes | Zeilen: {total_lines}")
        if truncated:
            result.append(f"(Zeige erste {max_lines} von {total_lines} Zeilen)")
        result.append("---")
        result.extend(display_lines)

        return "\n".join(result)


class SearchInFileTool(AuditTool):
    """In Datei nach Pattern suchen"""

    @property
    def name(self) -> str:
        return "search_in_file"

    @property
    def description(self) -> str:
        return (
            "Durchsucht eine Datei nach einem Regex-Pattern. "
            "Gibt passende Zeilen mit Zeilennummern zurueck. "
            "Max. 50 Treffer. Ideal fuer Log-Analyse und Fehlersuche."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absoluter Pfad zur Datei",
                },
                "pattern": {
                    "type": "string",
                    "description": "Regex-Suchmuster (z.B. 'error|warn|fail')",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximale Treffer (Standard: 50)",
                    "default": 50,
                },
            },
            "required": ["path", "pattern"],
        }

    async def execute(self, **kwargs) -> str:
        path_str = kwargs.get("path", "")
        pattern = kwargs.get("pattern", "")
        max_results = kwargs.get("max_results", 50)

        if not pattern:
            return "Kein Suchmuster angegeben"

        # Sicherheitspruefung
        try:
            validate_read_path(path_str)
        except ValueError as e:
            return f"Zugriff verweigert: {e}"

        path = Path(path_str)
        if not path.exists():
            return f"Datei nicht gefunden: {path_str}"
        if not path.is_file():
            return f"Keine regulaere Datei: {path_str}"

        # Regex kompilieren
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return f"Ungueltiges Regex-Pattern: {e}"

        # Datei durchsuchen
        matches = []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, 1):
                    if regex.search(line):
                        matches.append(f"{line_num:>6}: {line.rstrip()}")
                        if len(matches) >= max_results:
                            break
        except PermissionError:
            return f"Keine Leseberechtigung: {path_str}"
        except Exception as e:
            return f"Fehler beim Durchsuchen: {e}"

        if not matches:
            return f"Keine Treffer fuer '{pattern}' in {path_str}"

        result = [f"Suche in: {path_str}"]
        result.append(f"Pattern: {pattern}")
        result.append(f"Treffer: {len(matches)}")
        if len(matches) >= max_results:
            result.append(f"(Limit {max_results} erreicht — moeglicherweise mehr Treffer)")
        result.append("---")
        result.extend(matches)

        return "\n".join(result)


class TailLogTool(AuditTool):
    """Letzte N Zeilen einer Datei (optimiert fuer grosse Logs)"""

    @property
    def name(self) -> str:
        return "tail_log"

    @property
    def description(self) -> str:
        return (
            "Zeigt die letzten N Zeilen einer Datei (Standard: 100). "
            "Optimiert fuer grosse Log-Dateien — liest nur das Ende. "
            "Ideal fuer: /var/log/system.log, Windows Event Logs, etc."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absoluter Pfad zur Log-Datei",
                },
                "lines": {
                    "type": "integer",
                    "description": "Anzahl Zeilen vom Ende (Standard: 100)",
                    "default": 100,
                },
            },
            "required": ["path"],
        }

    async def execute(self, **kwargs) -> str:
        path_str = kwargs.get("path", "")
        num_lines = kwargs.get("lines", 100)

        # Sicherheitspruefung
        try:
            validate_read_path(path_str)
        except ValueError as e:
            return f"Zugriff verweigert: {e}"

        path = Path(path_str)
        if not path.exists():
            return f"Datei nicht gefunden: {path_str}"
        if not path.is_file():
            return f"Keine regulaere Datei: {path_str}"

        file_size = path.stat().st_size

        # Effizientes Tail: von hinten lesen
        try:
            tail_lines = self._tail(path, num_lines)
        except PermissionError:
            return f"Keine Leseberechtigung: {path_str}"
        except Exception as e:
            return f"Fehler beim Lesen: {e}"

        result = [f"Datei: {path_str}"]
        result.append(f"Groesse: {file_size / 1024:.1f} KB")
        result.append(f"Letzte {len(tail_lines)} Zeilen:")
        result.append("---")
        result.extend(tail_lines)

        return "\n".join(result)

    def _tail(self, path: Path, num_lines: int) -> list:
        """Effizientes Tail — liest Datei von hinten"""
        with open(path, "rb") as f:
            # Ans Ende springen
            f.seek(0, 2)
            file_size = f.tell()

            if file_size == 0:
                return []

            # Blockweise von hinten lesen
            block_size = 8192
            blocks = []
            remaining = file_size
            lines_found = 0

            while remaining > 0 and lines_found <= num_lines:
                read_size = min(block_size, remaining)
                remaining -= read_size
                f.seek(remaining)
                block = f.read(read_size)
                blocks.insert(0, block)
                lines_found += block.count(b"\n")

            content = b"".join(blocks)
            all_lines = content.decode("utf-8", errors="replace").splitlines()

            return all_lines[-num_lines:]
