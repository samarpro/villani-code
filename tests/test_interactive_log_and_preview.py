from pathlib import Path

from prompt_toolkit.layout.margins import ScrollbarMargin

from villani_code.interactive import InteractiveShell


class DummyCheckpoints:
    def create(self, *_args, **_kwargs):
        return None

    def list(self):
        return []


class DummyPermissions:
    def target_for(self, tool: str, payload: dict) -> str:
        return f"{tool}:{payload.get('file_path', '<none>')}"


class DummyRunner:
    checkpoints = DummyCheckpoints()
    permissions = DummyPermissions()

    def run(self, _text):
        return {"response": {"content": [{"type": "text", "text": "ok"}]}}


def test_startup_banner_appends_ascii_art_and_model_to_log(tmp_path: Path) -> None:
    shell = InteractiveShell(DummyRunner(), tmp_path)
    shell._append_startup_banner()
    log_text = shell.log_area.buffer.text

    assert "villani-fying your terminal" in log_text
    assert "Model:" in log_text


def test_append_log_uses_incremental_buffer_update(tmp_path: Path) -> None:
    shell = InteractiveShell(DummyRunner(), tmp_path)

    shell._append_log("first")
    first_text = shell.log_area.buffer.text
    shell._append_log("second")

    assert first_text == "first"
    assert shell.log_area.buffer.text.endswith("\nsecond")
    assert "\n".join(shell.log_lines) == shell.log_area.buffer.text


def test_log_uses_clickable_scrollbar_margin(tmp_path: Path) -> None:
    shell = InteractiveShell(DummyRunner(), tmp_path)

    assert any(isinstance(margin, ScrollbarMargin) for margin in shell.log_area.window.right_margins)
