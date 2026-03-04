from pathlib import Path

from villani_code.tui.app import VillaniTUI


class DummyRunner:
    model = "demo"
    permissions = None


def test_tui_constructs_with_runner(tmp_path: Path) -> None:
    app = VillaniTUI(DummyRunner(), tmp_path)
    assert app.runner.model == "demo"


def test_tui_uses_textual_css_file(tmp_path: Path) -> None:
    app = VillaniTUI(DummyRunner(), tmp_path)
    assert app.CSS_PATH == "styles.tcss"


def test_tui_has_priority_bindings_for_inline_approval(tmp_path: Path) -> None:
    app = VillaniTUI(DummyRunner(), tmp_path)
    keys = {binding.key for binding in app.BINDINGS}
    assert {"left", "right", "up", "down", "tab", "enter", "escape"}.issubset(keys)
