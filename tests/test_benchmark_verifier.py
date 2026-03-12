from __future__ import annotations

import sys
from pathlib import Path

from villani_code.benchmark.verifier import _normalize_verification_command, run_commands


def test_normalize_pytest_command_uses_active_interpreter() -> None:
    normalized, _display, shell = _normalize_verification_command("pytest -q tests/test_x.py")
    assert normalized == [sys.executable, "-m", "pytest", "-q", "tests/test_x.py"]
    assert shell is False


def test_normalize_bare_pytest_command() -> None:
    normalized, _display, shell = _normalize_verification_command("pytest")
    assert normalized == [sys.executable, "-m", "pytest"]
    assert shell is False


def test_normalize_leaves_python_m_pytest_unchanged() -> None:
    normalized, _display, shell = _normalize_verification_command("python -m pytest -q")
    assert normalized == "python -m pytest -q"
    assert shell is True


def test_normalize_leaves_non_pytest_commands_unchanged() -> None:
    normalized, _display, shell = _normalize_verification_command("echo hello")
    assert normalized == "echo hello"
    assert shell is True


def test_run_commands_logs_original_and_normalized(monkeypatch, tmp_path: Path) -> None:
    logs: list[str] = []

    class Proc:
        returncode = 0
        stdout = "ok"
        stderr = ""

    monkeypatch.setattr("villani_code.benchmark.verifier.subprocess.run", lambda *args, **kwargs: Proc())
    passed, _outcomes, _first, _last, launch_failed = run_commands(
        tmp_path,
        ["pytest -q tests/test_x.py"],
        timeout_seconds=3,
        stage="visible",
        logger=logs.append,
    )

    assert passed is True
    assert launch_failed is False
    assert any("visible verify cmd=pytest -q tests/test_x.py" in msg for msg in logs)
    assert any("visible verify normalized=" in msg and "-m pytest -q tests/test_x.py" in msg for msg in logs)


def test_run_commands_launch_error_marks_launch_failed(monkeypatch, tmp_path: Path) -> None:
    def _boom(*args, **kwargs):
        raise OSError("No such file or directory")

    monkeypatch.setattr("villani_code.benchmark.verifier.subprocess.run", _boom)
    passed, outcomes, _first, _last, launch_failed = run_commands(tmp_path, ["pytest -q"], timeout_seconds=3)
    assert passed is False
    assert launch_failed is True
    assert outcomes[0].passed is False
    assert "launch-error" in outcomes[0].stderr


def test_run_commands_test_failure_not_launch_failure(monkeypatch, tmp_path: Path) -> None:
    class Proc:
        returncode = 1
        stdout = ""
        stderr = "assertion failed"

    monkeypatch.setattr("villani_code.benchmark.verifier.subprocess.run", lambda *args, **kwargs: Proc())
    passed, _outcomes, _first, _last, launch_failed = run_commands(tmp_path, ["pytest -q"], timeout_seconds=3)
    assert passed is False
    assert launch_failed is False
