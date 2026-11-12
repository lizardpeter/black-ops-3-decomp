#!/usr/bin/env python3
"""Run the direct/local runtime's native standalone tests without original game assets."""
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[2]
for script in ("profile.py", "startup.py", "startup_trace.py", "transport.py"):
    subprocess.run([sys.executable, str(root / "tests" / "direct" / script)], cwd=root, check=True)
print("PASS: standalone T7 identity and UDP transport suite")
