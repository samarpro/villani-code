from __future__ import annotations

import json
from pathlib import Path

from villani_code.debug_mode import build_debug_config
from villani_code.state import Runner
from villani_code.trace_summary import write_summary_from_events, write_tool_calls_from_events


class _SequenceClient:
    def __init__(self, responses: list[dict]):
        self._responses = responses
        self._idx = 0

    def create_message(self, payload, stream):
        _ = payload, stream
        response = self._responses[self._idx]
        self._idx += 1
        return response


def _run_dir(debug_root: Path) -> Path:
    run_dirs = sorted(path for path in debug_root.iterdir() if path.is_dir())
    assert len(run_dirs) == 1
    return run_dirs[0]


def _read_events(run_dir: Path) -> list[dict]:
    return [json.loads(line) for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def test_real_bash_execution_emits_canonical_tool_lifecycle(tmp_path: Path) -> None:
    debug_root = tmp_path / "debug"
    client = _SequenceClient(
        [
            {
                "id": "1",
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "tool-bash-1", "name": "Bash", "input": {"command": "pwd", "cwd": "."}}],
            },
            {"id": "2", "role": "assistant", "content": [{"type": "text", "text": "done"}]},
        ]
    )
    runner = Runner(client=client, repo=tmp_path, model="m", stream=False, debug_config=build_debug_config("trace", debug_root))
    runner.run("run bash")

    events = _read_events(_run_dir(debug_root))
    started = next(event for event in events if event["event_type"] == "tool_call_started")
    terminal = next(event for event in events if event["event_type"] in {"tool_call_completed", "tool_call_failed"})
    assert started["payload"]["tool_call_id"] == terminal["payload"]["tool_call_id"] == "tool-bash-1"
    assert isinstance(started.get("turn_index"), int)
    assert isinstance(terminal.get("turn_index"), int)


def test_command_events_join_to_canonical_bash_tool_row(tmp_path: Path) -> None:
    debug_root = tmp_path / "debug"
    client = _SequenceClient(
        [
            {
                "id": "1",
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "tool-bash-2", "name": "Bash", "input": {"command": "echo hi", "cwd": "."}}],
            },
            {"id": "2", "role": "assistant", "content": [{"type": "text", "text": "done"}]},
        ]
    )
    runner = Runner(client=client, repo=tmp_path, model="m", stream=False, debug_config=build_debug_config("trace", debug_root))
    runner.run("run bash")
    run_dir = _run_dir(debug_root)

    events = _read_events(run_dir)
    command_started = next(event for event in events if event["event_type"] == "command_started")
    command_finished = next(event for event in events if event["event_type"] == "command_finished")
    assert command_started["payload"]["tool_call_id"] == command_finished["payload"]["tool_call_id"] == "tool-bash-2"

    rows = [json.loads(line) for line in write_tool_calls_from_events(run_dir).read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    row = rows[0]
    assert row["tool_call_id"] == "tool-bash-2"
    assert row["result_summary"]["kind"] == "command_result"
    assert "exit_code" in row["result_summary"]
    assert "stdout_preview" in row["result_summary"]
    assert "stderr_preview" in row["result_summary"]


def test_real_write_execution_maps_to_canonical_tool_row_with_normalized_path(tmp_path: Path) -> None:
    debug_root = tmp_path / "debug"
    client = _SequenceClient(
        [
            {
                "id": "1",
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool-write-1",
                        "name": "Write",
                        "input": {"file_path": "./nested/out.txt", "content": "hello"},
                    }
                ],
            },
            {"id": "2", "role": "assistant", "content": [{"type": "text", "text": "done"}]},
        ]
    )
    runner = Runner(client=client, repo=tmp_path, model="m", stream=False, debug_config=build_debug_config("trace", debug_root))
    runner.run("write file")
    run_dir = _run_dir(debug_root)

    events = _read_events(run_dir)
    assert any(e["event_type"] == "tool_call_started" and e["payload"]["tool_call_id"] == "tool-write-1" for e in events)
    assert any(
        e["event_type"] in {"tool_call_completed", "tool_call_failed"} and e["payload"]["tool_call_id"] == "tool-write-1"
        for e in events
    )
    file_write = next(e for e in events if e["event_type"] == "file_write")
    assert file_write["payload"]["tool_call_id"] == "tool-write-1"

    rows = [json.loads(line) for line in write_tool_calls_from_events(run_dir).read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["result_summary"]["kind"] == "file_write_result"
    assert rows[0]["result_summary"]["path"] == "nested/out.txt"


def test_runtime_turn_index_propagates_to_tool_and_command_events(tmp_path: Path) -> None:
    debug_root = tmp_path / "debug"
    client = _SequenceClient(
        [
            {
                "id": "1",
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "tool-bash-3", "name": "Bash", "input": {"command": "pwd", "cwd": "."}}],
            },
            {"id": "2", "role": "assistant", "content": [{"type": "text", "text": "done"}]},
        ]
    )
    runner = Runner(client=client, repo=tmp_path, model="m", stream=False, debug_config=build_debug_config("trace", debug_root))
    runner.run("turn index trace")

    events = _read_events(_run_dir(debug_root))
    for event_type in ("tool_call_started", "tool_call_completed", "command_started", "command_finished"):
        matching = [event for event in events if event["event_type"] == event_type]
        assert matching, f"missing {event_type}"
        assert all(isinstance(event.get("turn_index"), int) for event in matching)


def test_summary_generation_succeeds_for_normal_traced_run(tmp_path: Path) -> None:
    debug_root = tmp_path / "debug"
    client = _SequenceClient(
        [
            {
                "id": "1",
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "tool-write-2", "name": "Write", "input": {"file_path": "a.txt", "content": "x"}}],
            },
            {"id": "2", "role": "assistant", "content": [{"type": "text", "text": "done"}]},
        ]
    )
    runner = Runner(client=client, repo=tmp_path, model="m", stream=False, debug_config=build_debug_config("trace", debug_root))
    runner.run("normal traced run")
    run_dir = _run_dir(debug_root)

    tool_calls_path = write_tool_calls_from_events(run_dir)
    tool_rows = [json.loads(line) for line in tool_calls_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert tool_rows
    summary_path = write_summary_from_events(run_dir)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["total_tool_calls"] > 0
    assert summary["commands_executed"] >= 0

