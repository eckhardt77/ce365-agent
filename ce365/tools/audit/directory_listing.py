"""
CE365 Agent - Directory Listing Tool

Verzeichnisinhalt auflisten mit Dateityp-Erkennung und Zusammenfassung.
Audit-Tool (read-only, immer erlaubt).
"""

import os
from pathlib import Path
from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.tools.sanitize import validate_file_path


class ListDirectoryTool(AuditTool):
    """Verzeichnisinhalt auflisten"""

    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return (
            "Listet den Inhalt eines Verzeichnisses auf — Dateien, Ordner, "
            "Dateitypen und Groessen. Ideal fuer: Desktop auflisten, Ordnerstruktur "
            "verstehen, Dateien nach Typ zaehlen. "
            "Read-only, aendert nichts am System."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Verzeichnispfad (z.B. '~/Desktop', '/Users/carsten/Documents', 'C:\\Users\\Admin\\Desktop')",
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Versteckte Dateien anzeigen (Standard: nein)",
                    "default": False,
                },
                "group_by_type": {
                    "type": "boolean",
                    "description": "Nach Dateityp gruppieren mit Zusammenfassung (Standard: ja)",
                    "default": True,
                },
            },
            "required": ["path"],
        }

    async def execute(self, **kwargs) -> str:
        path_str = kwargs.get("path", "").strip()
        show_hidden = kwargs.get("show_hidden", False)
        group_by_type = kwargs.get("group_by_type", True)

        if not path_str:
            return "Verzeichnispfad ist erforderlich"

        # Home-Verzeichnis expandieren
        path = Path(path_str).expanduser().resolve()

        if not path.exists():
            return f"Verzeichnis existiert nicht: {path}"

        if not path.is_dir():
            return f"Pfad ist kein Verzeichnis: {path}"

        try:
            entries = list(path.iterdir())
        except PermissionError:
            return f"Keine Leseberechtigung fuer: {path}"

        # Filtern
        if not show_hidden:
            entries = [e for e in entries if not e.name.startswith(".")]

        # Sortieren: Ordner zuerst, dann alphabetisch
        dirs = sorted([e for e in entries if e.is_dir()], key=lambda x: x.name.lower())
        files = sorted([e for e in entries if e.is_file()], key=lambda x: x.name.lower())

        lines = []
        lines.append(f"Verzeichnis: {path}")
        lines.append(f"Inhalt: {len(dirs)} Ordner, {len(files)} Dateien")
        lines.append("")

        # Ordner auflisten
        if dirs:
            lines.append("ORDNER:")
            for d in dirs:
                try:
                    item_count = len(list(d.iterdir()))
                except PermissionError:
                    item_count = "?"
                lines.append(f"  📁 {d.name}/ ({item_count} Eintraege)")
            lines.append("")

        if group_by_type and files:
            # Nach Dateityp gruppieren
            type_groups: Dict[str, list] = {}
            for f in files:
                ext = f.suffix.lower() if f.suffix else "(ohne Endung)"
                if ext not in type_groups:
                    type_groups[ext] = []
                try:
                    size = f.stat().st_size
                except OSError:
                    size = 0
                type_groups[ext].append((f.name, size))

            lines.append("DATEIEN (nach Typ):")
            for ext in sorted(type_groups.keys()):
                group = type_groups[ext]
                total_size = sum(s for _, s in group)
                lines.append(f"  {ext} — {len(group)} Dateien ({_format_size(total_size)}):")
                for name, size in group[:20]:  # Max 20 pro Typ
                    lines.append(f"    {name} ({_format_size(size)})")
                if len(group) > 20:
                    lines.append(f"    ... und {len(group) - 20} weitere")
            lines.append("")

            # Zusammenfassung
            total_size = sum(f.stat().st_size for f in files if f.exists())
            lines.append("ZUSAMMENFASSUNG:")
            for ext in sorted(type_groups.keys(), key=lambda x: len(type_groups[x]), reverse=True):
                lines.append(f"  {ext}: {len(type_groups[ext])} Dateien")
            lines.append(f"  GESAMT: {len(files)} Dateien, {_format_size(total_size)}")

        elif files:
            # Flache Liste
            lines.append("DATEIEN:")
            for f in files:
                try:
                    size = f.stat().st_size
                except OSError:
                    size = 0
                lines.append(f"  {f.name} ({_format_size(size)})")

        if not dirs and not files:
            lines.append("(Verzeichnis ist leer)")

        return "\n".join(lines)


def _format_size(size_bytes: int) -> str:
    """Bytes in menschenlesbare Groesse umrechnen"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
