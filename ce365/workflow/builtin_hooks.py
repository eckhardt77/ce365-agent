"""
CE365 Agent - Eingebaute Hooks

Standard-Hooks die automatisch registriert werden (Pro Edition).
"""

from ce365.workflow.hooks import BaseHook, HookEvent, HookContext, HookResult
from typing import List


class BackupCheckHook(BaseHook):
    """
    Prueft vor der ERSTEN Reparatur ob ein aktuelles Backup vorhanden ist.
    Warnt den User, blockiert aber NICHT die Ausfuehrung.
    Laeuft nur 1x pro Session (nicht bei jedem einzelnen Tool-Call).
    """

    def __init__(self):
        self._already_checked = False
        self._cached_result: HookResult | None = None

    @property
    def name(self) -> str:
        return "BackupCheck"

    @property
    def description(self) -> str:
        return "Warnt vor Reparaturen wenn kein aktuelles Backup vorhanden ist"

    @property
    def events(self) -> List[HookEvent]:
        return [HookEvent.PRE_REPAIR]

    async def execute(self, context: HookContext) -> HookResult:
        # Nur 1x pro Session pruefen, nicht bei jedem Tool-Call
        if self._already_checked:
            return self._cached_result or HookResult(proceed=True)
        self._already_checked = True
        import platform

        # Backup-Status pruefen (plattformuebergreifend)
        try:
            from ce365.core.command_runner import get_command_runner
            runner = get_command_runner()

            if platform.system() == "Darwin":
                # Time Machine pruefen
                result = runner.run_sync(["tmutil", "latestbackup"], timeout=5)
                if result.success and result.stdout:
                    self._cached_result = HookResult(
                        proceed=True,
                        message=f"Backup vorhanden: {result.stdout.split('/')[-1]}",
                    )
                else:
                    self._cached_result = HookResult(
                        proceed=True,  # Warnung, nicht blockieren
                        message="⚠️  Kein aktuelles Time Machine Backup gefunden! "
                                "Erstelle ein Backup bevor du Reparaturen durchfuehrst.",
                    )

            elif platform.system() == "Windows":
                # Windows Wiederherstellungspunkt pruefen
                result = runner.run_sync(
                    ["powershell", "-Command",
                     "Get-ComputerRestorePoint | Select-Object -First 1 -ExpandProperty Description"],
                    timeout=10,
                )
                if result.success and result.stdout:
                    self._cached_result = HookResult(
                        proceed=True,
                        message=f"Wiederherstellungspunkt: {result.stdout[:60]}",
                    )
                else:
                    self._cached_result = HookResult(
                        proceed=True,
                        message="⚠️  Kein Wiederherstellungspunkt gefunden! "
                                "Erstelle einen Restore Point bevor du Reparaturen durchfuehrst.",
                    )

        except Exception:
            pass

        self._cached_result = self._cached_result or HookResult(proceed=True)
        return self._cached_result


class VerifyRepairHook(BaseHook):
    """
    Fuehrt nach einer Reparatur eine kurze Verifikation durch.
    Loggt ob die Reparatur erfolgreich war.
    """

    @property
    def name(self) -> str:
        return "VerifyRepair"

    @property
    def description(self) -> str:
        return "Verifiziert nach einer Reparatur ob sie erfolgreich war"

    @property
    def events(self) -> List[HookEvent]:
        return [HookEvent.POST_REPAIR]

    async def execute(self, context: HookContext) -> HookResult:
        if context.tool_success:
            return HookResult(
                proceed=True,
                message=f"Reparatur '{context.tool_name}' erfolgreich abgeschlossen",
            )
        else:
            return HookResult(
                proceed=True,
                message=f"⚠️  Reparatur '{context.tool_name}' moeglicherweise fehlgeschlagen — "
                        "bitte manuell verifizieren",
            )


class SessionReportHook(BaseHook):
    """
    Am Session-Ende: Zusammenfassung der durchgefuehrten Aktionen.
    """

    def __init__(self):
        self._actions: list = []

    @property
    def name(self) -> str:
        return "SessionReport"

    @property
    def description(self) -> str:
        return "Erstellt am Session-Ende eine Zusammenfassung"

    @property
    def events(self) -> List[HookEvent]:
        return [HookEvent.POST_TOOL, HookEvent.SESSION_END]

    async def execute(self, context: HookContext) -> HookResult:
        if context.event == HookEvent.POST_TOOL:
            # Aktion merken
            self._actions.append({
                "tool": context.tool_name,
                "success": context.tool_success,
            })
            return HookResult()

        elif context.event == HookEvent.SESSION_END:
            if not self._actions:
                return HookResult()

            total = len(self._actions)
            success = sum(1 for a in self._actions if a["success"])
            tools = ", ".join(set(a["tool"] for a in self._actions))

            return HookResult(
                proceed=True,
                message=f"Session-Zusammenfassung: {total} Tool-Ausfuehrungen "
                        f"({success} erfolgreich). Tools: {tools}",
            )

        return HookResult()


def get_builtin_hooks() -> list:
    """Alle eingebauten Hooks zurueckgeben"""
    return [
        BackupCheckHook(),
        VerifyRepairHook(),
        SessionReportHook(),
    ]
