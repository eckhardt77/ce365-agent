import json
import os
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
    duration_ms: int = 0
    snapshot_before: str = ""
    snapshot_after: str = ""


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
        duration_ms: int = 0,
        snapshot_before: str = "",
        snapshot_after: str = "",
    ):
        """
        Changelog-Eintrag hinzufügen (mit PII-Anonymisierung)

        Args:
            tool_name: Name des ausgeführten Tools
            tool_input: Tool-Parameter
            result: Execution Result
            success: True wenn erfolgreich
            duration_ms: Ausfuehrungsdauer in Millisekunden
            snapshot_before: Systemzustand vor Repair
            snapshot_after: Systemzustand nach Repair
        """
        # PII in tool_input und result anonymisieren
        anonymized_input = self._anonymize_dict(tool_input)
        anonymized_result = self._anonymize_text(result)

        entry = ChangelogEntry(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            tool_input=anonymized_input,
            result=anonymized_result,
            success=success,
            duration_ms=duration_ms,
            snapshot_before=snapshot_before,
            snapshot_after=snapshot_after,
        )
        self.entries.append(entry)

        # Sofort persistieren
        self._save()

    def _anonymize_text(self, text: str) -> str:
        """Anonymisiert PII in einem Text-String"""
        try:
            from ce365.security.pii_detector import get_pii_detector
            detector = get_pii_detector()
            if detector and detector.enabled:
                anonymized, _ = detector.anonymize(text)
                return anonymized
        except (ImportError, Exception):
            pass
        return text

    def _anonymize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymisiert PII in Dictionary-Werten (rekursiv)"""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._anonymize_text(value)
            elif isinstance(value, dict):
                result[key] = self._anonymize_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self._anonymize_text(v) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                result[key] = value
        return result

    def _save(self):
        """Changelog zu JSON-Datei schreiben (mit restriktiven Berechtigungen)"""
        data = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "entries": [asdict(entry) for entry in self.entries],
        }

        # Verzeichnis mit restriktiven Berechtigungen erstellen
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.log_path.parent, 0o700)
        except OSError:
            pass

        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Datei nur für Owner lesbar
        try:
            os.chmod(self.log_path, 0o600)
        except OSError:
            pass

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
            duration_str = f"{entry.duration_ms / 1000:.1f}s" if entry.duration_ms else "N/A"

            lines.append(f"📝 ÄNDERUNGSLOG - Schritt {i}")
            lines.append("─" * 50)
            lines.append(f"Zeitstempel: {entry.timestamp[:19]}")
            lines.append(f"Aktion: {entry.tool_name}")
            lines.append(f"Kommando: {entry.tool_input}")
            lines.append(f"Status: {status}")
            lines.append(f"Dauer: {duration_str}")
            lines.append(f"Output: {entry.result}")
            if entry.snapshot_before:
                lines.append(f"Vorher: {entry.snapshot_before}")
            if entry.snapshot_after:
                lines.append(f"Nachher: {entry.snapshot_after}")
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
        # Abwaertskompatibilitaet: alte Eintraege ohne neue Felder
        entries = []
        for entry_data in data["entries"]:
            entry_data.setdefault("duration_ms", 0)
            entry_data.setdefault("snapshot_before", "")
            entry_data.setdefault("snapshot_after", "")
            entries.append(ChangelogEntry(**entry_data))
        writer.entries = entries

        return writer
