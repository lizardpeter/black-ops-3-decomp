#!/usr/bin/env python3
"""Synthetic evidence reducer tests; not a real Wine or native game run."""
import json
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tools/enhanced"))
from compare_startup import compare

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    base, updated = root/"baseline.json", root/"feature.json"
    missing = compare(base, updated)
    assert not missing["both_traces_present"] and not missing["menu_fix_confirmed"]
    base.write_text(json.dumps({"gdk_initialized_without_vendor":True,
                                "recon_probe_observed":True,
                                "recon_callback_execution_observed":False,
                                "runtime_class_names_first_64":["XThreading"]}))
    updated.write_text(json.dumps({"gdk_initialized_without_vendor":True,
                                   "recon_probe_observed":True,
                                   "recon_callback_execution_observed":True,
                                   "local_feature_interface_enabled":True,
                                   "local_feature_interface_granted":True,
                                   "runtime_class_names_first_64":["XThreading","XUser"],
                                   "fastfile_path_mentions_not_open_proof":["ui_mp.ff"]}))
    result = compare(base, updated)
    assert result["both_traces_present"]
    assert result["baseline"]["recon_probe_observed"]
    assert result["local_feature_probe"]["recon_callback_execution_observed"]
    assert not result["menu_fix_confirmed"]
    assert not result["local_feature_probe"]["fastfile_open_verified"]
    assert result["local_feature_probe"]["fastfile_names_mentioned_not_open_proof"] == ["ui_mp.ff"]
print("PASS: two-run startup comparisons preserve missing/observed distinctions and never invent menu success")
