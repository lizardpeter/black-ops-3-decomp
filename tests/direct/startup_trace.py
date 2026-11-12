#!/usr/bin/env python3
"""Trace reducer is strict about successes, exposes only bounded API arguments."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/offline"))
from startup_trace import reduce_log, redact_args

empty = reduce_log("")
assert not empty["gdk_initialized_without_vendor"]
assert not empty["fastfile_open_verified"] and not empty["menu_render_verified"]
assert not empty["map_loaded_verified"] and not empty["game_join_verified"]
assert empty["logged_gdk_queries"] == 0
raw = 'wine:trace: T7GDK:INIT_OK_NO_VENDOR\nwine:trace: T7GDK:QUERY_API=0000000000000015\n'
raw += "T7GDK:LOCAL_PROFILE_PREPARED\n" + ("T7GDK:QUERY_API=ABCDEF1234567890\n" * 100)
report = reduce_log(raw)
assert report["gdk_initialized_without_vendor"] and report["local_profile_prepared"]
assert report["logged_gdk_queries"] == 101
assert len(report["query_arguments_first_64"]) == 64
assert not report["menu_render_verified"]
assert redact_args(["+direct_player", "ABCDEF1234567890", "Secret Name",
                    "+connect", "127.0.0.1:27016"]) == [
                        "+direct_player", "<local-id>", "<local-name>", "+connect", "127.0.0.1:27016"]
print("PASS: GDK startup observations, bounded reporting, no gameplay false positives, ID redaction")
