#!/usr/bin/env python3
"""Bounded Wine run of a BO3 executable on a virtual display, with all network sockets blocked.

    python3 tools/offline/wine_run.py --exe <exe> --game <game dir> --prefix <wine prefix> --output <new dir>
                                      [--seconds 120] [--shot-every 10] [--display :99] [-- game arguments]
    python3 tools/offline/wine_run.py --self-test

The exe must be one this repo knows: an original listed in target.toml (verified by sha256) or a package built by
tools/offline/package.py (verified against its manifest.json). It runs with the game directory as working
directory. Every process in the tree may create only AF_UNIX sockets (Wine's own IPC, the X display); IPv4, IPv6
and netlink sockets and io_uring are refused by an inherited seccomp policy, so the game cannot reach any server,
official or custom. The approach is ghosts-decomp's tools/offline/wine_smoke.py.

Writes to --output: wine.log (Wine's stderr with +loaddll,+seh and timestamps), stdout.log, shot-NNNs.png
desktop captures, and result.json (exit code, timeout, elapsed, hashes, socket policy).

This is a diagnostic on Linux/Wine with a software GPU: it shows how far startup gets, not how the game runs on
Windows hardware.
"""
import argparse
import ctypes
import ctypes.util
import hashlib
import json
import os
import platform
import signal
import subprocess
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def deny_ip_sockets():
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise RuntimeError("requires x86-64 Linux and libseccomp")
    lib = ctypes.CDLL(ctypes.util.find_library("seccomp") or "libseccomp.so.2", use_errno=True)
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]

    class Compare(ctypes.Structure):
        _fields_ = [("arg", ctypes.c_uint), ("op", ctypes.c_uint), ("a", ctypes.c_uint64), ("b", ctypes.c_uint64)]

    ctx = lib.seccomp_init(0x7FFF0000)  # SCMP_ACT_ALLOW
    if not ctx:
        raise RuntimeError("seccomp_init failed")
    try:
        # socket(family != AF_UNIX) -> EPERM (SCMP_ACT_ERRNO(1)); io_uring_setup -> EPERM
        for name, cmps in (("socket", (Compare(0, 1, 1, 0),)), ("io_uring_setup", ())):
            nr = lib.seccomp_syscall_resolve_name(name.encode())
            if nr < 0 or lib.seccomp_rule_add(ctx, 0x50001, nr, len(cmps), *cmps):
                raise RuntimeError("cannot install socket policy: " + name)
        if lib.seccomp_load(ctx):
            raise RuntimeError("seccomp_load failed")
    finally:
        lib.seccomp_release(ctx)


def self_test():
    prog = """import socket, subprocess, sys
for fam in (socket.AF_INET, socket.AF_INET6, socket.AF_NETLINK):
    try: socket.socket(fam)
    except PermissionError: pass
    else: raise AssertionError(fam)
socket.socket(socket.AF_UNIX).close()
r = subprocess.run([sys.executable, '-c', 'import socket; socket.socket(socket.AF_INET)'], capture_output=True)
assert r.returncode == 1, 'child not covered'
print('PASS: IP/netlink sockets denied, AF_UNIX allowed, children inherit the policy')
"""
    subprocess.run([sys.executable, "-c", prog], preexec_fn=deny_ip_sockets, check=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def identify(exe: Path):
    """(kind, id, sha256) for a known original or package; raises otherwise."""
    digest = sha256(exe)
    cfg = tomllib.loads((ROOT / "target.toml").read_text())
    for b in cfg.get("build", []):
        if b["exe"]["sha256"] == digest:
            return "original", b["id"], digest
    manifest = exe.parent / "manifest.json"
    if manifest.exists():
        m = json.loads(manifest.read_text())
        if m.get("exe_sha256") == digest:
            dll = exe.parent / "recon.dll"
            if m.get("dll_sha256") and sha256(dll) != m["dll_sha256"]:
                raise ValueError("package recon.dll does not match its manifest")
            return "package:" + m.get("mode", "?"), m.get("build", "?"), digest
    raise ValueError(f"{exe} is neither an original in target.toml nor a verified package")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--exe", type=Path)
    ap.add_argument("--game", type=Path)
    ap.add_argument("--prefix", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--wine", default="/usr/lib/wine/wine64")
    ap.add_argument("--seconds", type=int, default=120)
    ap.add_argument("--shot-every", type=int, default=10)
    ap.add_argument("--display", default=":99")
    ap.add_argument("--debug", default="+timestamp,+pid,+loaddll,+seh")
    ap.add_argument("--dlloverrides", default="mscoree,mshtml=")
    ap.add_argument("arguments", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    if not all((a.exe, a.game, a.prefix, a.output)):
        ap.error("--exe, --game, --prefix and --output are required")
    if not 1 <= a.seconds <= 3600:
        ap.error("--seconds must be 1..3600")
    exe, game = a.exe.resolve(), a.game.resolve()
    kind, build, digest = identify(exe)
    a.output.mkdir(parents=True, exist_ok=False)
    env = {k: v for k, v in os.environ.items() if "proxy" not in k.lower()}  # no proxy handed to Wine
    env.update(WINEPREFIX=str(a.prefix.resolve()), WINEARCH="win64", DISPLAY=a.display,
               WINEDEBUG=a.debug, WINEDLLOVERRIDES=a.dlloverrides)
    args = a.arguments[1:] if a.arguments[:1] == ["--"] else a.arguments
    start, timed_out, shots = time.monotonic(), False, []
    with open(a.output / "stdout.log", "wb") as out, open(a.output / "wine.log", "wb") as err:
        p = subprocess.Popen([a.wine, str(exe), *args], cwd=game, env=env, stdout=out, stderr=err,
                             close_fds=True, start_new_session=True, preexec_fn=deny_ip_sockets)
        next_shot = a.shot_every
        while True:
            try:
                code = p.wait(timeout=1)
                break
            except subprocess.TimeoutExpired:
                pass
            t = time.monotonic() - start
            if a.shot_every and t >= next_shot:
                png = a.output / f"shot-{int(t):04d}s.png"
                subprocess.run(["import", "-display", a.display, "-window", "root", str(png)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
                if png.exists():
                    shots.append(png.name)
                next_shot += a.shot_every
            if t >= a.seconds:
                timed_out = True
                os.killpg(p.pid, signal.SIGKILL)
                code = p.wait()
                break
        subprocess.run([a.wine.replace("wine64", "wineserver") if "wine64" in a.wine else "wineserver", "-k"],
                       env=env, stdout=out, stderr=err, timeout=20, preexec_fn=deny_ip_sockets)
    report = {"exe": exe.name, "kind": kind, "build": build, "exe_sha256": digest, "exit_code": code,
              "timed_out": timed_out, "elapsed_seconds": round(time.monotonic() - start, 1),
              "arguments": args, "screenshots": shots,
              "socket_policy": "AF_UNIX only; IPv4/IPv6/netlink sockets and io_uring_setup refused",
              "renderer": "Wine on a virtual X display with a software GPU (Mesa llvmpipe/lavapipe)"}
    (a.output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
