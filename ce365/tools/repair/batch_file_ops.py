"""
CE365 Agent - Batch File Operations

Mehrere Dateien gleichzeitig verschieben (nach Muster/Endung).
Ideal fuer Desktop-Sortierung und Datei-Organisation.
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List
from ce365.tools.base import RepairTool
from ce365.tools.sanitize import validate_file_path


class BatchMoveFilesTool(RepairTool):
    """Mehrere Dateien auf einmal verschieben (nach Muster/Endung)"""

    @property
    def name(self) -> str:
        return "batch_move_files"

    @property
    def description(self) -> str:
        return (
            "Verschiebt mehrere Dateien gleichzeitig basierend auf Dateiendungen. "
            "Ideal fuer: Desktop nach Dateityp sortieren, Dateien in Ordner organisieren. "
            "Erstellt Zielordner automatisch falls noetig. "
            "ACHTUNG: Verschiebt Dateien, loescht aber nichts. "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source_dir": {
                    "type": "string",
                    "description": "Quellverzeichnis (z.B. '~/Desktop')",
                },
                "rules": {
                    "type": "array",
                    "description": "Liste von Sortierregeln: welche Endungen wohin",
                    "items": {
                        "type": "object",
                        "properties": {
                            "extensions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Dateiendungen (z.B. ['.pdf', '.PDF'])",
                            },
                            "destination": {
                                "type": "string",
                                "description": "Zielordner (z.B. '~/Desktop/Sortiert/PDF')",
                            },
                        },
                        "required": ["extensions", "destination"],
                    },
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Versteckte Dateien einbeziehen (Standard: nein)",
                    "default": False,
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Nur anzeigen was verschoben wuerde, ohne tatsaechlich zu verschieben (Standard: nein)",
                    "default": False,
                },
            },
            "required": ["source_dir", "rules"],
        }

    async def execute(self, **kwargs) -> str:
        source_dir = kwargs.get("source_dir", "").strip()
        rules = kwargs.get("rules", [])
        include_hidden = kwargs.get("include_hidden", False)
        dry_run = kwargs.get("dry_run", False)

        if not source_dir:
            return "Quellverzeichnis ist erforderlich"
        if not rules:
            return "Mindestens eine Sortierregel ist erforderlich"

        src = Path(source_dir).expanduser().resolve()
        if not src.exists() or not src.is_dir():
            return f"Quellverzeichnis existiert nicht: {src}"

        # Alle Dateien im Quellverzeichnis sammeln (nur direkte Kinder)
        try:
            all_files = [f for f in src.iterdir() if f.is_file()]
        except PermissionError:
            return f"Keine Leseberechtigung fuer: {src}"

        if not include_hidden:
            all_files = [f for f in all_files if not f.name.startswith(".")]

        # Extension-zu-Destination Mapping aufbauen
        ext_map: Dict[str, Path] = {}
        for rule in rules:
            extensions = rule.get("extensions", [])
            dest_str = rule.get("destination", "")
            if not dest_str:
                continue
            dest = Path(dest_str).expanduser().resolve()
            for ext in extensions:
                ext_lower = ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                ext_map[ext_lower] = dest

        # Dateien zuordnen
        moves: List[tuple] = []  # (src_file, dest_dir)
        skipped: List[str] = []

        for f in all_files:
            ext = f.suffix.lower()
            if ext in ext_map:
                moves.append((f, ext_map[ext]))
            else:
                skipped.append(f.name)

        if not moves:
            return (
                f"Keine Dateien zum Verschieben gefunden.\n"
                f"Quellverzeichnis: {src}\n"
                f"Dateien ohne passende Regel: {len(skipped)}"
            )

        # Dry Run — nur anzeigen
        if dry_run:
            lines = [f"DRY RUN — {len(moves)} Dateien wuerden verschoben:"]
            lines.append("")
            by_dest: Dict[str, List[str]] = {}
            for src_file, dest_dir in moves:
                dest_name = dest_dir.name
                if dest_name not in by_dest:
                    by_dest[dest_name] = []
                by_dest[dest_name].append(src_file.name)

            for dest_name in sorted(by_dest.keys()):
                files = by_dest[dest_name]
                lines.append(f"→ {dest_name}/ ({len(files)} Dateien):")
                for name in files[:10]:
                    lines.append(f"  {name}")
                if len(files) > 10:
                    lines.append(f"  ... und {len(files) - 10} weitere")
                lines.append("")

            if skipped:
                lines.append(f"Nicht zugeordnet: {len(skipped)} Dateien (bleiben liegen)")

            return "\n".join(lines)

        # Tatsaechlich verschieben
        moved = 0
        errors: List[str] = []

        for src_file, dest_dir in moves:
            try:
                # Zielordner erstellen falls noetig
                dest_dir.mkdir(parents=True, exist_ok=True)

                dest_file = dest_dir / src_file.name
                # Bei Namenskollision: Datei umbenennen
                if dest_file.exists():
                    stem = src_file.stem
                    suffix = src_file.suffix
                    counter = 1
                    while dest_file.exists():
                        dest_file = dest_dir / f"{stem}_{counter}{suffix}"
                        counter += 1

                shutil.move(str(src_file), str(dest_file))
                moved += 1
            except Exception as e:
                errors.append(f"{src_file.name}: {e}")

        # Ergebnis
        lines = [f"{moved} Dateien verschoben."]
        lines.append("")

        # Zusammenfassung nach Ziel
        by_dest: Dict[str, int] = {}
        for _, dest_dir in moves:
            dest_name = dest_dir.name
            by_dest[dest_name] = by_dest.get(dest_name, 0) + 1
        for dest_name in sorted(by_dest.keys()):
            lines.append(f"  → {dest_name}/: {by_dest[dest_name]} Dateien")

        if skipped:
            lines.append(f"\nNicht zugeordnet (geblieben): {len(skipped)} Dateien")

        if errors:
            lines.append(f"\nFehler ({len(errors)}):")
            for err in errors[:10]:
                lines.append(f"  ❌ {err}")

        return "\n".join(lines)
