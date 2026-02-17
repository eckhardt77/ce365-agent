"""
Tests für WorkflowStateMachine

Testet alle State Transitions und Tool-Freigabe-Logik.
"""

import pytest
from techcare.workflow.state_machine import WorkflowStateMachine, WorkflowState


class TestWorkflowStates:
    """Tests für WorkflowState Enum"""

    def test_all_states_defined(self):
        states = [s.value for s in WorkflowState]
        assert "idle" in states
        assert "audit" in states
        assert "analysis" in states
        assert "plan_ready" in states
        assert "locked" in states
        assert "executing" in states
        assert "completed" in states

    def test_state_count(self):
        assert len(WorkflowState) == 7


class TestStateMachineInit:
    """Tests für Initialisierung"""

    def test_initial_state_is_idle(self, state_machine):
        assert state_machine.current_state == WorkflowState.IDLE

    def test_initial_no_plan(self, state_machine):
        assert state_machine.repair_plan is None

    def test_initial_empty_steps(self, state_machine):
        assert state_machine.approved_steps == []
        assert state_machine.executed_steps == []

    def test_initial_history_has_idle(self, state_machine):
        assert len(state_machine.state_history) == 1
        assert state_machine.state_history[0][0] == WorkflowState.IDLE


class TestStateTransitions:
    """Tests für State Transitions"""

    def test_transition_to_audit(self, state_machine):
        state_machine.transition_to(WorkflowState.AUDIT)
        assert state_machine.current_state == WorkflowState.AUDIT

    def test_full_workflow(self, state_machine):
        """Kompletter Workflow: IDLE → AUDIT → ANALYSIS → PLAN_READY → LOCKED → EXECUTING → COMPLETED"""
        state_machine.transition_to(WorkflowState.AUDIT)
        state_machine.transition_to(WorkflowState.ANALYSIS)
        state_machine.transition_to_plan_ready("Plan: 1. DNS flush 2. Reboot")
        state_machine.lock_execution([1, 2])
        state_machine.mark_step_executed(1)
        assert state_machine.current_state == WorkflowState.EXECUTING
        state_machine.complete_session()
        assert state_machine.current_state == WorkflowState.COMPLETED

    def test_history_tracking(self, state_machine):
        state_machine.transition_to(WorkflowState.AUDIT)
        state_machine.transition_to(WorkflowState.ANALYSIS)
        assert len(state_machine.state_history) == 3
        assert state_machine.state_history[0][0] == WorkflowState.IDLE
        assert state_machine.state_history[1][0] == WorkflowState.AUDIT
        assert state_machine.state_history[2][0] == WorkflowState.ANALYSIS


class TestAuditToolExecution:
    """Tests für Audit-Tool Freigabe"""

    def test_audit_tool_allowed_in_idle(self, state_machine):
        allowed, msg = state_machine.can_execute_tool("get_system_info", False)
        assert allowed is True
        assert msg == ""

    def test_audit_tool_transitions_idle_to_audit(self, state_machine):
        state_machine.can_execute_tool("get_system_info", False)
        assert state_machine.current_state == WorkflowState.AUDIT

    def test_audit_tool_allowed_in_audit(self, state_machine):
        state_machine.transition_to(WorkflowState.AUDIT)
        allowed, _ = state_machine.can_execute_tool("check_logs", False)
        assert allowed is True

    def test_audit_tool_allowed_in_locked(self, state_machine):
        state_machine.transition_to(WorkflowState.AUDIT)
        state_machine.transition_to_plan_ready("Plan")
        state_machine.lock_execution([1])
        allowed, _ = state_machine.can_execute_tool("get_system_info", False)
        assert allowed is True

    def test_audit_tool_blocked_in_completed(self, state_machine):
        state_machine.transition_to(WorkflowState.COMPLETED)
        allowed, msg = state_machine.can_execute_tool("get_system_info", False)
        assert allowed is False
        assert "abgeschlossen" in msg


