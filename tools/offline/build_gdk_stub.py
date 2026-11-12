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
           "enhanced/direct/profile.cpp", "enhanced/direct/startup.cpp")

def run(*args):
    proc = subprocess.run([str(a) for a in args], text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(f"{' '.join(map(str,args))}\n{proc.stdout}{proc.stderr}")

def build(out):
    out.mkdir(parents=True, exist_ok=True)
    objects = []
    for src in SOURCES:
        obj = out / (Path(src).stem + ".obj")
        run("clang++", "--target=x86_64-pc-windows-msvc", "-std=c++17", "-O2",
            "-fno-exceptions", "-fno-rtti", "-ffreestanding", "-fno-builtin",
            "-fno-stack-protector", "-mno-stack-arg-probe", "-Wall", "-Werror",
            "-c", ROOT / src, "-o", obj)
        objects.append(obj)
    defs = out / "kernel32.def"
    defs.write_text("LIBRARY kernel32.dll\nEXPORTS\n    GetCommandLineA\n    OutputDebugStringA\n")
    lib = out / "kernel32.lib"
    run("llvm-lib", "/machine:x64", f"/def:{defs}", f"/out:{lib}")
    dll = out / "xgameruntime.dll"
    run("lld-link", "/dll", "/entry:_DllMainCRTStartup", "/nodefaultlib",
        "/base:0x180000000", "/subsystem:windows", f"/out:{dll}",
        *objects, lib)
    print(f"Built {dll} ({dll.stat().st_size} bytes); not tested in a game")
    return dll

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "build/BlackOps3_MSStore/gdk-stub")
    build(ap.parse_args().out)
