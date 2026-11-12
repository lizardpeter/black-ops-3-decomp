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
The GDK shim now attempts a narrow in-process recon probe and GDK callback;\nits success and gameplay integration require actual runtime evidence.
This distinction is mandatory and encoded in manifest.json.
"""
import argparse
import csv
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


def image_ranges_overlap(base_a, size_a, base_b, size_b):
    """Check Win64 mapped image intervals, not file sizes or RVA overlaps."""
    for name, value in (("base_a", base_a), ("base_b", base_b),
                        ("size_a", size_a), ("size_b", size_b)):
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"Invalid PE image interval {name}")
    if not size_a or not size_b or base_a + size_a > (1 << 64) or base_b + size_b > (1 << 64):
        raise ValueError("Invalid PE image size or overflow")
    return base_a < base_b + size_b and base_b < base_a + size_a


def validate_image_layout(original, reconstruction):
    """Reject actual EXE/DLL preferred-image overlaps, without guessing ranges."""
    import pefile
    exe = pefile.PE(str(original), fast_load=True)
    dll = pefile.PE(str(reconstruction), fast_load=True)
    a, b = exe.OPTIONAL_HEADER, dll.OPTIONAL_HEADER
    if image_ranges_overlap(a.ImageBase, a.SizeOfImage, b.ImageBase, b.SizeOfImage):
        raise ValueError("Enhanced reconstruction preferred base overlaps the actual Store EXE mapped image")
    if not (b.DllCharacteristics & 0x40):
        raise ValueError("Enhanced reconstruction must allow ASLR (IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE)")
    if dll.FILE_HEADER.Characteristics & 0x0001:
        raise ValueError("Enhanced reconstruction is fixed / RELOCS_STRIPPED")
    return {
        "original_image_base": f"0x{a.ImageBase:X}",
        "original_image_size": f"0x{a.SizeOfImage:X}",
        "recon_preferred_base": f"0x{b.ImageBase:X}",
        "recon_image_size": f"0x{b.SizeOfImage:X}",
        "recon_dynamicbase": True,
    }


def verify_reconstruction(path):
    import pefile
    if not path.is_file():
        raise ValueError("Missing compiled --enhanced reconstruction DLL")
    pe = pefile.PE(str(path), fast_load=True)
    if pe.FILE_HEADER.Machine != 0x8664 or not (pe.FILE_HEADER.Characteristics & 0x2000):
        raise ValueError("Enhanced reconstruction must be an x64 PE DLL")
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]])
    if not (pe.OPTIONAL_HEADER.DllCharacteristics & 0x40):
        raise ValueError("Enhanced reconstruction must be ASLR-relocatable")
    if pe.FILE_HEADER.Characteristics & 0x0001:
        raise ValueError("Enhanced reconstruction cannot have stripped relocations")
    if not getattr(pe, "DIRECTORY_ENTRY_EXPORT", None):
        raise ValueError("Enhanced reconstruction has no exported functions")
    exports = {e.name.decode("ascii") for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
    required = {"T7EnhancedReconProbe", "T7EnhancedObserveGdkDispatch",
                "T7EnhancedObservedGdkCalls"}
    if not required <= exports:
        raise ValueError("Enhanced reconstruction is missing GDK bridge exports: " +
                         repr(sorted(required - exports)))
    return path


def reconstruction_metrics(recon):
    """Source-derived evidence, not in-game integration or whole-game coverage."""
    symbol_file = recon.parent / "recon.symbols.tsv"
    hybrid_file = recon.parent / "hybrid.tsv"
    if not symbol_file.is_file() or not hybrid_file.is_file():
        raise ValueError("Enhanced reconstruction must include its generated symbols and hybrid tables")
    with symbol_file.open(newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    with hybrid_file.open(newline="") as stream:
        hybrid = list(csv.DictReader(stream, delimiter="\t"))
    if not rows or not hybrid:
        raise ValueError("Reconstruction tables cannot be empty")
    features = sum(1 for row in rows if row["source"].replace("\\", "/").startswith("enhanced/"))
    if not features:
        raise ValueError("This DLL has no reported enhanced functions")
    return {
        "reconstructed_exports_in_table": len(rows),
        "enhanced_exports_in_table": features,
        "hybrid_symbols_in_table": len(hybrid),
        "unresolved_hybrid_symbols": sum(1 for row in hybrid
                                          if row["kind"].startswith("unresolved")),
        "engine_hooks_verified": False,
    }

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
    from winhttp_stub import audit as audit_winhttp
    from gamechat_stub import audit as audit_gamechat
    from scepad_stub import audit as audit_pad
    gdk, xcurl = gdk_out / "xgameruntime.dll", vendor_out / "xcurl.dll"
    audit_gdk(gdk)
    audit_xcurl(xcurl)
    winhttp = vendor_out / "winhttp.dll"
    audit_winhttp(winhttp)
    gamechat = vendor_out / "gamechat2.dll"
    audit_gamechat(gamechat)
    pad = vendor_out / "libScePad.dll"
    audit_pad(pad)
    return gdk, xcurl, winhttp, gamechat, pad


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
            "offline_winhttp_failure_boundary": True,
            "offline_gamechat2_loader_boundary": True,
            "offline_no_device_scepad_loader_boundary": True,
            "local_player_identity": True,
            "direct_udp_transport": True,
            "authenticated_v3_directional_and_replay_defense": True,
            "enhanced_reconstruction_compiled": full,
            "gdk_can_attempt_recon_load": True,
            "offline_local_feature_com_available": True,
            "recon_gdk_bridge_compiled": full,
        },
        "verified": {
            "component_export_and_import_audits": True,
            "game_engine_hooks_installed": False,
            "in_process_recon_bridge_observed": False,
            "native_windows_startup": False,
            "rendered_menu": False,
            "fastfiles_loaded": False,
            "offline_match_started": False,
            "direct_multiplayer_join": False,
            "whole_process_network_isolation": False,
        },
        "warning": "GDK shim is only for a private Wine prefix, never native Windows system32. "
                   "The shim can call recon.dll through the GDK factory; COM feature availability is opt-in and always false. Actual menu, engine hook and network isolation results remain unverified.",
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
        layout = validate_image_layout(Path(original), Path(reconstruction))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".t7-enhanced-", dir=output.parent))
    try:
        gdk, xcurl, winhttp, gamechat, pad = build_components(temporary)
        binaries = {
            "wine-system32/xgameruntime.dll": gdk,
            "xcurl.dll": xcurl,
            "winhttp.dll": winhttp,
            "gamechat2.dll": gamechat,
            "libScePad.dll": pad,
        }
        if not components_only:
            binaries.update({
                "BlackOps3.exe": Path(original),
                "recon.dll": Path(reconstruction),
            })
        recorded = {}
        recorded_metadata = {}
        for name, source in sorted(binaries.items()):
            target = temporary / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if sha256(source) != sha256(target):
                raise IOError(f"Copy changed {name}")
            recorded[name] = {SHA_NAME: sha256(target), "bytes": target.stat().st_size}
        if not components_only and recorded["BlackOps3.exe"][SHA_NAME] != pinned_exe_hash():
            raise ValueError("Original executable changed while staging")
        metrics = None
        if not components_only:
            metrics = reconstruction_metrics(Path(reconstruction))
            metadata_paths = {
                "metadata/recon.symbols.tsv": Path(reconstruction).parent / "recon.symbols.tsv",
                "metadata/hybrid.tsv": Path(reconstruction).parent / "hybrid.tsv",
                "metadata/patches.tsv": ROOT / "records/patches.tsv",
            }
            for name, source in sorted(metadata_paths.items()):
                target = temporary / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                recorded_metadata[name] = {SHA_NAME: sha256(target),
                                           "bytes": target.stat().st_size}
        # Remove intermediate build objects so the distributable has one
        # clearly inventoried set of runtime binaries.
        shutil.rmtree(temporary / "_gdk")
        shutil.rmtree(temporary / "_xcurl")
        manifest = components_manifest(recorded, full=not components_only)
        if not components_only:
            manifest["image_layout"] = layout
        manifest["metadata"] = recorded_metadata
        manifest["reconstruction_metrics"] = metrics
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
