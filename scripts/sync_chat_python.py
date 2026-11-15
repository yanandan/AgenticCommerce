"""Copy the shared Python core into static assets, or verify it with --check."""
import argparse
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
for name in ('__init__.py', 'filtering.py', 'parser.py'):
    source = root / 'commerceos' / name
    target = root / 'sites' / 'commerceos' / 'dist' / 'python' / 'commerceos' / name
    if args.check:
        if not target.exists() or source.read_bytes() != target.read_bytes():
            raise SystemExit(f'{target.relative_to(root)} is out of date; run python scripts/sync_chat_python.py')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
print('Browser and backend Python sources match.' if args.check else 'Browser Python sources synchronized.')
