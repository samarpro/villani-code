from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PlanOption:
    id: str
    label: str
    description: str
    is_other: bool = False


@dataclass(slots=True)
class PlanQuestion:
    id: str
    question: str
    rationale: str
    options: list[PlanOption]

    def __post_init__(self) -> None:
        if len(self.options) != 4:
            raise ValueError("PlanQuestion must contain exactly 4 options")
        other = [opt for opt in self.options if opt.is_other]
        if len(other) != 1:
            raise ValueError("PlanQuestion must contain exactly one Other option")
        if other[0].label != "Other":
            raise ValueError('Other option label must be exactly "Other"')


@dataclass(slots=True)
class PlanAnswer:
    question_id: str
    selected_option_id: str
    other_text: str = ""


@dataclass(slots=True)
class PlanSessionResult:
    instruction: str
    task_summary: str
    candidate_files: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    recommended_steps: list[str] = field(default_factory=list)
    open_questions: list[PlanQuestion] = field(default_factory=list)
    resolved_answers: list[PlanAnswer] = field(default_factory=list)
    ready_to_execute: bool = False
    execution_brief: str = ""
    risk_level: str = "medium"
    confidence_score: float = 0.5
