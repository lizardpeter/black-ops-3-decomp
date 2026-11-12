#!/usr/bin/env python3
"""Canonical BO3 enhanced package. The only supported enhanced packaging entrypoint.

Builds and audits the in-process local GDK runtime and no-network XCurl shim,
then bundles the pinned, byte-identical Store EXE and the reconstructed enhanced
recon.dll. No .text edits, import rewrites, fake Xbox users, or vendor services.

FULL (requires the user's original files; does not generate copyrighted binaries):
  python3 tools/enhanced/build.py --original .work/originals/BlackOps3_MSStore.exe \
    --recon build/BlackOps3_MSStore/enhanced/recon.dll \
    --out build/BlackOps3_MSStore/enhanced-package

COMPONENTS ONLY (CI; no original game files):
  python3 tools/enhanced/build.py --components-only --out /tmp/t7-components

GDK imports xgameruntime.dll from Windows system32. The bundled copy is
ONLY for a private Wine prefix's system32: NEVER install in native Windows.
The enhanced reconstruction DLL is packaged but not yet called by game code.
This distinction is mandatory and encoded in manifest.json.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = "BlackOps3_MSStore"
SHA_NAME = "sha256"


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def pinned_exe_hash():
    data = tomllib.loads((ROOT / "target.toml").read_text())
    matches = [row["exe"]["sha256"] for row in data["build"] if row["id"] == BUILD]
    if len(matches) != 1 or len(matches[0]) != 64:
        raise ValueError("Store EXE hash is missing or ambiguous in target.toml")
    return matches[0]


def validate_original(path):
    if not path.is_file() or sha256(path) != pinned_exe_hash():
        raise ValueError("Refusing original game EXE whose hash differs from pinned Store target")
    return path


def verify_reconstruction(path):
    import pefile
    if not path.is_file():
        raise ValueError("Missing compiled --enhanced reconstruction DLL")
    pe = pefile.PE(str(path), fast_load=True)
    if pe.FILE_HEADER.Machine != 0x8664 or not (pe.FILE_HEADER.Characteristics & 0x2000):
        raise ValueError("Enhanced reconstruction must be an x64 PE DLL")
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]])
    if not getattr(pe, "DIRECTORY_ENTRY_EXPORT", None):
        raise ValueError("Enhanced reconstruction has no exported functions")
    return path


def build_components(work):
    # The component builders consume the *same* enhanced/direct source tree
    # used by the --enhanced hybrid reconstruction.
    gdk_out, vendor_out = work / "_gdk", work / "_xcurl"
    for script, dest in (
        ("tools/offline/build_gdk_stub.py", gdk_out),
        ("tools/offline/build_vendor_stubs.py", vendor_out),
    ):
        subprocess.run([sys.executable, str(ROOT / script), "--out", str(dest)],
                       check=True, cwd=ROOT)
    sys.path.insert(0, str(ROOT / "tests" / "direct"))
    from gdk_stub import audit as audit_gdk
    from vendor_stubs import audit as audit_xcurl
    gdk, xcurl = gdk_out / "xgameruntime.dll", vendor_out / "xcurl.dll"
    audit_gdk(gdk)
    audit_xcurl(xcurl)
    return gdk, xcurl


def components_manifest(artifacts, *, full):
    return {
        "format": 1,
        "project": "t7",
        "target": BUILD,
        "variant": "enhanced",
        "type": "local-Wine-diagnostic-with-reconstructed-enhancements" if full
                else "enhanced-components-only",
        "original_executable_modified": False,
        "legacy_patched_pe_used": False,
        "components": artifacts,
        "compiled_features": {
            "offline_gdk_compatibility": True,
            "offline_xcurl_failure_boundary": True,
            "local_player_identity": True,
            "direct_udp_transport": True,
            "authenticated_v2_and_replay_defense": True,
            "enhanced_reconstruction_compiled": full,
        },
        "verified": {
            "component_export_and_import_audits": True,
            "game_engine_hooks_installed": False,
            "native_windows_startup": False,
            "rendered_menu": False,
            "fastfiles_loaded": False,
            "offline_match_started": False,
            "direct_multiplayer_join": False,
            "whole_process_network_isolation": False,
        },
        "warning": "GDK shim is only for a private Wine prefix, never native Windows system32. "
                   "Enhanced reconstruction is included but its engine callsites are not hooked.",
    }


def package(output, original=None, reconstruction=None, components_only=False):
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Refusing to replace existing enhanced package: {output}")
    if components_only:
        if original is not None or reconstruction is not None:
            raise ValueError("--components-only cannot accept game binaries")
    else:
        if original is None or reconstruction is None:
            raise ValueError("Full enhanced package requires --original AND --recon")
        validate_original(Path(original))
        verify_reconstruction(Path(reconstruction))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".t7-enhanced-", dir=output.parent))
    try:
        gdk, xcurl = build_components(temporary)
        binaries = {
            "wine-system32/xgameruntime.dll": gdk,
            "xcurl.dll": xcurl,
        }
        if not components_only:
            binaries.update({
                "BlackOps3.exe": Path(original),
                "recon.dll": Path(reconstruction),
            })
        recorded = {}
        for name, source in sorted(binaries.items()):
            target = temporary / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if sha256(source) != sha256(target):
                raise IOError(f"Copy changed {name}")
            recorded[name] = {SHA_NAME: sha256(target), "bytes": target.stat().st_size}
        if not components_only and recorded["BlackOps3.exe"][SHA_NAME] != pinned_exe_hash():
            raise ValueError("Original executable changed while staging")
        # Remove intermediate build objects so the distributable has one
        # clearly inventoried set of runtime binaries.
        shutil.rmtree(temporary / "_gdk")
        shutil.rmtree(temporary / "_xcurl")
        manifest = components_manifest(recorded, full=not components_only)
        (temporary / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        os.rename(temporary, output)
        print(f"BO3 canonical enhanced {'components' if components_only else 'package'}: {output}")
        print("WARNING: native gameplay, enhanced engine hooks and whole-process isolation unverified.")
        return manifest
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--original", type=Path)
    parser.add_argument("--recon", type=Path)
    parser.add_argument("--components-only", action="store_true")
    parser.add_argument("--out", type=Path,
                        default=ROOT / "build" / BUILD / "enhanced-package")
    args = parser.parse_args()
    package(args.out, args.original, args.recon, args.components_only)


if __name__ == "__main__":
    main()
