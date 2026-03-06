# Villani Code

Villani Code is a **disciplined coding agent for constrained inference**.

It is designed to make weaker/slower/quantized/local models more reliable by enforcing:
- explicit planning
- compact repo memory
- visible context governance
- scoped validation
- bounded repair

## What Villani is

Villani is a terminal-first coding agent that runs against local or remote OpenAI-compatible endpoints and keeps its control decisions explicit.

## What Villani is optimized for

- Fix one failing test.
- Fix lint/type errors.
- Make a narrow refactor.
- Update docs safely with scoped checks.
- Inspect a repo and produce a safe execution plan without edits.

## What constrained inference means here

Constrained inference = small context budgets, weaker model reasoning, and slower responses.

Villani addresses this with:
- compact `.villani/` memory files
- deterministic context compaction
- context pressure estimation (low/moderate/high/overflow)
- stale-context detection and checkpoint/reset handoff

## Core workflow

1. Initialize repo memory (`villani-code init`).
2. Classify task mode and generate explicit plan.
3. Build visible active context inventory.
4. Prune/compact context under budget pressure.
5. Execute minimal edits.
6. Run mode-appropriate validation (targeted first).
7. Attempt bounded repair when needed.
8. Emit outcome summary with touched files, validation breadth, and scope adherence.

## `.villani/` memory files

- `.villani/repo_map.json`
- `.villani/validation.json`
- `.villani/project_rules.md`
- `.villani/session_state.json`
- `.villani/context_state.json` (active/excluded context, pressure, pruning, compaction)
- `.villani/session_checkpoints/*.json` (compact checkpoint handoff)

## Context governance

Use:
- `villani-code context [--json]`
- `villani-code checkpoint "summary"`
- `villani-code reset-from-checkpoint <checkpoint_id>`

Context output includes:
- active context sources
- excluded candidates and reasons
- pressure estimate and level
- compaction outcomes
- stale-context signals

## Validation and bounded repair

Validation defaults are task-mode aware:
- failing test fixes prioritize targeted tests
- lint/type fixes prioritize static checks
- docs updates skip code-heavy validation
- inspect-and-plan mode uses inspection-only validation

Repair loops are bounded by `--max-repair-attempts`.

## Eval harness

Run:
- `villani-code eval`
- `villani-code eval --json`

Reports include:
- task success/failure
- validation success/failure
- files touched
- unnecessary files touched
- context size estimate
- context pruning events
- repair attempts used
- catastrophic failure flag
- risk classification
- validation breadth used
- elapsed time
- outcome status

## Safety / high-risk behavior

Villani favors narrow touch sets and early stop conditions when:
- risk grows beyond expected task bounds
- scope drifts beyond requested mode
- validation breadth escalates unexpectedly
- repeated repair attempts fail

## CLI examples

Inspect repo and produce plan:
```bash
villani-code run "inspect repo and produce safe execution plan with no edits" --base-url http://localhost:8000 --model local-model
```

Fix failing test with scoped validation:
```bash
villani-code run "fix failing test in tests/test_parser.py" --base-url http://localhost:8000 --model local-model
```

Inspect active context:
```bash
villani-code context --json
```

Run eval suite:
```bash
villani-code eval --suite tests/fixtures/eval/suite.json --json
```

Create checkpoint and reset:
```bash
villani-code checkpoint "after targeted test fix"
villani-code reset-from-checkpoint 20260101T000000Z
```
