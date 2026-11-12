#!/usr/bin/env python3
"""Reduce Wine debug output to bounded, non-identifying BO3 startup milestones.

Only an observed event is marked observed. In particular, no FastFile or menu
milestone exists merely because the GDK shim initialized. No gameplay/session
success is inferred from a process remaining open.
"""
import argparse
import json
import re
from pathlib import Path

QUERY = re.compile(r"T7GDK:QUERY_API=([0-9A-Fa-f]{16})(?![0-9A-Fa-f])")
CLASS_GUID = re.compile(r"T7GDK:QUERY_CLASS_GUID=([0-9a-fA-F-]{36})(?![0-9A-Fa-f-])")
INTERFACE_GUID = re.compile(r"T7GDK:QUERY_INTERFACE_GUID=([0-9a-fA-F-]{36})(?![0-9A-Fa-f-])")
# Public GDK COM class identifiers, not user/account identities.
GDK_CLASSES = {
    "073b7dcb-1fcf-4030-94be-e3c9eb623428": "XThreading",
    "01acd177-91f9-4763-a38e-ccbb55ce32e0": "XUser",
    "f4faf4d4-2d04-4fce-b3e0-474a713a3e84": "XPersistentLocalStorage",
    "973a344e-24bf-4d0f-8457-56c534892b29": "XGame",
    "704c3f58-e629-4cc2-b197-30511b996fe2": "XGameSave",
    "0651aae2-4012-4077-bf84-8b9097090e2c": "XGameInvite",
    "0dd112ac-7c24-448c-b92b-3960fb5bd30c": "XStore",
    "af406016-e850-4aa8-a88d-2f3dcb9dac7e": "XPackage",
    "37e56907-2f10-41e8-b72f-36edb185331a": "XNetworking",
    "dfcd4649-4ff8-4043-ba07-35d607df98b0": "XGameUI",
    "e349bd1a-fc20-4e40-b99c-4178cc6b409f": "XSystem",
}
CALLER = re.compile(r"T7GDK:QUERY_CALLER_RVA=([0-9A-Fa-f]{8})(?![0-9A-Fa-f])")
ERROR = re.compile(r"T7GDK:RECON_LOAD_ERROR=([0-9A-Fa-f]{8})(?![0-9A-Fa-f])")
# Path mentions are *not* proof of successful file open. Strip directories so
# the derived report never contains game/user directory names.
FASTFILE = re.compile(r"(?i)(?:zone[\\/])([a-z0-9_+.-]{1,96}\.ff)\b")
LOCALIZATION = re.compile(r"(?i)\b(localization_[a-z0-9_+.-]{1,80}\.txt)\b")
# Diagnose failures *before* GDK initialization without exposing absolute
# Wine/user paths. Only known error categories and DLL basenames are retained.
WINE_ERROR = re.compile(r"(?i)err:([a-z0-9_-]{1,32}):([a-z0-9_-]{1,64})")
WINE_DLL = re.compile(r'(?i)\b(?:library|module)\s+(?:L")?([^\s"()]{1,240}\.dll)')
WIN_STATUS = re.compile(r"(?i)\b(?:c0000135|c000007b|c0000005|c0000142|0x8007007e)\b")

def wine_loader_diagnostics(log):
    categories = {}
    missing = []
    for line in log.splitlines():
        match = WINE_ERROR.search(line)
        if match:
            key = f"{match.group(1).lower()}:{match.group(2).lower()}"
            categories[key] = categories.get(key, 0) + 1
        if "not found" in line.lower() or "failed to load" in line.lower():
            for raw in WINE_DLL.findall(line):
                name = raw.replace("\\", "/").rsplit("/", 1)[-1].lower()
                if re.fullmatch(r"[a-z0-9_.+-]{1,96}\.dll", name) and name not in missing:
                    missing.append(name)
    status = list(dict.fromkeys(x.lower() for x in WIN_STATUS.findall(log)))[:12]
    return {
        "wine_error_categories_first_24": dict(list(categories.items())[:24]),
        "missing_dependency_dll_basename_candidates": missing[:24],
        "wine_loader_status_codes": status,
        "note": "Wine loader errors are diagnostic clues, not verified absent files or gameplay outcomes."
    }

