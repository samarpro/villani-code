from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from app.health import status

here = Path.cwd()
marker = here / 'config' / 'enabled.txt'
print(status(marker))
