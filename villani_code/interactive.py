from __future__ import annotations

import subprocess
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console

from villani_code.state import Runner


class InteractiveShell:
    def __init__(self, runner: Runner, repo: Path):
        self.runner = runner
        self.repo = repo
        self.console = Console()
        self.verbose_tools = False
        self.show_tasks = False
        self.jobs: dict[int, subprocess.Popen] = {}

    def run(self) -> None:
        kb = KeyBindings()

        @kb.add("c-o")
        def _toggle_verbose(_):
            self.verbose_tools = not self.verbose_tools
            self.console.print(f"[dim]Verbose tool output: {self.verbose_tools}[/dim]")

        @kb.add("c-t")
        def _toggle_tasks(_):
            self.show_tasks = not self.show_tasks
            self.console.print(f"[dim]Task panel: {self.show_tasks}[/dim]")

        session = PromptSession("villani> ", key_bindings=kb)
        while True:
            try:
                text = session.prompt()
            except EOFError:
                return
            except KeyboardInterrupt:
                self.console.print("[yellow]Cancelled[/yellow]")
                continue
            if not text.strip():
                continue
            if text.strip().startswith("!"):
                self._run_bash_line(text[1:])
                continue
            if text.strip().startswith("/"):
                if self._handle_slash(text.strip()):
                    continue
            result = self.runner.run(text)
            for block in result["response"].get("content", []):
                if block.get("type") == "text":
                    self.console.print(block.get("text", ""))

    def _run_bash_line(self, command: str) -> None:
        proc = subprocess.Popen(command, shell=True, cwd=str(self.repo), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.jobs[proc.pid] = proc
        out, _ = proc.communicate()
        self.console.print(out)
        self.jobs.pop(proc.pid, None)

    def _handle_slash(self, line: str) -> bool:
        if line == "/":
            self.console.print("/help /jobs /kill <pid> /diff /rewind /export [name] /fork [name] /mcp /hooks /exit")
            return True
        if line == "/exit":
            raise EOFError
        if line == "/diff":
            proc = subprocess.run(["git", "diff"], cwd=str(self.repo), capture_output=True, text=True)
            self.console.print(proc.stdout or "No diff")
            return True
        if line.startswith("/rewind"):
            cps = self.runner.checkpoints.list()
            if not cps:
                self.console.print("No checkpoints")
                return True
            cp = cps[-1]
            self.runner.checkpoints.rewind(cp.id)
            self.console.print(f"Rewound to {cp.id}")
            return True
        if line.startswith("/export"):
            parts = line.split()
            name = parts[1] if len(parts) > 1 else "session_export"
            src = self.repo / ".villani_code" / "sessions" / "last.json"
            if src.exists():
                txt = src.read_text(encoding="utf-8")
                (self.repo / f"{name}.json").write_text(txt, encoding="utf-8")
                self.console.print(f"Exported {name}.json")
            return True
        if line.startswith("/fork"):
            parts = line.split()
            name = parts[1] if len(parts) > 1 else "fork"
            src = self.repo / ".villani_code" / "sessions" / "last.json"
            if src.exists():
                (self.repo / ".villani_code" / "sessions" / f"{name}.json").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                subprocess.run(["git", "checkout", "-b", name], cwd=str(self.repo), capture_output=True)
                self.console.print(f"Forked session as {name}")
            return True
        if line == "/jobs":
            for pid, proc in self.jobs.items():
                self.console.print(f"{pid} running={proc.poll() is None}")
            return True
        if line.startswith("/kill "):
            pid = int(line.split()[1])
            if pid in self.jobs:
                self.jobs[pid].kill()
            return True
        return False
