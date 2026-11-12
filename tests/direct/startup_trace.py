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
assert len(report["legacy_pointer_arguments_first_64"]) == 64
assert not report["menu_render_verified"]
traced = ("T7GDK:RECON_PROBE_OK\\nT7GDK:RECON_CALLBACK_EXECUTED\\n"
          "T7GDK:QUERY_API=0000000000000015\\n"
          "T7GDK:QUERY_CALLER_RVA=00920000\\n"
          "trace:CreateFileW Z:\\\\Games\\\\BO3\\\\zone\\\\ui_mp.ff\\n"
          "trace:CreateFileW /private/BO3/zone/core_common.ff\\n"
          "trace:CreateFileW /private/BO3/localization_en.txt\\n")
traced += ("T7GDK:QUERY_CLASS_GUID=073B7DCB-1FCF-4030-94BE-E3C9EB623428\\n"
           "T7GDK:QUERY_INTERFACE_GUID=073b7dcb-1fcf-4030-94be-e3c9eb623428\\n"
           "T7GDK:QUERY_CLASS_GUID=01acd177-91f9-4763-a38e-ccbb55ce32e0\\n")
triage = reduce_log(traced)
assert triage["class_guids_first_64"][0] == "073b7dcb-1fcf-4030-94be-e3c9eb623428"
assert triage["runtime_class_names_first_64"] == ["XThreading", "XUser"]
assert triage["last_requested_runtime_class"] == "XUser"
assert triage["interface_guids_first_64"] == ["073b7dcb-1fcf-4030-94be-e3c9eb623428"]
assert triage["recon_probe_observed"]
assert triage["recon_callback_execution_observed"]
assert triage["query_caller_rvas_first_64"] == ["00920000"]
assert sorted(triage["fastfile_path_mentions_not_open_proof"]) == ["core_common.ff", "ui_mp.ff"]
assert triage["localization_path_mentions_not_open_proof"] == ["localization_en.txt"]
assert not triage["fastfile_open_verified"] and not triage["menu_render_verified"]
assert "/private" not in str(triage) and "Games" not in str(triage)
failure = reduce_log("T7GDK:RECON_LOAD_FAILED\\nT7GDK:RECON_LOAD_ERROR=0000007E")
assert failure["recon_load_failure_observed"] and failure["recon_load_error_codes_first_8"] == ["0000007E"]
assert redact_args(["+direct_player", "ABCDEF1234567890", "Secret Name",
                    "+connect", "127.0.0.1:27016"]) == [
                        "+direct_player", "<local-id>", "<local-name>", "+connect", "127.0.0.1:27016"]
print("PASS: GDK startup observations, bounded reporting, no gameplay false positives, ID redaction")
