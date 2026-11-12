#!/usr/bin/env python3
"""Prefix path guards never allow a symlink to redirect a test system32."""
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/offline"))
from stage_wine import validate_prefix
with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    prefix = root / "private-prefix"
    system32 = prefix / "drive_c/windows/system32"
    system32.mkdir(parents=True)
    (prefix / "system.reg").write_text("WINE REGISTRY Version 2")
    (prefix / "user.reg").write_text("WINE REGISTRY Version 2")
    assert validate_prefix(prefix) == system32
    system32.rmdir()
    system32.symlink_to(root, target_is_directory=True)
    try: validate_prefix(prefix)
    except ValueError: pass
    else: raise AssertionError("followed symlinked system32")
    system32.unlink()
    try: validate_prefix(prefix)
    except ValueError: pass
    else: raise AssertionError("accepted missing Wine system32")
print("PASS: private Wine prefix validation; rejects missing/symlinked system directory")
