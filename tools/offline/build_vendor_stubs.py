#!/usr/bin/env python3
"""Build offline-only XCurl replacement for isolated BO3 diagnostics."""
import argparse
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def build(out):
    out.mkdir(parents=True, exist_ok=True)
    obj, dll = out / "xcurl.obj", out / "xcurl.dll"
    for cmd in [
        ["clang++", "--target=x86_64-pc-windows-msvc", "-std=c++17", "-O2",
         "-fno-exceptions", "-fno-rtti", "-ffreestanding", "-fno-builtin",
         "-fno-stack-protector", "-mno-stack-arg-probe", "-Wall", "-Werror",
         "-c", str(ROOT / "enhanced/offline/xcurl_stub.cpp"), "-o", str(obj)],
        ["lld-link", "/dll", "/entry:_DllMainCRTStartup", "/nodefaultlib",
         "/subsystem:windows", f"/out:{dll}", str(obj)]
    ]:
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode: raise RuntimeError(f"{cmd}\n{p.stdout}{p.stderr}")
    # WinHTTP is a separate Windows system provider; offline imports are
    # redirected only when the isolated game actually loads this app-local DLL.
    src = ROOT / "enhanced/offline/winhttp_stub.cpp"
    obj, winhttp = out / "winhttp.obj", out / "winhttp.dll"
    libdef = out / "kernel32.def"
    libdef.write_text("LIBRARY kernel32.dll\nEXPORTS\n    SetLastError\n")
    lib = out / "kernel32.lib"
    commands = [
        ["clang++", "--target=x86_64-pc-windows-msvc", "-std=c++17", "-O2",
         "-fno-exceptions", "-fno-rtti", "-ffreestanding", "-fno-builtin",
         "-fno-stack-protector", "-mno-stack-arg-probe", "-Wall", "-Werror",
         "-c", str(src), "-o", str(obj)],
        ["llvm-lib", "/machine:x64", f"/def:{libdef}", f"/out:{lib}"],
        ["lld-link", "/dll", "/entry:_DllMainCRTStartup", "/nodefaultlib",
         "/subsystem:windows", f"/out:{winhttp}", str(obj), str(lib)],
    ]
    for cmd in commands:
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode: raise RuntimeError(f"{cmd}\n{p.stdout}{p.stderr}")
    print(f"Built offline XCurl and WinHTTP shims in {out}; native game not tested")
    return dll
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "build/BlackOps3_MSStore/offline-shims")
    build(ap.parse_args().out)
