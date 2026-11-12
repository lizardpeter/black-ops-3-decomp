#!/usr/bin/env python3
"""Portable build path regression: canonical enhanced and faithful outputs."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tools"))
from build_recon import recon_output_dir
assert recon_output_dir("BlackOps3_MSStore", enhanced=True) == ROOT/"build/BlackOps3_MSStore/enhanced"
assert recon_output_dir("BlackOps3_MSStore", enhanced=False) == ROOT/"build"
assert recon_output_dir("BlackOps3_Steam", enhanced=True) == ROOT/"build/BlackOps3_Steam/enhanced"
print("PASS: canonical enhanced recon path and unchanged faithful reference path")