class TestRepairToolExecution:
    """Tests für Repair-Tool Freigabe"""

    def test_repair_blocked_in_idle(self, state_machine):
        allowed, msg = state_machine.can_execute_tool("disk_cleanup", True)
        assert allowed is False
        assert "GO REPAIR" in msg

    def test_repair_blocked_in_audit(self, state_machine):
        state_machine.transition_to(WorkflowState.AUDIT)
        allowed, msg = state_machine.can_execute_tool("disk_cleanup", True)
        assert allowed is False

    def test_repair_blocked_in_plan_ready(self, state_machine):
        state_machine.transition_to(WorkflowState.AUDIT)
        state_machine.transition_to_plan_ready("Plan")
        allowed, msg = state_machine.can_execute_tool("disk_cleanup", True)
        assert allowed is False

    def test_repair_allowed_in_locked(self, state_machine):
        state_machine.transition_to(WorkflowState.AUDIT)
        state_machine.transition_to_plan_ready("Plan")
        state_machine.lock_execution([1, 2])
        allowed, _ = state_machine.can_execute_tool("disk_cleanup", True)
        assert allowed is True

    def test_repair_allowed_in_executing(self, state_machine):
        state_machine.transition_to(WorkflowState.AUDIT)
        state_machine.transition_to_plan_ready("Plan")
        state_machine.lock_execution([1])
        state_machine.mark_step_executed(1)
        assert state_machine.current_state == WorkflowState.EXECUTING
        allowed, _ = state_machine.can_execute_tool("disk_cleanup", True)
        assert allowed is True

    def test_repair_blocked_in_completed(self, state_machine):
        state_machine.transition_to(WorkflowState.COMPLETED)
        allowed, _ = state_machine.can_execute_tool("disk_cleanup", True)
        assert allowed is False


class TestPlanAndLock:
    """Tests für Plan-Ready und Execution Lock"""

    def test_transition_to_plan_ready(self, state_machine):
        plan = "1. DNS flush\n2. Reboot"
        state_machine.transition_to_plan_ready(plan)
        assert state_machine.current_state == WorkflowState.PLAN_READY
        assert state_machine.repair_plan == plan

    def test_lock_execution(self, state_machine):
        state_machine.transition_to_plan_ready("Plan")
        state_machine.lock_execution([1, 2, 3])
        assert state_machine.current_state == WorkflowState.LOCKED
        assert state_machine.approved_steps == [1, 2, 3]

    def test_lock_fails_from_wrong_state(self, state_machine):
        with pytest.raises(ValueError, match="PLAN_READY"):
            state_machine.lock_execution([1])

    def test_is_step_approved(self, state_machine):
        state_machine.transition_to_plan_ready("Plan")
        state_machine.lock_execution([1, 3, 5])
        assert state_machine.is_step_approved(1) is True
        assert state_machine.is_step_approved(2) is False
        assert state_machine.is_step_approved(3) is True

    def test_mark_step_executed(self, state_machine):
        state_machine.transition_to_plan_ready("Plan")
        state_machine.lock_execution([1, 2])
        state_machine.mark_step_executed(1)
        assert 1 in state_machine.executed_steps
        assert state_machine.current_state == WorkflowState.EXECUTING

    def test_duplicate_step_execution(self, state_machine):
        state_machine.transition_to_plan_ready("Plan")
        state_machine.lock_execution([1])
        state_machine.mark_step_executed(1)
        state_machine.mark_step_executed(1)
        assert state_machine.executed_steps.count(1) == 1


class TestReset:
    """Tests für State Machine Reset"""

    def test_reset_returns_to_idle(self, state_machine):
        state_machine.transition_to(WorkflowState.AUDIT)
        state_machine.transition_to_plan_ready("Plan")
        state_machine.reset()
        assert state_machine.current_state == WorkflowState.IDLE
        assert state_machine.repair_plan is None
        assert state_machine.approved_steps == []
        assert state_machine.executed_steps == []


class TestGetStatus:
    """Tests für Status-Ausgabe"""

    def test_status_format(self, state_machine):
        status = state_machine.get_status()
        assert "state" in status
        assert "has_plan" in status
        assert "approved_steps" in status
        assert "executed_steps" in status
        assert status["state"] == "idle"
        assert status["has_plan"] is False

    def test_status_with_plan(self, state_machine):
        state_machine.transition_to_plan_ready("Plan")
        status = state_machine.get_status()
        assert status["has_plan"] is True
        assert status["state"] == "plan_ready"
