from pathlib import Path
from app.health import status

def test_status_reads_marker_from_repo_root(tmp_path):
    marker = tmp_path / 'enabled.txt'
    marker.write_text('1', encoding='utf-8')
    assert status(marker) == 'ok'
