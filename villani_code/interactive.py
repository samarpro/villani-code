from __future__ import annotations

from pathlib import Path
from typing import Any


class OptionalTUIDependencyError(RuntimeError):
    """Raised when interactive mode is requested without the optional TUI extra."""


def _load_tui_assets() -> str:
    try:
        from villani_code.tui.assets import LAUNCH_BANNER
    except ModuleNotFoundError as exc:
        if exc.name == "textual":
            raise OptionalTUIDependencyError(
                "Interactive mode requires the optional TUI dependencies. "
                "Install with `pip install .[tui]` or `pip install villani-code[tui]`."
            ) from exc
        raise
    return LAUNCH_BANNER


def _load_tui_app() -> type[Any]:
    try:
        from villani_code.tui.app import VillaniTUI
    except ModuleNotFoundError as exc:
        if exc.name == "textual":
            raise OptionalTUIDependencyError(
                "Interactive mode requires the optional TUI dependencies. "
                "Install with `pip install .[tui]` or `pip install villani-code[tui]`."
            ) from exc
        raise
    return VillaniTUI


class InteractiveShell:
    LAUNCH_BANNER = "villani-fying your terminal..."

    def __init__(self, runner: Any, repo: Path, villani_mode: bool = False, villani_objective: str | None = None):
        self.runner = runner
        self.repo = repo
        self.villani_mode = villani_mode
        self.villani_objective = villani_objective
        self.LAUNCH_BANNER = _load_tui_assets()

    def run(self) -> None:
        tui_app = _load_tui_app()
        tui_app(
            self.runner,
            self.repo,
            villani_mode=self.villani_mode,
            villani_objective=self.villani_objective,
        ).run()
