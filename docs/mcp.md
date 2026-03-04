# MCP

Config precedence:
1. managed
2. user `~/.villani.json`
3. project `.mcp.json`
4. local override `~/.villani.local.json`

Environment expansion supports `${VAR}` and `${VAR:-default}`.
