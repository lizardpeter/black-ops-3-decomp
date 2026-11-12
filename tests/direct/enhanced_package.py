#!/usr/bin/env python3
"""Portable tests for the single enhanced package contract and local identity.

These tests do not require originals, Xbox services, Wine or internet access.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/enhanced"))

from build import components_manifest, package, pinned_exe_hash
from profile import load_or_create, valid_name, validate_profile


def main():
    assert len(pinned_exe_hash()) == 64
    for name in ("", " bad", "bad ", "bad;quit", "bad\"name", "bad\nname",
                 "a" * 32, "../other", "bad\\name"):
        assert not valid_name(name), name
    for name in ("A", "LocalPlayer", "Local Player_2-3", "Z" * 31):
        assert valid_name(name), name
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        profile = root / "private/player.json"
        one = load_or_create(profile, "First Player")
        assert len(one["id"]) == 16 and int(one["id"], 16) != 0
        assert one == load_or_create(profile), "Identity was not stable"
        renamed = load_or_create(profile, "Second Player")
        assert renamed["id"] == one["id"] and renamed["name"] == "Second Player"
        assert validate_profile(json.loads(profile.read_text())) == renamed
        assert os.stat(profile).st_mode & 0o077 == 0, "Profile must not be world-readable"
        try: load_or_create(profile, "not;valid")
        except ValueError: pass
        else: raise AssertionError("Accepted command injection in profile name")
        assert load_or_create(profile) == renamed, "Invalid update changed persisted profile"
        outside = root / "outside.json"
        outside.write_text("{}")
        linked = root / "private/link.json"
        linked.symlink_to(outside)
        try: load_or_create(linked)
        except ValueError: pass
        else: raise AssertionError("Followed symlinked profile")
        assert outside.read_text() == "{}"
        bad = root / "bad.json"
        bad.write_text('{"format":1,"id":"0000000000000000","name":"Guest"}')
        try: load_or_create(bad)
        except ValueError: pass
        else: raise AssertionError("Accepted zero local ID")
        out = root / "package"
        for options in ({"original": root / "bad"}, {"components_only": True, "original": root / "bad"}):
            try: package(out, **options)
            except (ValueError, FileNotFoundError): pass
            else: raise AssertionError("Accepted incomplete enhanced package request")
            assert not out.exists()
    inventory = {"xcurl.dll": {"sha256": "f" * 64, "bytes": 4}}
    for full in (False, True):
        m = components_manifest(inventory, full=full)
        assert m["variant"] == "enhanced"
        assert m["original_executable_modified"] is False
        assert m["legacy_patched_pe_used"] is False
        assert m["compiled_features"]["enhanced_reconstruction_compiled"] == full
        assert all(value is False for value in m["verified"].values())
    print("PASS: stable private local identity, injection rejection, atomic persistence, single-package contract")


if __name__ == "__main__":
    main()
