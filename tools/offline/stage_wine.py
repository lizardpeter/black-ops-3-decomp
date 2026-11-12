#!/usr/bin/env python3
"""Stage one isolated, byte-identical BO3 Wine startup diagnostic.

Requires an ALREADY INITIALIZED PRIVATE Wine prefix; never modifies a real
Windows installation or a game installation. In that Wine prefix only, installs
the GDK no-vendor shim in system32. The exe itself remains byte-identical.
XCurl shim is app-local in a new diagnostic output folder. Not a playable client.

  python3 tools/offline/stage_wine.py --original .work/originals/BlackOps3_MSStore.exe \
    --gdk build/BlackOps3_MSStore/gdk-stub/xgameruntime.dll \
    --xcurl build/BlackOps3_MSStore/offline-shims/xcurl.dll \
    --prefix .work/t7-private-wine --output .work/t7-offline-stage
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()

def validate_prefix(prefix):
    if platform.system() != "Linux" or os.name != "posix":
        raise ValueError("Wine-prefix staging is only supported on Linux; never Windows")
    prefix = prefix.absolute()
    if not prefix.is_dir() or prefix.is_symlink():
        raise ValueError("must supply an initialized private, non-symlink Wine prefix")
    # Prevent a symlink at any intermediate directory from redirecting system32.
    for name in ("drive_c", "drive_c/windows", "drive_c/windows/system32"):
        child = prefix / name
        if child.is_symlink() or not child.is_dir():
            raise ValueError("refusing missing/symlinked Wine system directory: " + name)
    if not (prefix / "system.reg").is_file() or not (prefix / "user.reg").is_file():
        raise ValueError("Wine prefix lacks registry files; run wineboot first")
    return prefix / "drive_c/windows/system32"

def stage(original, gdk, xcurl, prefix, output):
    import pefile
    system32 = validate_prefix(prefix)
    # Reject any original other than the exact pinned offline Store target.
    cfg = tomllib.loads((ROOT / "target.toml").read_text())
    pin = next(b["exe"]["sha256"] for b in cfg["build"] if b["id"] == "BlackOps3_MSStore")
    if digest(original) != pin:
        raise ValueError("original exe is not the pinned BO3 Store build")
    import sys
    sys.path.insert(0, str(ROOT / "tests/direct"))
    from gdk_stub import audit as audit_gdk
    from vendor_stubs import audit as audit_xcurl
    audit_gdk(gdk)
    audit_xcurl(xcurl)
    if output.exists() or output.is_symlink():
        raise FileExistsError("output already exists")
    installed = system32 / "xgameruntime.dll"
    # Never replace a preexisting Wine runtime with unknown ownership.
    if installed.exists() and digest(installed) != digest(gdk):
        raise FileExistsError("different xgameruntime.dll already exists in this Wine prefix")
    output.mkdir(parents=True)
    installed_by_stage = False
    try:
        game = output / "BlackOps3.exe"
        local_xcurl = output / "xcurl.dll"
        shutil.copyfile(original, game)
        shutil.copyfile(xcurl, local_xcurl)
        if not installed.exists():
            shutil.copyfile(gdk, installed)
            installed_by_stage = True
        assert digest(game) == pin and digest(installed) == digest(gdk)
        manifest = {
            "format": 1, "mode": "isolated-wine-diagnostic",
            "build": "BlackOps3_MSStore", "original_exe_untouched": True,
            "exe_sha256": pin, "xcurl_sha256": digest(xcurl),
            "prefix_gdk_sha256": digest(gdk),
            "native_windows_verified": False, "menu_verified": False,
            "map_verified": False, "join_verified": False,
            "full_vendor_isolation_verified": False,
            "warning": "Only private Wine prefixes; no installation on native Windows."
        }
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print("Staged byte-identical BO3 diagnostic at", output)
        print("Run wine_run.py with --exe", game, "--prefix", prefix, "and real --game assets.")
        return manifest
    except BaseException:
        shutil.rmtree(output)
        if installed_by_stage and installed.exists() and digest(installed) == digest(gdk):
            installed.unlink()
        raise

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for x in ("original", "gdk", "xcurl", "prefix", "output"):
        ap.add_argument("--" + x, type=Path, required=True)
    a = ap.parse_args()
    stage(a.original, a.gdk, a.xcurl, a.prefix, a.output)
if __name__ == "__main__":
    main()
