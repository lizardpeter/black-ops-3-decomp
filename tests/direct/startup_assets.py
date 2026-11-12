#!/usr/bin/env python3
"""Original BO3 startup subset provenance test; does not download any binaries."""
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools/enhanced"))
from fetch_startup import load_manifest, DEFAULT_MANIFEST

items=load_manifest(DEFAULT_MANIFEST)
assert len(items)==34, len(items)
assert sum(x[2] for x in items)==736627660
names={x[1] for x in items}
assert "zone/core_pre_gfx.ff" in names
assert "zone/core_frontend.ff" in names
assert "zone/core_ui.ff" in names
assert "zone/en_core_frontend.ff" in names
assert "localization_en.txt" in names
assert "zone/base.xpak" not in names
with tempfile.TemporaryDirectory() as root:
    bad=Path(root)/"bad.tsv"
    for name in ("bo3/DUMP/zone/../../malicious.ff", "bo3/DUMP/zone/base.xpak",
                 "wrong/place.ff"):
        bad.write_text("key\tbytes\tetag\n"+name+"\t4\t"+"0"*32+"\n")
        try: load_manifest(bad)
        except ValueError: pass
        else: raise AssertionError("Unsafe/out-of-scope R2 startup key accepted: "+name)
print("PASS: 34 pinned BO3 original startup R2 objects (~702.5 MiB), no base.xpak, no traversal")
