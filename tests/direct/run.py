#!/usr/bin/env python3
"""Run the direct/local runtime's native standalone tests without original game assets."""
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[2]
for script in ("profile.py", "enhanced_package.py", "engine_bridge.py", "startup.py", "startup_trace.py", "stage_wine.py", "native_probe.py", "transport.py", "wire_auth.py"):
    subprocess.run([sys.executable, str(root / "tests" / "direct" / script)], cwd=root, check=True)
print("PASS: standalone T7 identity and UDP transport suite")
