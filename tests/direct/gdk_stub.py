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
                "XErrorReport", "QueryApiImpl", "T7EnhancedCapabilities",
                "T7EnhancedEngineIntegrated", "T7EnhancedReconLoaded", "T7DirectPlayerConfigure",
                "T7DirectPlayerId", "T7DirectPlayerIdText", "T7DirectPlayerName",
                "T7DirectLoadStartupProfile", "T7DirectWireVersion", "T7DirectSetKey",
                "T7DirectOpen", "T7DirectClose", "T7DirectSelectPeer",
                "T7DirectPeer", "T7DirectPort", "T7DirectParse",
                "T7DirectSend", "T7DirectReceive", "T7DirectSameAddress"}
    assert exports == required, (exports, required)
    imported = {d.dll.decode().lower(): {i.name.decode() for i in d.imports if i.name}
                for d in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])}
    assert set(imported) == {"kernel32.dll", "ws2_32.dll"}, imported
    assert imported["kernel32.dll"] == {"GetCommandLineA", "OutputDebugStringA",
        "AcquireSRWLockExclusive", "ReleaseSRWLockExclusive",
        "GetModuleFileNameW", "GetModuleHandleW", "LoadLibraryW",
        "GetProcAddress", "GetLastError", "GetEnvironmentVariableA", "FreeLibrary"}, imported
    assert imported["ws2_32.dll"] == {"WSAStartup", "socket", "closesocket",
        "ioctlsocket", "bind", "getsockname", "sendto", "recvfrom"}, imported
    print("PASS: GDK shim includes custom local identity/UDP with no vendor or HTTP imports")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dll", type=Path, required=True)
    audit(ap.parse_args().dll)
