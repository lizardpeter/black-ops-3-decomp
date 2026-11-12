#!/usr/bin/env python3
"""Canonical enhanced BO3 *Wine diagnostic* launcher. Not a native playable build.

- Verifies the ONE enhanced package, including all binaries and their hashes.
- Uses a private existing Wine prefix, never a real Windows system directory.
- Temporarily installs its offline GDK shim into that prefix only.
- Persists a random local player ID (not an Xbox account) in the prefix.
- Runs the authentic unchanged Store EXE through the existing seccomp-isolated
  Wine smoke harness; no automatic hosting, joining or internet traffic.
- Removes only a shim it installed, even on failure. Logs remain local.

Example:
  python3 tools/enhanced/run_wine.py \
    --package build/BlackOps3_MSStore/enhanced-package \
    --game /path/to/legitimate/BO3 --prefix .work/private-t7-wine \
    --out .work/enhanced-run-1 --seconds 90 --player-name LocalPlayer
"""
import argparse
import os
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "offline"))

# Import the real offline staging library before the package verifier appends
# portable test paths containing a different stage_wine.py module.
from stage_wine import validate_prefix
from profile import load_or_create
from asset_preflight import inspect as inspect_assets
from verify import audit
from build import sha256


def run(package, game, prefix, out, seconds, name, wine, trace_files=False, local_feature_interface=False, shot_every=0, local_package_interface=False):
    if platform.system() != "Linux":
        raise RuntimeError("This GDK shim is for a private Wine prefix only, never native Windows")
    if not 10 <= seconds <= 180:
        raise ValueError("Observation duration must be 10..180 seconds")
    if shot_every not in (0, 10, 15, 30):
        raise ValueError("Screenshot cadence must be 0, 10, 15 or 30 seconds")
    package = Path(package).resolve(strict=True)
    game = Path(game).resolve(strict=True)
    prefix = Path(prefix).absolute()
    out = Path(out).absolute()
    if not game.is_dir():
        raise ValueError("The original game asset directory is missing")
    assets = inspect_assets(game)
    if not assets["fastfiles_present"]:
        print("ASSET PREFLIGHT: zone FastFiles missing/unverified; menus cannot be validated using this directory.")
    if out.exists() or out.is_symlink():
        raise FileExistsError("Diagnostic output must be a new directory")
    manifest = audit(package)
    if manifest["type"] != "local-Wine-diagnostic-with-reconstructed-enhancements":
        raise ValueError("A full canonical enhanced package is required")
    system32 = validate_prefix(prefix)
    gdk = package / "wine-system32/xgameruntime.dll"
    destination = system32 / "xgameruntime.dll"
    if destination.is_symlink():
        raise ValueError("Refusing symlinked GDK destination")
    if destination.exists() and sha256(destination) != sha256(gdk):
        raise FileExistsError("Different xgameruntime.dll already exists in the private Wine prefix")
    # A private prefix may be used by only one enhanced diagnostic at a time.
    lock = prefix / ".t7-enhanced-session.lock"
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    installed = False
    try:
        with os.fdopen(fd, "w") as lock_file:
            lock_file.write("Private offline Wine diagnostic\n")
        profile = load_or_create(prefix / "t7-enhanced-player.json", name)
        if not destination.exists():
            shutil.copyfile(gdk, destination)
            installed = True
        if sha256(destination) != sha256(gdk):
            raise IOError("Private Wine GDK shim hash changed")
        command = [
            sys.executable, str(ROOT / "tools/offline/wine_run.py"),
            "--exe", str(package / "BlackOps3.exe"),
            "--game", str(game),
            "--prefix", str(prefix),
            "--output", str(out),
            "--seconds", str(seconds),
            "--shot-every", str(shot_every),
            "--dlloverrides", "mscoree,mshtml=;xgameruntime=n;xcurl=n;winhttp=n;gamechat2=n;libscepad=n",
            "--",
            "+direct_player", profile["id"], profile["name"],
        ]
        if wine:
            command[2:2] = ["--wine", wine]
        if trace_files:
            command[2:2] = ["--trace-files"]
        environment = dict(os.environ)
        # The opt-in enables only the local COM feature-availability interface,
        # never Xbox account or licensing behavior.
        environment.pop("T7_ENHANCED_LOCAL_FEATURE", None)
        environment.pop("T7_ENHANCED_LOCAL_PACKAGE", None)
        if local_feature_interface:
            environment["T7_ENHANCED_LOCAL_FEATURE"] = "1"
        if local_package_interface:
            environment["T7_ENHANCED_LOCAL_PACKAGE"] = "1"
        completed = subprocess.run(command, cwd=ROOT, check=False, env=environment)
        if out.is_dir():
            (out / "asset_preflight.json").write_text(json.dumps(assets, indent=2) + "\n")
        if completed.returncode:
            raise RuntimeError(f"Isolated Wine smoke harness failed: exit {completed.returncode}")
        print("Diagnostic complete. Inspect local result.json and startup.json; game startup is not verified.")
        return out
    finally:
        if installed and destination.is_file() and sha256(destination) == sha256(gdk):
            destination.unlink()
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=90)
    parser.add_argument("--player-name", default=None)
    parser.add_argument("--wine")
    parser.add_argument("--trace-files", action="store_true", help="Record Wine file operations; raw log contains paths")
    parser.add_argument("--local-feature-interface", action="store_true", help="Experimental GDK feature availability COM; all feature checks return false")
    parser.add_argument("--shot-every", type=int, default=0, choices=(0, 10, 15, 30), help="Optional private screenshot capture; no images uploaded automatically")
    parser.add_argument("--local-package-interface", action="store_true", help="Experimental local package COM: no Xbox entitlement, language en-US")
    args = parser.parse_args()
    run(args.package, args.game, args.prefix, args.out, args.seconds, args.player_name, args.wine,
        args.trace_files, args.local_feature_interface, args.shot_every, args.local_package_interface)


if __name__ == "__main__":
    main()
