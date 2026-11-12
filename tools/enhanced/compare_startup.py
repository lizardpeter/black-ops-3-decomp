#!/usr/bin/env python3
"""Compare two observed GDK startup traces without inferring gameplay success.

Missing traces remain missing (rather than silently treated as passing).
Raw file paths, identities and binaries never enter this report.
"""
import argparse
import json
from pathlib import Path

def load(path):
    if not Path(path).is_file():
        return {"status": "missing", "source": str(Path(path).name)}
    value = json.loads(Path(path).read_text())
    assets_path = Path(path).parent / "asset_preflight.json"
    assets = json.loads(assets_path.read_text()) if assets_path.is_file() else {}
    asset_status = str(assets.get("status", "not-reported"))
    return {
        "status": "observed",
        "asset_preflight_status": asset_status,
        "zone_fastfile_count": int(assets.get("fastfile_count", 0)),
        "menu_assets_present_not_loaded": bool(assets.get("fastfiles_present", False)),
        "gdk_initialized_without_vendor": bool(value.get("gdk_initialized_without_vendor")),
        "recon_probe_observed": bool(value.get("recon_probe_observed")),
        "recon_callback_execution_observed": bool(value.get("recon_callback_execution_observed")),
        "local_feature_interface_enabled": bool(value.get("local_feature_interface_enabled")),
        "local_feature_interface_granted": bool(value.get("local_feature_interface_granted")),
        "local_package_interface_enabled": bool(value.get("local_package_interface_enabled")),
        "local_package_interface_granted": bool(value.get("local_package_interface_granted")),
        "package_methods_first_32": value.get("package_methods_first_64", [])[:32],
        "logged_gdk_queries": int(value.get("logged_gdk_queries", 0)),
        "last_requested_runtime_class": value.get("last_requested_runtime_class"),
        "first_16_runtime_classes": value.get("runtime_class_names_first_64", [])[:16],
        "fastfile_names_mentioned_not_open_proof": value.get("fastfile_path_mentions_not_open_proof", [])[:20],
        "fastfile_open_verified": False,
        "menu_render_verified": False,
    }

def compare(baseline_path, feature_path, probe_label="local_feature_probe"):
    if probe_label not in ("local_feature_probe", "local_package_probe"):
        raise ValueError("Unknown GDK A/B startup probe type")
    baseline, feature = load(baseline_path), load(feature_path)
    return {
        "baseline": baseline,
        probe_label: feature,
        "both_traces_present": baseline["status"] == feature["status"] == "observed",
        "menu_fix_confirmed": False,
        "native_windows_gameplay_verified": False,
        "interpretation": "Runtime GDK/factory observations and disk-only asset inventory; no missing result, probe or FastFile path is a menu pass.",
    }

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("feature", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--probe-label", choices=("local_feature_probe", "local_package_probe"), default="local_feature_probe")
    args = ap.parse_args()
    report = compare(args.baseline, args.feature, args.probe_label)
    content = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.write_text(content)
    else:
        print(content, end="")

if __name__ == "__main__":
    main()
