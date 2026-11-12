#!/usr/bin/env python3
"""Audit all 17 pinned original XCurl imports against the standalone offline shim."""
import argparse
import csv
from pathlib import Path
import pefile
ROOT = Path(__file__).resolve().parents[2]
def audit(path):
    with (ROOT / "analysis/BlackOps3_MSStore/net/imports.tsv").open(newline="") as f:
        expected = {x["import"] for x in csv.DictReader(f, delimiter="\t")
                    if x["dll"].lower() == "xcurl.dll"}
    assert len(expected) == 17, f"expected 17 static XCurl imports; got {len(expected)}"
    pe = pefile.PE(str(path))
    assert pe.FILE_HEADER.Machine == 0x8664
    exported = {x.name.decode() for x in pe.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
    assert exported == expected, {"missing": sorted(expected-exported),
                                  "unexpected": sorted(exported-expected)}
    assert not getattr(pe, "DIRECTORY_ENTRY_IMPORT", []), "must not depend on vendor/network DLL"
    print("PASS: 17 XCurl exports, zero DLL imports")
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dll", type=Path, required=True)
    audit(ap.parse_args().dll)
