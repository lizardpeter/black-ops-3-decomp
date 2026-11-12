#!/usr/bin/env python3
"""No-game test of privacy-safe BO3 FastFile inventory."""
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools/enhanced"))
from asset_preflight import inspect

with tempfile.TemporaryDirectory() as scratch:
    root=Path(scratch)
    assert inspect(root)["status"] == "missing-zone-directory"
    zone=root/"zone"
    zone.mkdir()
    assert inspect(root)["status"] == "no-fastfiles-found"
    (zone/"ui_mp.ff").write_bytes(b"stub")
    english=zone/"english"
    english.mkdir()
    (english/"common.ff").write_bytes(b"fake")
    (english/"other.txt").write_text("unrelated")
    external=root/"external.ff"
    external.write_bytes(b"not a game asset")
    (zone/"linked.ff").symlink_to(external)
    status=inspect(root)
    assert status["status"] == "fastfiles-present-open-unverified"
    assert status["fastfile_count"] == 2
    assert status["ui_fastfile_basename_candidates"] == ["ui_mp.ff"]
    assert str(root) not in str(status)
    assert "fastfile_open_verified" not in status
print("PASS: BO3 FastFile asset inventory, symlink skip, private path redaction")
