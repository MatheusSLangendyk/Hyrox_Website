import sys
from pathlib import Path

# Make `backend/` importable when pytest is invoked from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
