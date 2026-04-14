# Villani Code: Simple Explanation, Specialty, and Detailed Architecture

## 1) In simple language: how this project works

Villani Code is a coding-agent runtime (CLI + optional terminal UI) that takes a coding task, works inside a repository using tools (read files, search, run commands, edit files), and tries to land a patch that can be verified.

You can think of it like this:

1. You give an instruction.
2. It quickly scans/understands repository structure.
3. It makes a small plan.
4. It calls tools to inspect and edit.
5. It verifies changes.
6. If verification fails, it tries a bounded repair loop.
7. It returns a result with execution evidence.

The design goal is not "chat quality". The design goal is "verified repo work", especially with smaller local models.

---

## 2) What is special about this project

Most agent runtimes are built for strong hosted models with large context. Villani Code is intentionally built for constrained settings.

Its main specialty is: **small-model-first task discipline**.

That shows up in concrete runtime behavior:

- Strong scope control (avoid random file drift).
- Read-before-edit enforcement.
- Tight tool policy and permission gating.
- Targeted verification after edits.
- Repair loop when validation fails.
- Context budget + context governance to avoid prompt bloat.
- Benchmark mode with allowlists/forbidden paths and strict mutation policy.

So the specialty is not one feature, but a full control stack that helps weaker/local models stay focused and finish bounded tasks reliably.

---

## 3) High-level architecture

Villani Code is organized as layered runtime components:

1. **Entry layer (CLI/TUI)**
2. **Orchestration layer (Runner control loop)**
3. **Planning + memory layer**
4. **Tool execution + policy layer**
5. **Verification + repair layer**
6. **Autonomous Villani mode layer**
7. **Benchmark/evaluation layer**

---

## 4) Component map (what each part does)

### A. Entry layer

- `villani_code/cli.py`
  - Main Typer app.
  - Commands: `run`, `interactive`, `villani-mode`, `benchmark`, `mcp`, `plugin`, context/checkpoint commands.
  - Builds `Runner` with provider client (`OpenAIClient` or `AnthropicClient`).

- `villani_code/interactive.py`
  - Lightweight loader for optional Textual UI.

- `villani_code/tui/*`
  - Terminal UI app, status bar, approval widgets, plan-question widget.
  - `RunnerController` bridges async UI events to runner execution.

### B. Orchestration layer (core runtime loop)

- `villani_code/state.py` (`Runner`)
  - Central orchestrator.
  - Owns the turn loop: model call -> tool calls -> tool results -> next turn.
  - Maintains runtime state (targets, changed files, verification memory, retries, no-progress tracking).
  - Applies execution budgets and bounded stopping conditions.
  - Saves transcripts/session snapshots.

- `villani_code/state_runtime.py`
  - Runtime helpers used by `Runner`: planning bootstrap, message preparation, retrieval briefing, patch sanity checks, verification runs, post-execution validation/repair integration.

- `villani_code/state_tooling.py`
  - Policy-aware tool execution wrapper.
  - Enforces read-only planning mode, benchmark mutation rules, small-model scope locks, first-attempt target locks.

### C. Planning + memory layer

- `villani_code/project_memory.py`
  - Creates and maintains `.villani/` files:
    - `repo_map.json`
    - `validation.json`
    - `project_rules.md`
    - `session_state.json`
  - This is persistent repo intelligence used across runs.

- `villani_code/planning.py`
  - Classifies task mode (`fix_failing_test`, `docs_update_safe`, etc.).
  - Generates structured execution plan with scope/risk/impact reasoning.

- `villani_code/plan_session.py`
  - Structured plan schema with clarifying questions and answers.

- `villani_code/prompting.py`
  - System prompt blocks and initial messages.
  - Planning prompt and execution-from-plan prompt builders.

### D. Context + retrieval for constrained models

- `villani_code/indexing.py` + `villani_code/retrieval.py`
  - Builds local repo index and BM25 retrieval hits.
  - Used to inject focused retrieval hints for small-model runs.

- `villani_code/context_budget.py`
  - Compacts long conversation/tool outputs under char budget.

- `villani_code/context_governance.py`
  - Tracks context inventory, budget pressure, stale context signals.
  - Supports checkpointing compact context for handoff/reset.

### E. Tool execution + safety/policy layer

- `villani_code/tools.py`
  - Tool schemas and implementations:
    - `Ls`, `Read`, `Grep`, `Glob`, `Search`
    - `Bash`
    - `Write`, `Patch`
    - `WebFetch`
    - Git helpers
    - `SubmitPlan`

- `villani_code/permissions.py`
  - Permission model (`ALLOW` / `ASK` / `DENY`).
  - Rule-based target matching.
  - `BashSafe` command classification.

