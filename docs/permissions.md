# Permissions

Rule order is strict: deny, ask, allow. First match wins.

Default deny examples:
- `Read(.env)`
- `Read(secrets/**)`
- `Bash(curl *)`
- `Bash(wget *)`

Bash matching is operator-aware and token-based.
