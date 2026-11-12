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
CALLER = re.compile(r"T7GDK:QUERY_CALLER_RVA=([0-9A-Fa-f]{8})(?![0-9A-Fa-f])")
ERROR = re.compile(r"T7GDK:RECON_LOAD_ERROR=([0-9A-Fa-f]{8})(?![0-9A-Fa-f])")
# Path mentions are *not* proof of successful file open. Strip directories so
# the derived report never contains game/user directory names.
FASTFILE = re.compile(r"(?i)(?:zone[\\\\/])([a-z0-9_+.-]{1,96}\\.ff)\\b")
LOCALIZATION = re.compile(r"(?i)\\b(localization_[a-z0-9_+.-]{1,80}\\.txt)\\b")
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
)

def reduce_log(text):
    # Query values are API identifiers from the stub, not game accounts.
    # They may be addresses depending on the internal ABI: do not call them GDK
    # service IDs until that ABI is demonstrated.
    observations = {marker: marker in text for marker in MARKERS}
    api = QUERY.findall(text)
    callers = CALLER.findall(text)
    failure = ERROR.findall(text)
    ff = list(dict.fromkeys(name.lower() for name in FASTFILE.findall(text)))[:64]
    localization = list(dict.fromkeys(name.lower() for name in LOCALIZATION.findall(text)))[:64]
    return {
        "source": "Wine OutputDebugStringA, when +debugstr is enabled",
        "gdk_initialized_without_vendor": observations["T7GDK:INIT_OK_NO_VENDOR"],
        "local_profile_prepared": observations["T7GDK:LOCAL_PROFILE_PREPARED"],
        "local_profile_unset": observations["T7GDK:LOCAL_PROFILE_UNSET"],
        "recon_probe_observed": observations["T7GDK:RECON_PROBE_OK"],
        "recon_callback_execution_observed": observations["T7GDK:RECON_CALLBACK_EXECUTED"],
        "recon_load_failure_observed": observations["T7GDK:RECON_LOAD_FAILED"],
        "recon_load_error_codes_first_8": failure[:8],
        "logged_gdk_queries": len(api),
        "logged_gdk_caller_rvas": len(callers),
        "query_caller_rvas_first_64": callers[:64],
        "fastfile_path_mentions_not_open_proof": ff,
        "localization_path_mentions_not_open_proof": localization,
        "query_arguments_first_64": api[:64],
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
