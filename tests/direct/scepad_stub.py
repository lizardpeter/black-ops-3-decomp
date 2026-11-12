#!/usr/bin/env python3
"""Audit BO3's 7 original Sony controller entrypoints; never claim pad input."""
import argparse
from pathlib import Path
import pefile
EXPECTED = {
    "scePadInit", "scePadTerminate", "scePadOpen", "scePadClose",
    "scePadReadState", "scePadSetVibration", "scePadGetControllerInformation",
}

def audit(path):
    pe = pefile.PE(str(path))
    if pe.FILE_HEADER.Machine != 0x8664 or pe.OPTIONAL_HEADER.Magic != 0x20B:
        raise ValueError("ScePad offline shim must be x64 PE32+")
    exported = {e.name.decode("ascii") for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
    if exported != EXPECTED:
        raise ValueError(f"Wrong ScePad import surface: missing {sorted(EXPECTED-exported)}, extra {sorted(exported-EXPECTED)}")
    if getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        raise ValueError("No-device controller fallback must not load system, Sony, Xbox or network DLLs")
    print("PASS: exactly 7 ScePad exports, no external imports; device APIs remain unimplemented")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dll", required=True, type=Path)
    audit(parser.parse_args().dll)
