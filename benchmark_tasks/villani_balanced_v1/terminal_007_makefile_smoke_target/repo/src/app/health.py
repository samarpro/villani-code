from pathlib import Path

def status(marker: Path) -> str:
    return 'ok' if marker.exists() and marker.read_text(encoding='utf-8').strip() == '1' else 'bad'
