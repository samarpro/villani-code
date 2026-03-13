from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("textual")

from textual.widgets import Input

from villani_code.permissions import Decision
from villani_code.plan_session import PlanAnswer, PlanOption, PlanQuestion, PlanSessionResult
from villani_code.state import Runner
from villani_code.state_tooling import execute_tool_with_policy
from villani_code.tui.app import VillaniTUI


class DummyClient:
    pass


class DummyRunnerForApp:
    model = "demo"
    permissions = None


class ControllerSpy:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def run_prompt(self, text: str) -> None:
        self.calls.append(f"run:{text}")

    def run_plan_prompt(self, text: str) -> None:
        self.calls.append(f"plan:{text}")

    def run_execute_plan(self) -> None:
        self.calls.append("execute")

    def replan(self) -> None:
        self.calls.append("replan")

    def submit_plan_answer(self, answer: PlanAnswer) -> None:
        self.calls.append(answer.question_id)

    def resolve_approval(self, request_id: str, choice: str) -> None:
        return None


class MinimalRunner:
    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self.model = "demo"
        self.permissions = type("Perm", (), {"evaluate_with_reason": lambda self, *_a, **_k: type("P", (), {"decision": Decision.ALLOW, "reason": ""})()})()
        self.hooks = type("Hooks", (), {"run_event": lambda self, *_a, **_k: type("R", (), {"allow": True, "reason": ""})()})()
        self.small_model = False
        self.villani_mode = False
        self.benchmark_config = type("B", (), {"enabled": False})()
        self._planning_read_only = True
        self.bypass_permissions = True
        self.auto_accept_edits = True
        self.unsafe = False
        self.checkpoints = type("C", (), {"create": lambda self, *_a, **_k: None})()
        self._intended_targets = set()
        self._current_verification_targets = set()
        self._current_verification_before_contents = {}
        self._before_contents = {}
        self.event_callback = lambda _e: None
        self._small_model_tool_guard = lambda *_a, **_k: None
        self._tighten_tool_input = lambda *_a, **_k: None
        self._emit_policy_event = lambda *_a, **_k: None



def test_plan_question_enforces_four_options_and_single_other() -> None:
    options = [
        PlanOption("a", "A", "one"),
        PlanOption("b", "B", "two"),
        PlanOption("c", "C", "three"),
        PlanOption("o", "Other", "custom", is_other=True),
    ]
    q = PlanQuestion(id="q1", question="Pick", rationale="Need choice", options=options)
    assert len(q.options) == 4
    assert sum(1 for o in q.options if o.is_other) == 1


def test_runner_plan_returns_plan_session_result(tmp_path: Path) -> None:
    runner = Runner(DummyClient(), tmp_path, model="demo")
    result = runner.plan("implement plan workflow")
    assert isinstance(result, PlanSessionResult)
    for question in result.open_questions:
        assert len(question.options) == 4
        assert sum(1 for option in question.options if option.is_other and option.label == "Other") == 1


def test_plan_mode_routes_prompt_to_plan_controller(tmp_path: Path) -> None:
    app = VillaniTUI(DummyRunnerForApp(), tmp_path)
    app.controller = ControllerSpy()
    app.plan_mode_enabled = True
    app.plan_session_active = True
    app.on_input_submitted(Input.Submitted(Input(id="input"), "do work"))
    assert app.controller.calls == ["plan:do work"]


def test_run_with_plan_uses_approved_plan_payload(tmp_path: Path) -> None:
    runner = Runner(DummyClient(), tmp_path, model="demo")
    seen: dict[str, str] = {}

    def fake_run(instruction: str, messages=None, execution_budget=None):
        seen["instruction"] = instruction
        return {"response": {"content": []}}

    runner.run = fake_run  # type: ignore[assignment]
    plan = PlanSessionResult(
        instruction="orig",
        task_summary="summary",
        assumptions=["assume"],
        recommended_steps=["step1"],
        resolved_answers=[PlanAnswer("q", "opt", "custom")],
        ready_to_execute=True,
        execution_brief="brief",
    )
    runner.run_with_plan(plan)
    assert "Original instruction: orig" in seen["instruction"]
    assert "Resolved clarifications:" in seen["instruction"]


def test_run_with_plan_fails_if_unresolved(tmp_path: Path) -> None:
    runner = Runner(DummyClient(), tmp_path, model="demo")
    plan = PlanSessionResult(instruction="orig", task_summary="summary", ready_to_execute=False)
    with pytest.raises(RuntimeError):
        runner.run_with_plan(plan)


def test_planning_read_only_blocks_write_tool(tmp_path: Path) -> None:
    runner = MinimalRunner(tmp_path)
    blocked = execute_tool_with_policy(runner, "Write", {"file_path": "a.txt", "content": "x"}, "1", 0)
    assert blocked["is_error"] is True
    assert "read-only" in blocked["content"].lower()
