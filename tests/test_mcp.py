import json
from pathlib import Path

from villani_code.mcp import load_mcp_config


def test_mcp_precedence_and_env_expansion(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("API_TOKEN", "abc")
    managed = tmp_path / "managed.json"
    managed.write_text(json.dumps({"servers": {"x": {"url": "managed"}}}), encoding="utf-8")
    (tmp_path / ".mcp.json").write_text(json.dumps({"servers": {"x": {"url": "${API_TOKEN:-none}"}, "y": {"url": "proj"}}}), encoding="utf-8")

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    (home / ".villani.json").write_text(json.dumps({"servers": {"x": {"url": "user"}}}), encoding="utf-8")
    (home / ".villani.local.json").write_text(json.dumps({"servers": {"y": {"url": "local"}}}), encoding="utf-8")

    cfg = load_mcp_config(tmp_path, managed_path=managed)
    assert cfg["servers"]["x"]["url"] == "abc"
    assert cfg["servers"]["y"]["url"] == "local"
