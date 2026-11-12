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
MARKERS = (
    "T7GDK:INIT_OK_NO_VENDOR",
    "T7GDK:LOCAL_PROFILE_PREPARED",
    "T7GDK:LOCAL_PROFILE_UNSET",
    "T7GDK:UNINITIALIZE",
    "T7GDK:ERROR_REPORT_IGNORED",
    "T7D:LOCAL_PROFILE_PREPARED",
)

def reduce_log(text):
    # Query values are API identifiers from the stub, not game accounts.
    # They may be addresses depending on the internal ABI: do not call them GDK
    # service IDs until that ABI is demonstrated.
    observations = {marker: marker in text for marker in MARKERS}
    api = QUERY.findall(text)
    return {
        "source": "Wine OutputDebugStringA, when +debugstr is enabled",
        "gdk_initialized_without_vendor": observations["T7GDK:INIT_OK_NO_VENDOR"],
        "local_profile_prepared": observations["T7GDK:LOCAL_PROFILE_PREPARED"],
        "local_profile_unset": observations["T7GDK:LOCAL_PROFILE_UNSET"],
        "logged_gdk_queries": len(api),
        "query_arguments_first_64": api[:64],
        "observed_markers": [x for x in MARKERS if observations[x]],
        "fastfile_open_verified": False,
        "menu_render_verified": False,
        "map_loaded_verified": False,
        "game_join_verified": False,
        "native_windows_verified": False,
        "note": "A diagnostic log cannot establish gameplay; unknown/missing events are not a pass."
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