MARKERS = (
    "T7GDK:INIT_OK_NO_VENDOR",
    "T7GDK:LOCAL_PROFILE_PREPARED",
    "T7GDK:LOCAL_PROFILE_UNSET",
    "T7GDK:UNINITIALIZE",
    "T7GDK:ERROR_REPORT_IGNORED",
    "T7D:LOCAL_PROFILE_PREPARED",
    "T7GDK:RECON_PROBE_OK",
    "T7GDK:RECON_IN_PROCESS",
    "T7GDK:RECON_CALLBACK_EXECUTED",
    "T7GDK:RECON_LOAD_FAILED",
    "T7GDK:RECON_INVALID_PROBE",
    "T7GDK:RECON_INVALID_EXE_DIRECTORY",
    "T7GDK:LOCAL_FEATURE_INTERFACE_ENABLED",
    "T7GDK:LOCAL_FEATURE_INTERFACE_GRANTED",
)

def reduce_log(text):
    # Query values are API identifiers from the stub, not game accounts.
    # They may be addresses depending on the internal ABI: do not call them GDK
    # service IDs until that ABI is demonstrated.
    observations = {marker: marker in text for marker in MARKERS}
    api = QUERY.findall(text)
    classes = [x.lower() for x in CLASS_GUID.findall(text)]
    interfaces = [x.lower() for x in INTERFACE_GUID.findall(text)]
    callers = CALLER.findall(text)
    failure = ERROR.findall(text)
    ff = list(dict.fromkeys(name.lower() for name in FASTFILE.findall(text)))[:64]
    localization = list(dict.fromkeys(name.lower() for name in LOCALIZATION.findall(text)))[:64]
    return {
        "source": "Wine OutputDebugStringA and error channels, when enabled",
        "pre_gdk_loader_diagnostics": wine_loader_diagnostics(text),
        "gdk_initialized_without_vendor": observations["T7GDK:INIT_OK_NO_VENDOR"],
        "local_profile_prepared": observations["T7GDK:LOCAL_PROFILE_PREPARED"],
        "local_profile_unset": observations["T7GDK:LOCAL_PROFILE_UNSET"],
        "recon_probe_observed": observations["T7GDK:RECON_PROBE_OK"],
        "local_feature_interface_enabled": observations["T7GDK:LOCAL_FEATURE_INTERFACE_ENABLED"],
        "local_feature_interface_granted": observations["T7GDK:LOCAL_FEATURE_INTERFACE_GRANTED"],
        "recon_callback_execution_observed": observations["T7GDK:RECON_CALLBACK_EXECUTED"],
        "recon_load_failure_observed": observations["T7GDK:RECON_LOAD_FAILED"],
        "recon_load_error_codes_first_8": failure[:8],
        "logged_gdk_queries": max(len(api), len(classes) +
                                  text.count("T7GDK:QUERY_CLASS_GUID_UNAVAILABLE")),
        "class_guids_first_64": classes[:64],
        "interface_guids_first_64": interfaces[:64],
        "runtime_class_names_first_64": [GDK_CLASSES.get(guid, "unknown") for guid in classes[:64]],
        "last_requested_runtime_class": GDK_CLASSES.get(classes[-1], "unknown") if classes else None,
        "logged_gdk_caller_rvas": len(callers),
        "query_caller_rvas_first_64": callers[:64],
        "fastfile_path_mentions_not_open_proof": ff,
        "localization_path_mentions_not_open_proof": localization,
        "legacy_pointer_arguments_first_64": api[:64],
        "observed_markers": [x for x in MARKERS if observations[x]],
        "fastfile_open_verified": False,
        "menu_render_verified": False,
        "map_loaded_verified": False,
        "game_join_verified": False,
        "native_windows_verified": False,
        "note": "File paths mentioned in Wine logs are not confirmed successful opens; observed GDK callbacks do not establish a rendered menu or game engine hooks."
    }

def redact_args(args):
    # Private player names and stable IDs must not go into shared CI metadata.
    safe = list(args)
    for i, arg in enumerate(args):
        if arg.lower() == "+direct_player":
            if i + 1 < len(safe): safe[i + 1] = "<local-id>"
            if i + 2 < len(safe): safe[i + 2] = "<local-name>"
    return safe

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = reduce_log(args.log.read_text(errors="replace"))
    if args.out:
        args.out.write_text(json.dumps(report, indent=2) + "\n")
    else:
        print(json.dumps(report, indent=2))
if __name__ == "__main__":
    main()
