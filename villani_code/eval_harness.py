from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EvalTask:
    name: str
    mode: str
    expected_touch_set: list[str] = field(default_factory=list)
    touched_files: list[str] = field(default_factory=list)
    success: bool = False
    validation_success: bool = False
    context_size_estimate: int = 0
    pruning_events: int = 0
    repair_attempts_used: int = 0
    catastrophic_failure: bool = False
    risk_classification: str = "low"
    validation_breadth: str = "targeted"
    elapsed_seconds: float = 0.0
    outcome_status: str = "unknown"

    @property
    def unnecessary_files_touched(self) -> list[str]:
        if not self.expected_touch_set:
            return []
        expected = set(self.expected_touch_set)
        return sorted([f for f in self.touched_files if f not in expected])


@dataclass(slots=True)
class EvalSuiteResult:
    suite_name: str
    tasks: list[EvalTask]

    def aggregate(self) -> dict[str, Any]:
        successes = [t for t in self.tasks if t.success]
        catastrophic = [t for t in self.tasks if t.catastrophic_failure]
        return {
            "suite_name": self.suite_name,
            "tasks_total": len(self.tasks),
            "tasks_success": len(successes),
            "tasks_failed": len(self.tasks) - len(successes),
            "catastrophic_failures": len(catastrophic),
            "avg_elapsed_seconds": round(sum(t.elapsed_seconds for t in self.tasks) / max(len(self.tasks), 1), 3),
            "avg_context_size_estimate": int(sum(t.context_size_estimate for t in self.tasks) / max(len(self.tasks), 1)),
            "total_pruning_events": sum(t.pruning_events for t in self.tasks),
            "total_repair_attempts": sum(t.repair_attempts_used for t in self.tasks),
        }


def _load_suite(path: Path) -> tuple[str, list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return str(payload.get("suite_name", path.stem)), list(payload.get("tasks", []))


def run_eval_suite(suite_file: Path) -> EvalSuiteResult:
    suite_name, task_rows = _load_suite(suite_file)
    tasks: list[EvalTask] = []

    for row in task_rows:
        started = time.monotonic()
        expected = [str(v) for v in row.get("expected_touch_set", [])]
        touched = [str(v) for v in row.get("simulated_touched_files", expected)]
        status = str(row.get("simulated_outcome_status", "success"))
        task = EvalTask(
            name=str(row.get("name", "task")),
            mode=str(row.get("mode", "general")),
            expected_touch_set=expected,
            touched_files=touched,
            success=bool(row.get("simulated_success", True)),
            validation_success=bool(row.get("simulated_validation_success", True)),
            context_size_estimate=int(row.get("simulated_context_size_estimate", 0)),
            pruning_events=int(row.get("simulated_pruning_events", 0)),
            repair_attempts_used=int(row.get("simulated_repair_attempts_used", 0)),
            catastrophic_failure=bool(row.get("simulated_catastrophic_failure", False)),
            risk_classification=str(row.get("simulated_risk_classification", "low")),
            validation_breadth=str(row.get("simulated_validation_breadth", "targeted")),
            outcome_status=status,
        )
        task.elapsed_seconds = round(time.monotonic() - started, 4)
        tasks.append(task)
    return EvalSuiteResult(suite_name=suite_name, tasks=tasks)


def result_to_json(result: EvalSuiteResult) -> dict[str, Any]:
    return {
        "aggregate": result.aggregate(),
        "tasks": [
            {
                **asdict(task),
                "unnecessary_files_touched": task.unnecessary_files_touched,
            }
            for task in result.tasks
        ],
    }


def render_human_summary(result: EvalSuiteResult) -> str:
    aggregate = result.aggregate()
    lines = [
        f"Suite: {aggregate['suite_name']}",
        f"Success: {aggregate['tasks_success']}/{aggregate['tasks_total']}",
        f"Catastrophic failures: {aggregate['catastrophic_failures']}",
        f"Average context size estimate: {aggregate['avg_context_size_estimate']}",
        "Per-task:",
    ]
    for task in result.tasks:
        lines.append(
            f"- {task.name}: success={task.success} validation={task.validation_success} touched={len(task.touched_files)} unnecessary={len(task.unnecessary_files_touched)} risk={task.risk_classification} status={task.outcome_status}"
        )
    return "\n".join(lines)
