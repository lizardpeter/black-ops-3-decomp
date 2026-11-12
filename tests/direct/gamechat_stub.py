#!/usr/bin/env python3
"""Pinned BO3 Store GameChat2 import ABI inventory/PE boundary audit.

The shim is *loader-compatibility only*: no actual Xbox chat API or signed-in
identity is present. An exact PE export match never establishes ABI correctness
or proves the game handles all API failures.
"""
import argparse
import csv
from pathlib import Path
import pefile

ROOT = Path(__file__).resolve().parents[2]

def expected_exports():
    with (ROOT / "analysis/BlackOps3_MSStore/net/imports.tsv").open(newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    imported = {row["import"] for row in rows if row["dll"].lower() == "gamechat2.dll"}
    if len(imported) != 16:
        raise ValueError(f"Unexpected pinned BO3 GameChat2 import count {len(imported)}")
    return imported

def audit(path):
    pe = pefile.PE(str(path))
    if pe.FILE_HEADER.Machine != 0x8664 or pe.OPTIONAL_HEADER.Magic != 0x20B:
        raise ValueError("GameChat2 no-vendor shim must be x64 PE32+")
    exported = {s.name.decode("ascii") for s in pe.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
    expected = expected_exports()
    if expected != exported:
        raise ValueError(f"GameChat2 import mismatch: missing {sorted(expected-exported)}, extra {sorted(exported-expected)}")
    if getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        raise ValueError("GameChat2 no-vendor shim must not import Xbox, WinHTTP, Winsock or any other DLL")
    print("PASS: 16 pinned GameChat2 imports satisfied; zero external DLL dependencies (loader-level only)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dll", required=True, type=Path)
    audit(parser.parse_args().dll)
