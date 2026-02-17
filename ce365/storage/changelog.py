import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from ce365.config.settings import get_settings


@dataclass
class ChangelogEntry:
    """Einzelner Changelog-Eintrag"""

    timestamp: str
    tool_name: str
    tool_input: Dict[str, Any]
    result: str
    success: bool


class ChangelogWriter:
    """
    Strukturiertes Änderungslog für Repair-Aktionen

    Format:
    {
      "session_id": "...",
      "created_at": "...",
      "entries": [...]
    }
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now().isoformat()
        self.entries: List[ChangelogEntry] = []

        settings = get_settings()
        self.log_path = settings.changelogs_dir / f"{session_id}.json"

    def add_entry(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        result: str,
        success: bool,
    ):
        """
        Changelog-Eintrag hinzufügen

        Args:
            tool_name: Name des ausgeführten Tools
            tool_input: Tool-Parameter
            result: Execution Result
            success: True wenn erfolgreich
        """
        entry = ChangelogEntry(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            tool_input=tool_input,
            result=result,
            success=success,
        )
        self.entries.append(entry)

        # Sofort persistieren
        self._save()

    def _save(self):
        """Changelog zu JSON-Datei schreiben"""
        data = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "entries": [asdict(entry) for entry in self.entries],
        }

        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_entries(self) -> List[ChangelogEntry]:
        """Alle Einträge zurückgeben"""
        return self.entries.copy()

    def get_summary(self) -> str:
        """Changelog-Zusammenfassung als String (neues Format)"""
        if not self.entries:
            return "Keine Änderungen durchgeführt."

        lines = []

        for i, entry in enumerate(self.entries, 1):
            status = "✓ ERFOLG" if entry.success else "✗ FEHLER"

            lines.append(f"📝 ÄNDERUNGSLOG - Schritt {i}")
            lines.append("─" * 50)
            lines.append(f"Zeitstempel: {entry.timestamp[:19]}")
            lines.append(f"Aktion: {entry.tool_name}")
            lines.append(f"Kommando: {entry.tool_input}")
            lines.append(f"Status: {status}")
            lines.append(f"Output: {entry.result}")
            lines.append(f"Rollback: [siehe Reparatur-Plan]")
            lines.append("─" * 50)
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def load(cls, session_id: str) -> "ChangelogWriter":
        """Changelog aus Datei laden"""
        settings = get_settings()
        log_path = settings.changelogs_dir / f"{session_id}.json"

        if not log_path.exists():
            return cls(session_id)

        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        writer = cls(session_id)
        writer.created_at = data["created_at"]
        writer.entries = [ChangelogEntry(**entry) for entry in data["entries"]]

        return writer
