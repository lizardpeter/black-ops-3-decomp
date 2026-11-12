#!/usr/bin/env python3
"""Audit BO3's app-local offline WinHTTP shim against the pinned import inventory."""
import argparse
import csv
from pathlib import Path
import pefile

ROOT = Path(__file__).resolve().parents[2]


def audit(path):
    with (ROOT / "analysis/BlackOps3_MSStore/net/imports.tsv").open(newline="") as stream:
        expected = {row["import"] for row in csv.DictReader(stream, delimiter="\t")
                    if row["dll"].lower() == "winhttp.dll"}
    if len(expected) != 16:
        raise ValueError(f"Unexpected Store WinHTTP import count: {len(expected)}")
    pe = pefile.PE(str(path))
    if pe.FILE_HEADER.Machine != 0x8664 or pe.OPTIONAL_HEADER.Magic != 0x20B:
        raise ValueError("WinHTTP shim must be an x64 DLL")
    exported = {symbol.name.decode() for symbol in pe.DIRECTORY_ENTRY_EXPORT.symbols if symbol.name}
    if exported != expected:
        raise ValueError(f"WinHTTP export mismatch: missing={sorted(expected-exported)} "
                         f"extra={sorted(exported-expected)}")
    imports = {dll.dll.decode().lower():
               {symbol.name.decode() for symbol in dll.imports if symbol.name}
               for dll in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])}
    if imports != {"kernel32.dll": {"SetLastError"}}:
        raise ValueError(f"WinHTTP shim unexpectedly imports dependencies: {imports}")
    print("PASS: 16 pinned WinHTTP exports; no sockets, vendor modules or HTTP provider imports")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    audit(parser.parse_args().dll)
