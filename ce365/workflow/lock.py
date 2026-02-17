import re
from typing import List, Optional


class ExecutionLock:
    """
    Execution Lock für Repair-Tools

    Parsed "GO REPAIR" Befehle und verwaltet freigegebene Schritte
    """

    @staticmethod
    def parse_go_command(command: str) -> Optional[List[int]]:
        """
        Parse "GO REPAIR: X,Y,Z" oder "GO REPAIR: X-Y" Befehl

        Unterstützte Formate:
        - "GO REPAIR: 1,2,3"
        - "GO REPAIR: 1-3"
        - "GO REPAIR: 1,3-5,7"

        Args:
            command: User Input

        Returns:
            List[int]: Freigegebene Schritt-Nummern oder None wenn ungültig
        """
        # Normalisieren (case-insensitive, whitespace entfernen)
        command = command.strip().upper().replace(" ", "")

        # Pattern: GO REPAIR: <steps>
        match = re.match(r"GOREPAIR:(.+)", command)
        if not match:
            return None

        steps_str = match.group(1)
        steps = []

        # Parts splitten (Komma-separiert)
        for part in steps_str.split(","):
            part = part.strip()

            # Range (1-3)
            if "-" in part:
                try:
                    start, end = part.split("-")
                    start, end = int(start), int(end)
                    if start > end:
                        return None
                    steps.extend(range(start, end + 1))
                except ValueError:
                    return None

            # Einzelner Schritt (1)
            else:
                try:
                    steps.append(int(part))
                except ValueError:
                    return None

        # Duplikate entfernen, sortieren
        return sorted(set(steps))

    @staticmethod
    def is_go_command(text: str) -> bool:
        """Check ob Text ein GO REPAIR Befehl ist"""
        normalized = text.strip().upper().replace(" ", "")
        return normalized.startswith("GOREPAIR:")

    @staticmethod
    def format_steps(steps: List[int]) -> str:
        """Steps als String formatieren (z.B. "1, 2, 3")"""
        return ", ".join(map(str, steps))
