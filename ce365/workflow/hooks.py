"""
CE365 Agent - Hook System

Event-basiertes Hook-System fuer Workflow-Automatisierung.
Hooks werden vor/nach Tool-Ausfuehrung und bei Session-Events gefeuert.

Pro-Feature: Erfordert "hooks" Feature-Flag.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Dict, Any, Optional


class HookEvent(Enum):
    """Verfuegbare Hook-Events"""
    PRE_TOOL = "pre_tool"          # Vor jedem Tool
    POST_TOOL = "post_tool"        # Nach jedem Tool
    PRE_REPAIR = "pre_repair"      # Vor jedem Repair-Tool
    POST_REPAIR = "post_repair"    # Nach jedem Repair-Tool
    SESSION_START = "session_start"
    SESSION_END = "session_end"


@dataclass
class HookContext:
    """Kontext-Daten die an Hooks uebergeben werden"""
    event: HookEvent
    tool_name: str = ""
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_result: str = ""
    tool_success: bool = True
    session_id: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HookResult:
    """Ergebnis eines Hook-Durchlaufs"""
    proceed: bool = True       # False = Tool-Ausfuehrung blockieren
    message: str = ""          # Nachricht fuer den User
    modified_input: Optional[Dict[str, Any]] = None  # Modifizierte Tool-Parameter


class BaseHook:
    """Basis-Klasse fuer alle Hooks"""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def description(self) -> str:
        return ""

    @property
    def events(self) -> List[HookEvent]:
        """Auf welche Events dieser Hook reagiert"""
        return []

    async def execute(self, context: HookContext) -> HookResult:
        """Hook ausfuehren — muss von Subklassen implementiert werden"""
        return HookResult()


class HookManager:
    """
    Verwaltet und fuehrt Hooks aus.

    Hooks werden nach Event-Typ gruppiert und in Registrierungs-Reihenfolge
    ausgefuehrt. Ein PRE-Hook kann die Tool-Ausfuehrung blockieren.
    """

    def __init__(self):
        self._hooks: Dict[HookEvent, List[BaseHook]] = {
            event: [] for event in HookEvent
        }
        self._enabled: bool = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    def register(self, hook: BaseHook):
        """Hook registrieren fuer alle seine Events"""
        for event in hook.events:
            if hook not in self._hooks[event]:
                self._hooks[event].append(hook)

    def unregister(self, hook: BaseHook):
        """Hook entfernen"""
        for event in hook.events:
            if hook in self._hooks[event]:
                self._hooks[event].remove(hook)

    def get_hooks(self, event: HookEvent) -> List[BaseHook]:
        """Alle Hooks fuer ein Event"""
        return self._hooks.get(event, [])

    async def run_hooks(
        self,
        event: HookEvent,
        context: HookContext,
    ) -> HookResult:
        """
        Alle Hooks fuer ein Event ausfuehren.

        Bei PRE-Events: Erster Hook der proceed=False zurueckgibt
        stoppt die Kette und blockiert die Tool-Ausfuehrung.

        Bei POST-Events: Alle Hooks werden immer ausgefuehrt.
        """
        if not self._enabled:
            return HookResult()

        hooks = self._hooks.get(event, [])
        if not hooks:
            return HookResult()

        messages = []
        is_pre_event = event in (HookEvent.PRE_TOOL, HookEvent.PRE_REPAIR)

        for hook in hooks:
            try:
                result = await hook.execute(context)

                if result.message:
                    messages.append(f"[{hook.name}] {result.message}")

                # PRE-Hooks koennen blockieren
                if is_pre_event and not result.proceed:
                    return HookResult(
                        proceed=False,
                        message="\n".join(messages),
                        modified_input=result.modified_input,
                    )

                # Input-Modifikation weitergeben
                if result.modified_input is not None:
                    context.tool_input = result.modified_input

            except Exception as e:
                messages.append(f"[{hook.name}] Hook-Fehler: {e}")

        return HookResult(
            proceed=True,
            message="\n".join(messages) if messages else "",
        )

    def get_registered_hooks(self) -> List[Dict[str, Any]]:
        """Uebersicht aller registrierten Hooks"""
        seen = set()
        hooks_info = []
        for event, hooks in self._hooks.items():
            for hook in hooks:
                if hook.name not in seen:
                    seen.add(hook.name)
                    hooks_info.append({
                        "name": hook.name,
                        "description": hook.description,
                        "events": [e.value for e in hook.events],
                    })
        return hooks_info
