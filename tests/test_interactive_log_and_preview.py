from pathlib import Path

from villani_code.tui.controller import RunnerController
from villani_code.tui.messages import LogAppend, SpinnerState


class DummyRunner:
    permissions = None


class DummyApp:
    def __init__(self):
        self.messages = []

    def post_message(self, message):
        self.messages.append(message)


def test_stream_event_posts_log_append_incrementally(tmp_path: Path) -> None:
    app = DummyApp()
    controller = RunnerController(DummyRunner(), app)

    controller.on_runner_event({"type": "stream_text", "text": "hel"})
    controller.on_runner_event({"type": "stream_text", "text": "lo"})

    chunks = [m for m in app.messages if isinstance(m, LogAppend)]
    assert [(m.kind, m.text) for m in chunks] == [("stream", "hel"), ("stream", "lo")]


def test_model_started_uses_spinner_theme_label_not_literal_thinking(tmp_path: Path) -> None:
    app = DummyApp()
    controller = RunnerController(DummyRunner(), app)

    controller.on_runner_event({"type": "model_request_started"})

    state = next(m for m in app.messages if isinstance(m, SpinnerState))
    assert state.active is True
    assert state.label is None


def test_tool_started_logs_only_read_write_patch(tmp_path: Path) -> None:
    app = DummyApp()
    controller = RunnerController(DummyRunner(), app)

    controller.on_runner_event({"type": "tool_started", "name": "Read", "input": {"file_path": "a.py"}})
    controller.on_runner_event({"type": "tool_started", "name": "Write", "input": {"file_path": "b.py"}})
    controller.on_runner_event({"type": "tool_started", "name": "Patch", "input": {"file_path": "c.py"}})
    controller.on_runner_event({"type": "tool_started", "name": "Bash", "input": {"command": "echo hi"}})

    lines = [m.text for m in app.messages if isinstance(m, LogAppend)]
    assert lines == ["read  a.py", "write b.py", "patch c.py"]
    assert all("Using tool" not in line for line in lines)


def test_non_stream_fallback_has_no_assistant_prefix(tmp_path: Path) -> None:
    class NonStreamingRunner(DummyRunner):
        def run(self, _text):
            return {"response": {"content": [{"type": "text", "text": "hello"}]}}

    app = DummyApp()
    controller = RunnerController(NonStreamingRunner(), app)
    controller._run_prompt_worker("hi")

    ai = [m.text for m in app.messages if isinstance(m, LogAppend) and m.kind == "ai"]
    assert ai == ["hello"]
    assert "assistant>" not in ai[0]
