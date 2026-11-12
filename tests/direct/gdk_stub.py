#!/usr/bin/env python3
"""Structural audit of the GDK stub: validates PE exports; no runtime claims."""
import argparse
import pefile
from pathlib import Path

def audit(path):
    pe = pefile.PE(str(path))
    assert pe.FILE_HEADER.Machine == 0x8664, "must be x64"
    assert pe.OPTIONAL_HEADER.Magic == 0x20B, "must be PE32+"
    exports = {s.name.decode() for s in pe.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
    required = {"InitializeApiImpl", "InitializeApiImplEx", "UninitializeApiImpl",
                "XErrorReport", "QueryApiImpl"}
    assert exports == required, (exports, required)
    imported = {d.dll.decode().lower(): {i.name.decode() for i in d.imports if i.name}
                for d in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])}
    assert set(imported) <= {"kernel32.dll"}, imported
    assert imported.get("kernel32.dll") == {"GetCommandLineA", "OutputDebugStringA"}, imported
    print("PASS: unmodified-exe Wine stub has exactly five GDK exports; no vendor or socket imports")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dll", type=Path, required=True)
    audit(ap.parse_args().dll)
