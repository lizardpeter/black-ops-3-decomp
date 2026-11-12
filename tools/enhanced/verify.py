#!/usr/bin/env python3
"""Fail-closed audit for the single canonical BO3 enhanced package.

Checks every packaged executable and DLL against manifest SHA-256, confirms
the pinned unmodified BO3 Store binary, audits GDK/XCurl exports, and rejects
unlisted executables. A pass does NOT prove native startup or engine hooks.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "enhanced"))
sys.path.insert(0, str(ROOT / "tests" / "direct"))

from build import sha256, pinned_exe_hash, verify_reconstruction, reconstruction_metrics
from gdk_stub import audit as audit_gdk
from vendor_stubs import audit as audit_xcurl
from winhttp_stub import audit as audit_winhttp

COMPONENT_ONLY = {"wine-system32/xgameruntime.dll", "xcurl.dll", "winhttp.dll"}
FULL = COMPONENT_ONLY | {"BlackOps3.exe", "recon.dll"}
UNVERIFIED = (
    "game_engine_hooks_installed", "native_windows_startup",
    "rendered_menu", "fastfiles_loaded", "offline_match_started",
    "direct_multiplayer_join", "whole_process_network_isolation",
)


def reconstruction_metrics_from_metadata(directory):
    # build.reconstruction_metrics expects the two adjacent source tables.
    # Bundle metadata in its own subdirectory and pass a harmless DLL path
    # anchored there; only its parent is used for the source-table audit.
    return reconstruction_metrics(directory / "metadata/recon.dll")


def audit(directory):
    directory = Path(directory).resolve(strict=True)
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("Missing valid canonical manifest")
    manifest = json.loads(manifest_path.read_text())
    if (manifest.get("format"), manifest.get("project"), manifest.get("target"),
        manifest.get("variant")) != (1, "t7", "BlackOps3_MSStore", "enhanced"):
        raise ValueError("Not a canonical BO3 enhanced manifest")
    if manifest.get("original_executable_modified") is not False:
        raise ValueError("Original executable was not proven byte-identical")
    if manifest.get("legacy_patched_pe_used") is not False:
        raise ValueError("Legacy modified-PE path is forbidden")
    entries = manifest.get("components")
    if not isinstance(entries, dict) or set(entries) not in (COMPONENT_ONLY, FULL):
        raise ValueError("Incomplete/unknown enhanced package components")
    if any(manifest.get("verified", {}).get(k) is not False for k in UNVERIFIED):
        raise ValueError("Package falsely claims unverified runtime integration")
    if manifest.get("compiled_features", {}).get("enhanced_reconstruction_compiled") != (set(entries) == FULL):
        raise ValueError("Enhanced reconstruction manifest disagrees with DLL inventory")
    observed = set()
    for item in directory.rglob("*"):
        if item.is_symlink():
            raise ValueError("Symlinks are forbidden inside enhanced packages")
        if item.is_file() and item.suffix.lower() in (".dll", ".exe"):
            observed.add(item.relative_to(directory).as_posix())
    if observed != set(entries):
        raise ValueError(f"Untracked or missing runtime binary: {sorted(observed ^ set(entries))}")
    for name, properties in entries.items():
        path = directory / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Missing enhanced component {name}")
        if path.stat().st_size != properties["bytes"] or sha256(path) != properties["sha256"]:
            raise ValueError(f"Modified component {name}")
    audit_gdk(directory / "wine-system32/xgameruntime.dll")
    audit_xcurl(directory / "xcurl.dll")
    audit_winhttp(directory / "winhttp.dll")
    metadata = manifest.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("Missing reconstruction provenance inventory")
    if set(entries) == FULL:
        required = {"metadata/recon.symbols.tsv", "metadata/hybrid.tsv", "metadata/patches.tsv"}
        if set(metadata) != required:
            raise ValueError("Missing or untracked enhanced reconstruction provenance")
        for name, props in metadata.items():
            path = directory / name
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"Missing reconstruction record {name}")
            if path.stat().st_size != props["bytes"] or sha256(path) != props["sha256"]:
                raise ValueError(f"Reconstruction record changed: {name}")
        # Compare the packaged source table to the manifest's exact counts,
        # rather than accepting a relabeled faithful-only DLL as enhanced.
        reconstructed = reconstruction_metrics_from_metadata(directory)
        if manifest.get("reconstruction_metrics") != reconstructed:
            raise ValueError("Reconstruction metrics do not match bundled source records")
    else:
        if metadata or manifest.get("reconstruction_metrics") is not None:
            raise ValueError("Components-only package must not claim reconstruction evidence")
    if set(entries) == FULL:
        if sha256(directory / "BlackOps3.exe") != pinned_exe_hash():
            raise ValueError("BO3 original EXE hash mismatch")
        verify_reconstruction(directory / "recon.dll")
    print("PASS: one canonical BO3 enhanced inventory; hashes/exports verified, original unmodified")
    print("NOT VERIFIED: BO3 engine hooks, playable startup, game sessions or process-wide isolation")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    audit(parser.parse_args().directory)


if __name__ == "__main__":
    main()