- `villani_code/repo_rules.py`
  - Path classification: authoritative vs runtime/editor/generated artifacts.
  - Used heavily to prevent low-value or risky edits.

- `villani_code/runtime_safety.py`
  - Prevents runtime dependency shadowing by target repo.

### F. Verification + repair layer

- `villani_code/autonomy.py` (`VerificationEngine`, `FailureClassifier`)
  - Adversarial verification result:
    - status (`pass/fail/uncertain`)
    - confidence
    - findings (regression, broad edit risk, incomplete edit, etc.)

- `villani_code/validation_loop.py`
  - Selects validation steps intelligently (targeted-first, then broader when needed).
  - Runs validation commands and summarizes structured failures.

- `villani_code/repair.py`
  - Bounded repair loop after validation failure.
  - Keeps repair scope locked to changed targets.

### G. Autonomous Villani mode layer

- `villani_code/autonomous.py` (`VillaniModeController`)
  - Multi-wave autonomous improvement loop.
  - Discovers opportunities, ranks them, executes bounded tasks, verifies each, retries when appropriate.
  - Stops using explicit stop decisions (budget exhausted, no opportunities, planner churn, etc.).

- `villani_code/autonomous_helpers.py` + `autonomous_progress.py` + `autonomous_stop.py`
  - Candidate ranking, task-contract checks, follow-up task surfacing, stop rationale.

### H. LLM provider adaptation layer

- `villani_code/openai_client.py`
  - Adapts Anthropic-style message/tool structure to OpenAI Chat Completions format.
  - Supports streaming conversion back to Anthropic-like event format.

- `villani_code/anthropic_client.py`
  - Direct `/v1/messages` compatible client (sync + streaming).

### I. Extensions layer

- `villani_code/mcp.py`: merged MCP config loading (managed/user/project/local layers with env expansion).
- `villani_code/plugins.py`: local plugin install/list/remove.
- `villani_code/skills.py`: skill discovery from `.villani/skills/**/SKILL.md`.

---

## 5) End-to-end runtime flows

### Flow A: `villani-code run "<instruction>"`

1. CLI parses args and builds `Runner`.
2. Runner ensures project memory and generates execution plan.
3. For constrained modes (small model / benchmark / villani), it may run pre-edit diagnosis and force an initial target read.
4. Runner enters main model loop:
   - send system + messages + tool specs
   - receive text/tool calls
   - execute tools through policy wrapper
   - append tool results back to messages
5. After edits, it runs verification and validation.
6. If validation fails, bounded repair loop runs.
7. Final response + transcript + execution metadata are returned.

### Flow B: planning mode (`/plan` in TUI)

1. Runner switches to read-only planning mode.
2. Model can inspect/search but cannot mutate files.
3. Model finalizes structured plan by calling `SubmitPlan`.
4. Plan may include clarifying questions (strict schema).
5. After answers, plan can be executed with `/execute`.

### Flow C: Villani autonomous mode

1. Planner discovers high-value opportunities from repo heuristics.
2. Opportunities are ranked by priority/confidence.
3. Controller executes each as bounded intervention via normal Runner.
4. Verification contract determines pass/retry/block/exhausted.
5. Follow-up opportunities are inserted when needed (tests/docs/entrypoints).
6. Loop stops on explicit stop criteria and prints structured summary.

### Flow D: Benchmark mode

1. `benchmark/task_loader.py` loads task specs (`task.yaml`, `prompt.txt`, `metadata.json`).
2. Runner executes selected adapter (`villani`, `aider`, `opencode`, `claude-code`, etc.).
3. Policy enforces benchmark mutation scope and path constraints.
4. Visible + hidden verification commands run.
5. Results are scored and stored with telemetry/fairness metadata.
6. Reports and summary tables are generated.

---

## 6) Important state/artifact directories

- `.villani/`
  - long-lived project memory and planning/validation config.

- `.villani_code/`
  - runtime artifacts: sessions, transcripts, event logs, index, proposals.

This split is intentional:
- `.villani` = stable memory/config.
- `.villani_code` = runtime operational artifacts.

---

## 7) Why this architecture helps small/local models

This architecture reduces common weak-model failure modes:

- **Drift** -> scope locks + authoritative path filters.
- **Blind editing** -> read-before-edit policy + forced initial read when diagnosis confidence is strong.
- **Context overload** -> retrieval briefing + compaction + governance budget.
- **Fragile patches** -> post-edit sanity + targeted validation + repair loop.
- **False completion** -> benchmark no-op guards and verification-driven completion logic.

In short: Villani Code is a control-loop architecture, not just a prompt wrapper.

---

## 8) One-line summary

Villani Code is a disciplined coding-agent runtime that combines planning, strict tool/policy control, verification, and repair to make smaller/local models produce reliable, verifiable repository changes.
