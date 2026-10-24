#!/usr/bin/env python3
"""Build the offline package's recon.dll from enhanced/offline/*.cpp.

    python3 tools/offline/build_dll.py [--out build/BlackOps3_MSStore/offline]

clang (--target=x86_64-pc-windows-msvc) and lld-link, no Windows SDK and no CRT: every OS function the sources
call is declared dllimport in the source, and an import library is generated here for each DLL that provides one
(IMPORTS below; an unknown import stops the build). The DLL is linked at the fixed base 0x180000000 with
T7OfflineDllMain as its entry, as tools/offline/package.py requires.

This is the first, standalone form of the offline DLL. Reconstructed faithful functions (src/) join the same DLL
once tools/build_recon.py supports a build without a symbol reference build (ghosts-decomp links both together).
"""
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CFLAGS = ["--target=x86_64-pc-windows-msvc", "-O2", "-fno-exceptions", "-fno-rtti", "-ffreestanding",
          "-fno-builtin", "-fno-stack-protector", "-mno-stack-arg-probe", "-fms-extensions", "-Wall", "-Werror",
          "-Wno-unused-function"]
IMPORTS = {
    "kernel32.dll": ["GetModuleHandleW", "GetCurrentProcess", "TerminateProcess", "SetLastError", "GetProcAddress",
                     "LoadLibraryA", "LoadLibraryW", "LoadLibraryExA", "LoadLibraryExW", "GetModuleFileNameW",
                     "GetCurrentDirectoryA", "GetCurrentDirectoryW", "AcquireSRWLockExclusive",
                     "ReleaseSRWLockExclusive", "OutputDebugStringA", "GetEnvironmentVariableA"],
    "ws2_32.dll": ["WSASetLastError"],
}


def run(*cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stdout}{r.stderr}")
    return r.stdout


def main():
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else \
        ROOT / "build" / "BlackOps3_MSStore" / "offline"
    (out / "obj").mkdir(parents=True, exist_ok=True)
    objs = []
    for src in sorted((ROOT / "enhanced" / "offline").glob("*.cpp")):
        obj = out / "obj" / (src.stem + ".obj")
        run("clang++", "-std=c++17", f"-I{ROOT / 'enhanced' / 'include'}", *CFLAGS, "-c", src, "-o", obj)
        objs.append(obj)
    provider = {name: dll for dll, names in IMPORTS.items() for name in names}
    needed = defaultdict(set)
    for obj in objs:
        for line in run("llvm-nm", "--undefined-only", obj).splitlines():
            sym = line.split()[-1]
            if sym.startswith("__imp_"):
                name = sym[len("__imp_"):]
                if name not in provider:
                    sys.exit(f"{obj.name}: import {name} has no provider in tools/offline/build_dll.py IMPORTS")
                needed[provider[name]].add(name)
    libs = []
    for dll, names in sorted(needed.items()):
        stem = dll[:-4]
        (out / f"{stem}.def").write_text(f"LIBRARY {dll}\nEXPORTS\n" + "".join(f"    {n}\n" for n in sorted(names)))
        run("llvm-lib", "/machine:x64", f"/def:{out / (stem + '.def')}", f"/out:{out / (stem + '.lib')}")
        libs.append(out / f"{stem}.lib")
    dll = out / "recon.dll"
    run("lld-link", "/dll", "/entry:T7OfflineDllMain", "/nodefaultlib", "/base:0x180000000", "/fixed",
        "/subsystem:windows", f"/out:{dll}", f"/map:{out / 'recon.map'}", *objs, *libs)
    print(f"{dll} ({dll.stat().st_size} bytes) from {len(objs)} sources; imports: "
          + ", ".join(f"{d} ({len(n)})" for d, n in sorted(needed.items())))


if __name__ == "__main__":
    main()
