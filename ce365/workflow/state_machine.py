from enum import Enum
from typing import Optional, List
from datetime import datetime


class WorkflowState(Enum):
    """Workflow States für CE365 Agent"""

    IDLE = "idle"  # Start-Zustand
    AUDIT = "audit"  # Audit-Phase (Read-Only)
    ANALYSIS = "analysis"  # Analyse-Phase
    PLAN_READY = "plan_ready"  # Plan erstellt, wartet auf GO REPAIR
    LOCKED = "locked"  # Nach GO REPAIR, Repair-Tools erlaubt
    EXECUTING = "executing"  # Repair läuft
    COMPLETED = "completed"  # Session abgeschlossen


class WorkflowStateMachine:
    """
    State Machine für CE365 Workflow

    Workflow:
    IDLE → AUDIT → ANALYSIS → PLAN_READY → LOCKED → EXECUTING → COMPLETED

    Rules:
    - Audit-Tools: Immer erlaubt (außer COMPLETED)
    - Repair-Tools: Nur in LOCKED/EXECUTING State
    - GO REPAIR: Transition von PLAN_READY → LOCKED
    """

    def __init__(self):
        self.current_state = WorkflowState.IDLE
        self.repair_plan: Optional[str] = None
        self.approved_steps: List[int] = []
        self.approval_text: str = ""
        self.executed_steps: List[int] = []
        self.state_history: List[tuple[WorkflowState, datetime]] = [
            (WorkflowState.IDLE, datetime.now())
        ]

    def transition_to(self, new_state: WorkflowState):
        """State Transition"""
        self.current_state = new_state
        self.state_history.append((new_state, datetime.now()))

    def can_execute_tool(self, tool_name: str, is_repair_tool: bool) -> tuple[bool, str]:
        """
        Check ob Tool im aktuellen State ausgeführt werden darf

        Args:
            tool_name: Name des Tools
            is_repair_tool: True wenn Repair-Tool

        Returns:
            (erlaubt: bool, fehler_nachricht: str)
        """
        # Session abgeschlossen
        if self.current_state == WorkflowState.COMPLETED:
            return False, "Session wurde bereits abgeschlossen. Starte neue Session."

        # Audit-Tools immer erlaubt
        if not is_repair_tool:
            if self.current_state == WorkflowState.IDLE:
                self.transition_to(WorkflowState.AUDIT)
            return True, ""

        # Repair-Tools nur nach GO REPAIR
        if self.current_state not in [WorkflowState.LOCKED, WorkflowState.EXECUTING]:
            # Auto-Transition zu PLAN_READY wenn Bot Repair-Tools ausfuehren will
            # Das signalisiert: "Claude hat einen Plan und braucht Freigabe"
            if self.current_state in [WorkflowState.IDLE, WorkflowState.AUDIT, WorkflowState.ANALYSIS]:
                self.transition_to(WorkflowState.PLAN_READY)
            return False, (
                f"Tool '{tool_name}' ist ein Repair-Tool und kann nur nach "
                "GO REPAIR Freigabe ausgeführt werden.\n"
                "Workflow: Audit → Analyse → Plan → GO REPAIR → Ausführung"
            )

        return True, ""

    def transition_to_plan_ready(self, plan: str):
        """
        Transition zu PLAN_READY State

        Args:
            plan: Reparatur-Plan (nummeriert)
        """
        self.repair_plan = plan
        self.transition_to(WorkflowState.PLAN_READY)

    def lock_execution(self, approved_steps: List[int], approval_text: str = ""):
        """
        Execution Lock aktivieren (nach GO REPAIR)

        Args:
            approved_steps: Liste der freigegebenen Schritt-Nummern
            approval_text: Optionaler Freitext aus GO REPAIR Befehl
        """
        if self.current_state != WorkflowState.PLAN_READY:
            raise ValueError(
                f"Lock kann nur von PLAN_READY aktiviert werden. "
                f"Aktueller State: {self.current_state.value}"
            )

        self.approved_steps = approved_steps
        self.approval_text = approval_text
        self.transition_to(WorkflowState.LOCKED)

    def is_step_approved(self, step_number: int) -> bool:
        """Check ob Schritt freigegeben wurde"""
        return step_number in self.approved_steps

    def mark_step_executed(self, step_number: int):
        """Schritt als ausgeführt markieren"""
        if step_number not in self.executed_steps:
            self.executed_steps.append(step_number)

        if self.current_state == WorkflowState.LOCKED:
            self.transition_to(WorkflowState.EXECUTING)

    def complete_session(self):
        """Session abschließen"""
        self.transition_to(WorkflowState.COMPLETED)

    def reset(self):
        """State Machine zurücksetzen"""
        self.__init__()

    def get_status(self) -> dict:
        """Aktuellen Status zurückgeben"""
        return {
            "state": self.current_state.value,
            "has_plan": self.repair_plan is not None,
            "approved_steps": self.approved_steps,
            "executed_steps": self.executed_steps,
        }

    def __repr__(self):
        return f"StateMachine(state={self.current_state.value})"
