#!/usr/bin/env python3
"""Build the *isolated Wine diagnostic* replacement for xgameruntime.dll.

This is the byte-identical-exe path from docs/native-launch.md, not the obsolete
patched-PE offline package. The binary is intended for an isolated Wine prefix's
system32 only, never to overwrite a Windows system DLL.

    python3 tools/offline/build_gdk_stub.py [--out build/BlackOps3_MSStore/gdk-stub]
"""
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ("enhanced/offline/xgameruntime_stub.cpp",
           "enhanced/direct/profile.cpp", "enhanced/direct/startup.cpp",
           "enhanced/direct/transport.cpp")

def run(*args):
    proc = subprocess.run([str(a) for a in args], text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(f"{' '.join(map(str,args))}\n{proc.stdout}{proc.stderr}")

def build(out):
    out.mkdir(parents=True, exist_ok=True)
    objects = []
    # Stable enhanced-local ABI. BO3's original packet entrypoints are not hooked.
    local_api = (
        "T7EnhancedCapabilities", "T7EnhancedEngineIntegrated",
        "T7DirectPlayerConfigure", "T7DirectPlayerId",
        "T7DirectPlayerIdText", "T7DirectPlayerName",
        "T7DirectLoadStartupProfile", "T7DirectWireVersion", "T7DirectSetKey",
        "T7DirectOpen", "T7DirectClose", "T7DirectSelectPeer",
        "T7DirectPeer", "T7DirectPort", "T7DirectParse",
        "T7DirectSend", "T7DirectReceive", "T7DirectSameAddress",
    )
    for src in SOURCES:
        obj = out / (Path(src).stem + ".obj")
        run("clang++", "--target=x86_64-pc-windows-msvc", "-std=c++17", "-O2",
            "-fno-exceptions", "-fno-rtti", "-ffreestanding", "-fno-builtin",
            "-fno-stack-protector", "-mno-stack-arg-probe", "-Wall", "-Werror",
            "-isystem", ROOT / "tools/recon/include",
            "-c", ROOT / src, "-o", obj)
        objects.append(obj)
    defs = out / "kernel32.def"
    defs.write_text("LIBRARY kernel32.dll\nEXPORTS\n" +
                    "    GetCommandLineA\n    OutputDebugStringA\n" +
                    "    AcquireSRWLockExclusive\n    ReleaseSRWLockExclusive\n")
    lib = out / "kernel32.lib"
    run("llvm-lib", "/machine:x64", f"/def:{defs}", f"/out:{lib}")
    winsock = out / "ws2_32.def"
    winsock.write_text("LIBRARY ws2_32.dll\nEXPORTS\n" +
                       "".join(f"    {name}\n" for name in
                               ("WSAStartup", "socket", "closesocket", "ioctlsocket",
                                "bind", "getsockname", "sendto", "recvfrom")))
    winsock_lib = out / "ws2_32.lib"
    run("llvm-lib", "/machine:x64", f"/def:{winsock}", f"/out:{winsock_lib}")
    dll = out / "xgameruntime.dll"
    run("lld-link", "/dll", "/entry:_DllMainCRTStartup", "/nodefaultlib",
        "/base:0x190000000", "/subsystem:windows", f"/out:{dll}",
        *[f"/export:{name}" for name in local_api],
        *objects, lib, winsock_lib)
    print(f"Built {dll} ({dll.stat().st_size} bytes): local enhanced runtime compiled; BO3 engine packet entrypoints NOT hooked")
    return dll

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "build/BlackOps3_MSStore/gdk-stub")
    build(ap.parse_args().out)
