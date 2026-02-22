import re
from typing import List, Optional

# Patterns die als GO REPAIR erkannt werden (case-insensitive)
_GO_PATTERNS = [
    r"GO\s*REPAIR\s*[:\-]?\s*",       # "GO REPAIR:", "GO REPAIR", "GO REPAIR -"
    r"GO\s*[:\-]?\s*",                  # "GO:", "GO", "GO -"
]

# Patterns die als "alle Schritte freigeben" gelten
_APPROVE_ALL_PATTERNS = [
    r"^ja\b",                            # "ja", "ja Plan A", "ja mach das"
    r"^yes\b",                           # "yes"
    r"^ok\b",                            # "ok"
    r"^mach\b",                          # "mach das", "mach weiter"
    r"^passt\b",                         # "passt"
    r"^do\s*it\b",                       # "do it"
    r"^los\b",                           # "los", "los geht's"
    r"^bitte\b",                         # "bitte"
    r"^alles\b",                         # "alles"
]

# Maximale Schritt-Nummer fuer "alle freigeben"
_ALL_STEPS = list(range(1, 21))


class ExecutionLock:
    """
    Execution Lock für Repair-Tools

    Parsed "GO REPAIR" Befehle und verwaltet freigegebene Schritte.
    Erkennt flexible Eingaben wie "GO REPAIR: 1,2,3", "GO REPAIR",
    "ja mach das", "GO REPAIR: Desktop-Organisieren (Plan A)" etc.
    """

    @staticmethod
    def parse_go_command(command: str) -> Optional[tuple]:
        """
        Parse GO REPAIR Befehl — flexibel.

        Unterstützte Formate:
        - "GO REPAIR: 1,2,3"           → (Schritte [1,2,3], "")
        - "GO REPAIR: 1-3"             → (Schritte [1,2,3], "")
        - "GO REPAIR: 1,3-5,7"         → (Schritte [1,3,4,5,7], "")
        - "GO REPAIR"                  → (alle Schritte, "")
        - "GO REPAIR: disable Login Items [Notion, Steam]"
                                        → (alle Schritte, "disable Login Items [Notion, Steam]")
        - "GO"                          → (alle Schritte, "")

        Returns:
            tuple(List[int], str): (Freigegebene Schritte, Freitext) oder None wenn kein GO-Befehl.
            Freitext ist leer bei nummerierten Schritten oder reinem "GO REPAIR".
        """
        stripped = command.strip()

        # Prüfe ob es ein GO REPAIR Befehl ist
        if not ExecutionLock.is_go_command(stripped):
            return None

        # Steps-Teil extrahieren (alles nach "GO REPAIR:" oder "GO:")
        steps_str = ""
        for pattern in _GO_PATTERNS:
            match = re.match(pattern, stripped, re.IGNORECASE)
            if match:
                steps_str = stripped[match.end():].strip()
                break

        # Kein Steps-Teil → alle Schritte freigeben, kein Freitext
        if not steps_str:
            return (_ALL_STEPS[:], "")

        # Versuche Zahlen zu parsen
        steps = []
        has_numbers = False

        for part in steps_str.split(","):
            part = part.strip()
            if not part:
                continue

            # Range (1-3) — nur wenn beides Zahlen sind
            range_match = re.match(r"^(\d+)\s*-\s*(\d+)$", part)
            if range_match:
                start, end = int(range_match.group(1)), int(range_match.group(2))
                if start > end:
                    continue
                steps.extend(range(start, end + 1))
                has_numbers = True
                continue

            # Einzelne Zahl
            num_match = re.match(r"^(\d+)$", part)
            if num_match:
                steps.append(int(num_match.group(1)))
                has_numbers = True
                continue

            # Text (kein Zahlen-Format) → ignorieren

        # Wenn Zahlen gefunden → diese verwenden, kein Freitext
        if has_numbers and steps:
            return (sorted(set(steps)), "")

        # Keine Zahlen gefunden (z.B. "GO REPAIR: disable Login Items [Notion, Steam]")
        # → alle Schritte als Lock, Freitext als Kontext weiterleiten
        return (_ALL_STEPS[:], steps_str)

    @staticmethod
    def is_go_command(text: str) -> bool:
        """Check ob Text ein GO REPAIR Befehl oder eine Freigabe ist"""
        stripped = text.strip()

        # Explizite GO-Befehle
        for pattern in _GO_PATTERNS:
            if re.match(pattern + r"$", stripped, re.IGNORECASE) or \
               re.match(pattern + r".+", stripped, re.IGNORECASE):
                # Mindestens "GO" muss drin sein
                if re.search(r"\bGO\b", stripped, re.IGNORECASE):
                    return True

        return False

    @staticmethod
    def format_steps(steps: List[int]) -> str:
        """Steps als String formatieren (z.B. "1, 2, 3")"""
        return ", ".join(map(str, steps))
