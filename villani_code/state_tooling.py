from __future__ import annotations

from pathlib import Path
from typing import Any

from villani_code.permissions import Decision
from villani_code.repo_rules import classify_repo_path, is_ignored_repo_path
from villani_code.tools import execute_tool


def execute_tool_with_policy(
    runner: Any,
    tool_name: str,
    tool_input: dict[str, Any],
    tool_use_id: str,
    message_count: int,
) -> dict[str, Any]:
    hook_pre = runner.hooks.run_event(
        "PreToolUse",
        {"event": "PreToolUse", "tool": tool_name, "input": tool_input},
    )
    if not hook_pre.allow:
        return {"content": f"Blocked by hook: {hook_pre.reason}", "is_error": True}

    if runner.small_model:
        policy_error = runner._small_model_tool_guard(tool_name, tool_input)
        if policy_error:
            return {"content": policy_error, "is_error": True}
        runner._tighten_tool_input(tool_name, tool_input)

    policy = runner.permissions.evaluate_with_reason(
        tool_name,
        tool_input,
        bypass=runner.bypass_permissions,
        auto_accept_edits=runner.auto_accept_edits,
    )
    runner._emit_policy_event(tool_name, tool_input, policy.decision, policy.reason)
    if policy.decision == Decision.DENY:
        return {"content": "Denied by permission policy", "is_error": True}
    if policy.decision == Decision.ASK:
        if runner.villani_mode:
            runner.event_callback(
                {
                    "type": "approval_auto_resolved",
                    "name": tool_name,
                    "input": tool_input,
                }
            )
        else:
            runner.event_callback(
                {
                    "type": "approval_required",
                    "name": tool_name,
                    "input": tool_input,
                }
            )
            if not runner.approval_callback(tool_name, tool_input):
                return {"content": "User denied tool execution", "is_error": True}
    elif runner.plan_mode != "off" and tool_name in {"Write", "Patch"}:
        return {"content": "Plan mode: edit not executed", "is_error": False}

    if runner.villani_mode and tool_name in {"Write", "Patch"}:
        target = str(tool_input.get("file_path", ""))
        if target:
            classification = classify_repo_path(target)
            if is_ignored_repo_path(target) or classification in {
                "runtime_artifact",
                "editor_artifact",
                "vcs_internal",
            }:
                msg = f"Skipped low-authority path: {target} ({classification})"
                runner.event_callback({"type": "autonomous_phase", "phase": msg})
                return {"content": msg, "is_error": True}

    if tool_name in {"Write", "Patch"}:
        target = str(tool_input.get("file_path", ""))
        if target:
            normalized_target = target.replace("\\", "/").lstrip("./")
            runner._intended_targets.add(normalized_target)
            runner._current_verification_targets = {normalized_target}
            runner._current_verification_before_contents = {}
            target_path = (runner.repo / normalized_target).resolve()
            if target_path.exists() and target_path.is_file():
                before_text = target_path.read_text(encoding="utf-8", errors="replace")
                runner._before_contents[normalized_target] = before_text
                runner._current_verification_before_contents[normalized_target] = before_text
        runner.checkpoints.create(
            [Path(tool_input.get("file_path", ""))],
            message_index=message_count,
        )
    runner.event_callback(
        {
            "type": "tool_started",
            "name": tool_name,
            "input": tool_input,
            "tool_use_id": tool_use_id,
        }
    )
    return execute_tool(tool_name, tool_input, runner.repo, unsafe=runner.unsafe)
