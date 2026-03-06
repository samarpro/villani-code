from __future__ import annotations

from villani_code.planning import PlanRiskLevel, analyze_instruction, classify_plan_risk


def test_high_risk_plan_still_classified_high() -> None:
    analysis = analyze_instruction(
        "delete files and rewrite history across the repo",
        repo_map={"source_roots": ["villani_code"], "repo_shape": "single_package"},
        validation_steps=["pytest"],
    )
    risk = classify_plan_risk("delete files and rewrite history across the repo", analysis)
    assert risk == PlanRiskLevel.HIGH


def test_dependency_touching_plan_detected() -> None:
    analysis = analyze_instruction(
        "update dependencies in pyproject and lockfile",
        repo_map={"manifests": ["pyproject.toml"], "lockfiles": ["poetry.lock"]},
        validation_steps=[],
    )
    assert any(a.value == "dependency_change" for a in analysis.action_classes)
