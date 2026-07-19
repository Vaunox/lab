"""Test-wide path setup.

`tools/` is a scripts directory, not an installed package, so the checkers are
imported by putting that directory on the path rather than by a console entry
point. `tools/gate.py` does the same thing for the same reason.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
