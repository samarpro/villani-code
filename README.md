# Villani Code

Villani Code is a **disciplined, small-model-first coding agent**.

It is built for constrained inference environments (local, quantized, or weaker models) where reliability comes from explicit control loops rather than hidden magic.

## Product focus

Villani keeps coding work narrow, inspectable, and recoverable:
- explicit planning before edits
- visible context governance under tight budgets
- scoped validation and bounded repair
- transparent transcripts and task outcomes

## Installation

### Core (headless runtime + CLI)
```bash
pip install .
```

### Optional TUI
```bash
pip install .[tui]
```

### Development tooling
```bash
pip install .[dev]
```

### Everything
```bash
pip install .[all]
```

## Architecture (alpha, pragmatic)

- `villani_code.cli`: Typer CLI entry points and command wiring.
- `villani_code.state.Runner`: headless execution loop for `run` and shared runtime behaviour.
- `villani_code.state_runtime` / `villani_code.state_tooling`: message preparation, verification, and tool policy helpers.
- `villani_code.autonomous` + helpers: bounded Villani-mode autonomy loop and takeover summaries.
- `villani_code.context_governance`: context inventory, pruning, checkpointing, and resets.
- `villani_code.interactive` + `villani_code.tui.*`: optional Textual UI shell (loaded lazily).

## Core vs Optional

- **Core headless runner**: `init`, `run`, `context`, `checkpoint`, `reset-from-checkpoint`, and eval workflows.
- **Optional TUI**: `interactive` and `villani-mode` user interfaces that require the `tui` extra.
- **Autonomy / Villani mode**: bounded autonomous task waves over the same core runner primitives.
- **Evaluation + governance**: eval harness, context budget tracking, and verification loops to keep behaviour explicit.

## Typical workflow

1. Initialize repo memory (`villani-code init`).
2. Run a narrow task (`villani-code run ...`).
3. Review context pressure (`villani-code context --json`).
4. Checkpoint and reset when stale (`checkpoint` / `reset-from-checkpoint`).
5. Use interactive/TUI flows only when desired (`pip install .[tui]`).

## CLI examples

```bash
villani-code run "fix failing test in tests/test_parser.py" --base-url http://localhost:8000 --model local-model
villani-code context --json
villani-code eval --suite tests/fixtures/eval/suite.json --json
```
