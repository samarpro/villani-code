import json
from pathlib import Path

from typer.testing import CliRunner

from villani_code.cli import app
from villani_code.eval_harness import result_to_json, run_eval_suite


def test_eval_command_runs_fixture_suite() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["eval", "--suite", "tests/fixtures/eval/suite.json"])
    assert result.exit_code == 0
    assert "Suite:" in result.output


def test_eval_json_output_schema() -> None:
    suite = run_eval_suite(Path("tests/fixtures/eval/suite.json"))
    payload = result_to_json(suite)
    assert "aggregate" in payload
    assert "tasks" in payload
    assert "tasks_total" in payload["aggregate"]


def test_metric_aggregation_and_touch_set_accounting() -> None:
    suite = run_eval_suite(Path("tests/fixtures/eval/suite.json"))
    payload = result_to_json(suite)
    assert payload["aggregate"]["tasks_total"] == 3
    failed = [t for t in payload["tasks"] if t["success"] is False][0]
    assert failed["unnecessary_files_touched"] == ["README.md"]
    assert payload["aggregate"]["catastrophic_failures"] == 1
