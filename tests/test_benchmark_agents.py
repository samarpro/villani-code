from __future__ import annotations

from pathlib import Path

from villani_code.benchmark.agents import AGENTS
from villani_code.benchmark.agents.aider import AiderAgentRunner
from villani_code.benchmark.agents.opencode import OpenCodeAgentRunner
from villani_code.benchmark.agents.villani import VillaniAgentRunner


def test_registry_contains_supported_agents() -> None:
    assert AGENTS == {
        "villani": VillaniAgentRunner,
        "aider": AiderAgentRunner,
        "opencode": OpenCodeAgentRunner,
    }


def test_aider_command_forwards_model_and_endpoint() -> None:
    runner = AiderAgentRunner()
    cmd = runner.build_command(Path("."), "fix bug", model="qwen-9b", base_url="http://127.0.0.1:1234", api_key="sk-test")
    assert cmd == [
        "aider",
        "--yes",
        "--model",
        "openai/qwen-9b",
        "--openai-api-base",
        "http://127.0.0.1:1234",
        "--openai-api-key",
        "sk-test",
        "--message",
        "fix bug",
    ]


def test_opencode_command_and_env_forward_model_and_endpoint() -> None:
    runner = OpenCodeAgentRunner()
    cmd = runner.build_command(Path("."), "fix bug", model="qwen-9b", base_url="http://127.0.0.1:1234", api_key="sk-test")
    env = runner.build_env(base_url="http://127.0.0.1:1234", api_key="sk-test")
    assert cmd == ["opencode", "run", "--model", "openai/qwen-9b", "--prompt", "fix bug"]
    assert env["OPENAI_API_BASE"] == "http://127.0.0.1:1234"
    assert env["OPENAI_API_KEY"] == "sk-test"


def test_villani_command_forwards_model_and_endpoint() -> None:
    runner = VillaniAgentRunner()
    cmd = runner.build_command(Path("/tmp/repo"), "fix bug", model="qwen-9b", base_url="http://127.0.0.1:1234", api_key="sk-test")
    assert "--model" in cmd
    assert "qwen-9b" in cmd
    assert "--base-url" in cmd
    assert "http://127.0.0.1:1234" in cmd
    assert "--api-key" in cmd
    assert "sk-test" in cmd
