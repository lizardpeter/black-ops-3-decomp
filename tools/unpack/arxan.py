#!/usr/bin/env python3
"""Decrypt an Arxan-protected retail exe by emulating its entry stub, and write the decrypted image as a PE.

    python3 tools/unpack/arxan.py <build-id> <packed.exe> <unpacked.exe> <report-dir>

The IW6 (Ghosts) Steam exes ship with `.text` encrypted. At process start the entry stub (code in `.reloc` and
`.interpr`) makes the image writable, decrypts `.text` in place and then runs the game's real CRT entry.
This script runs that stub in Unicorn x64 with the handful of kernel32 calls it makes answered by fixed
values, and stops when the decrypted program makes its first ordinary runtime API call. The emulation is
deterministic: `rdtsc` returns a counter that advances by a fixed step per call (the stub times itself),
so every run produces the same bytes and the output sha256 can be pinned in target.toml (unpacked_sha256).

Output:
  <unpacked.exe>                 the original file with every section whose bytes changed replaced by the
                                 emulated memory, and the entry point set to the original entry (OEP) when
                                 it was identified. Sections are written back at their raw size only.
  <report-dir>/unpack.tsv        per section: name, va, raw size, bytes changed, entropy before/after
  <report-dir>/unpack.log        API calls made by the stub, stop reason, OEP evidence, hashes

Generated output only. Claude-side bucket helpers are not part of this.
"""
import collections
import hashlib
import math
import struct
import sys
import time
import tomllib
from pathlib import Path

import pefile
from unicorn.unicorn_py3.arch.intel import HOOK_INSN_CPUID_CFUNC  # rdtsc hooks share the cpuid callback type
from unicorn.unicorn_py3.unicorn import uccallback
from unicorn import UC_ARCH_X86, UC_HOOK_CODE, UC_HOOK_INSN, UC_HOOK_MEM_UNMAPPED, UC_MODE_64, Uc, UcError
from unicorn.x86_const import (UC_X86_INS_RDTSC, UC_X86_INS_RDTSCP, UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_RDX,
                               UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RIP, UC_X86_REG_RSP)

ROOT = Path(__file__).resolve().parents[2]
STUB, STUB_SIZE = 0x7FF000000000, 0x100000      # one 16-byte 'ret' slot per imported/resolved API
STACK = 0x7FFE00000000
TEB = 0x7FFD0000
FAKE_DLL = 0x7FFA00000000
RETURN = 0xDEAD0000
TSC_STEP = 0x400                                # cycles per rdtsc: small, so timing checks always pass
# APIs the stub itself uses; the first call to anything else is the decrypted program running.
STUB_APIS = {"LoadLibraryA", "GetProcAddress", "VirtualProtect", "VirtualQuery", "GetSystemInfo"}


def entropy(b: bytes) -> float:
    if not b:
        return 0.0
    c = collections.Counter(b)
    n = len(b)
    return -sum(v / n * math.log2(v / n) for v in c.values())


class Emu:
    def __init__(self, path: Path, log):
        self.log = log
        self.pe = pefile.PE(str(path))
        oh = self.pe.OPTIONAL_HEADER
        self.base = oh.ImageBase
        self.size = (oh.SizeOfImage + 0xFFF) & ~0xFFF
        self.ep = self.base + oh.AddressOfEntryPoint
        self.secs = [(s.Name.rstrip(b"\0").decode(), self.base + s.VirtualAddress, s.Misc_VirtualSize, s)
                     for s in self.pe.sections]
        mu = self.mu = Uc(UC_ARCH_X86, UC_MODE_64)
        mu.mem_map(self.base, self.size)
        mu.mem_write(self.base, self.pe.__data__[:oh.SizeOfHeaders])
        for _, va, _, s in self.secs:
            mu.mem_write(va, s.get_data()[:s.SizeOfRawData])
        mu.mem_map(STUB, STUB_SIZE)
        mu.mem_write(STUB, b"\xC3" * STUB_SIZE)
        self.stubs = {}
        for imp in self.pe.DIRECTORY_ENTRY_IMPORT:
            for f in imp.imports:
                name = f.name.decode() if f.name else f"#{f.ordinal}"
                mu.mem_write(f.address, struct.pack("<Q", self.stub(f"{imp.dll.decode()}!{name}")))
        mu.mem_map(STACK - 0x200000, 0x400000)
        mu.reg_write(UC_X86_REG_RSP, STACK - 0x1000)
        mu.mem_write(STACK - 0x1000, struct.pack("<Q", RETURN))
        mu.mem_map(TEB, 0x10000)
        mu.mem_write(TEB + 0x30, struct.pack("<Q", TEB))
        mu.mem_write(TEB + 0x60, struct.pack("<Q", TEB + 0x2000))
        mu.mem_write(TEB + 0x2000 + 0x10, struct.pack("<Q", self.base))   # PEB.ImageBaseAddress
        mu.msr_write(0xC0000101, TEB)                                        # IA32_GS_BASE
        self.tsc = 0x100000000
        self.rdtsc_calls = 0
        self.calls = collections.Counter()
        self.stop_reason = None
        self.first_runtime_call = None
        mu.hook_add(UC_HOOK_CODE, self.on_stub, begin=STUB, end=STUB + STUB_SIZE - 1)
        # The Python binding's hook_add has no RDTSC case; register the C-level hook directly.
        self._rdtsc_cb = uccallback(mu, HOOK_INSN_CPUID_CFUNC)(self.on_rdtsc)
        for insn in (UC_X86_INS_RDTSC, UC_X86_INS_RDTSCP):
            mu._Uc__do_hook_add(UC_HOOK_INSN, self._rdtsc_cb, 1, 0, insn)
        mu.hook_add(UC_HOOK_MEM_UNMAPPED, self.on_unmapped)

    def stub(self, name):
        a = STUB + len(self.stubs) * 16
        self.stubs[a] = name
        return a

    def section_of(self, a):
        for name, va, vs, _ in self.secs:
            if va <= a < va + vs:
                return name
        return "?"

    def cstr(self, a):
        return bytes(self.mu.mem_read(a, 256)).split(b"\0")[0].decode(errors="replace")

    def on_rdtsc(self, mu, ud):
        self.tsc += TSC_STEP
        self.rdtsc_calls += 1
        mu.reg_write(UC_X86_REG_RAX, self.tsc & 0xFFFFFFFF)
        mu.reg_write(UC_X86_REG_RDX, self.tsc >> 32)
        return 1  # skip the real instruction (Unicorn advances rip)

    def on_unmapped(self, mu, access, addr, size, value, ud):
        rip = mu.reg_read(UC_X86_REG_RIP)
        self.stop_reason = f"unmapped access {access} at {addr:#x} from {rip:#x} ({self.section_of(rip)})"
        return False

    def regions(self):
        yield self.base, 0x1000, 0x02
        for _, va, vs, s in self.secs:
            yield va, (vs + 0xFFF) & ~0xFFF, 0x40

    def on_stub(self, mu, addr, size, ud):
        name = self.stubs.get(addr)
        if name is None:
            return
        fn = name.split("!", 1)[1]
        self.calls[fn] += 1
        rcx, rdx, r8, r9 = (mu.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9))
        ret, note = 0, ""
        if fn == "LoadLibraryA":
            note, ret = self.cstr(rcx), FAKE_DLL
        elif fn in ("GetModuleHandleA", "GetModuleHandleW"):
            ret = self.base if rcx == 0 else FAKE_DLL
        elif fn == "GetProcAddress":
            note = self.cstr(rdx) if rdx > 0xFFFF else f"#{rdx}"
            ret = self.stub("dyn!" + note)
        elif fn == "VirtualProtect":
            note = f"{rcx:X}+{rdx:X} -> {r8:#x}"
            if r9:
                mu.mem_write(r9, struct.pack("<I", 0x20))
            ret = 1
        elif fn == "GetSystemInfo":
            b = bytearray(48)
            struct.pack_into("<HHIQQQIIIHH", b, 0, 9, 0, 0x1000, 0x10000, 0x7FFFFFFEFFFF, 0xFF, 8, 8664, 0x10000, 6, 0x3A09)
            mu.mem_write(rcx, bytes(b))
        elif fn == "VirtualQuery":
            info = (rcx & ~0xFFF, 0, 0, 0x1000, 0x10000, 0x01, 0)          # MEM_FREE
            for lo, sz, prot in self.regions():
                if lo <= rcx < lo + sz:
                    info = (lo, self.base, 0x80, sz, 0x1000, prot, 0x1000000)  # MEM_COMMIT, MEM_IMAGE
                    break
            mu.mem_write(rdx, struct.pack("<QQIIQIII", info[0], info[1], info[2], 0, info[3], info[4], info[5], info[6]))
            ret, note = 48, f"{rcx:X}"
        if fn in STUB_APIS:
            if fn != "VirtualQuery":
                self.log(f"stub api {fn}({note})")
        else:
            caller = struct.unpack("<Q", bytes(mu.mem_read(mu.reg_read(UC_X86_REG_RSP), 8)))[0]
            self.log(f"runtime api {name} called from {caller:X} ({self.section_of(caller)})")
            self.first_runtime_call = (name, caller)
            self.stop_reason = f"first runtime API call: {name}"
            mu.emu_stop()
        mu.reg_write(UC_X86_REG_RAX, ret)

    def run(self):
        # One uninterrupted emu_start: resuming after a wall-clock timeout split the run at different
        # points each time and made the stub's result differ between runs. Stops come only from hooks.
        t0 = time.time()
        try:
            self.mu.emu_start(self.ep, RETURN)
        except UcError as e:
            self.stop_reason = self.stop_reason or f"{e} at {self.mu.reg_read(UC_X86_REG_RIP):#x}"
        if self.stop_reason is None:
            self.stop_reason = "entry stub returned"
        self.log(f"stopped after {time.time() - t0:.0f}s: {self.stop_reason}; rdtsc calls {self.rdtsc_calls}")


def find_oep(img: bytes, base: int, text_va: int, caller: int):
    """VS2012 x64 CRT entry: `sub rsp,28h; call __security_init_cookie; add rsp,28h; jmp __tmainCRTStartup`.
    The first runtime API (GetSystemTimeAsFileTime in __security_init_cookie) is called from inside the
    call target; return the entry whose call target contains `caller`."""
    pat = bytes.fromhex("4883EC28E8")
    best = None
    i = img.find(pat, text_va - base)
    while i != -1:
        if img[i + 9:i + 14] == bytes.fromhex("4883C428E9"):
            target = base + i + 9 + struct.unpack_from("<i", img, i + 5)[0]
            if target <= caller < target + 0x200 and (best is None or target > best[1]):
                best = (base + i, target)
        i = img.find(pat, i + 1)
    return best


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    build, src, dst, rdir = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
    rdir.mkdir(parents=True, exist_ok=True)
    lines = []

    def log(s):
        lines.append(s)
        print(s, flush=True)

    raw = src.read_bytes()
    log(f"input {src.name} sha256 {hashlib.sha256(raw).hexdigest()}")
    emu = Emu(src, log)
    emu.run()
    img = bytes(emu.mu.mem_read(emu.base, emu.size))

    out = bytearray(raw)
    rows = []
    for name, va, vs, s in emu.secs:
        n = min(s.SizeOfRawData, vs)
        before = raw[s.PointerToRawData:s.PointerToRawData + n]
        after = img[va - emu.base:va - emu.base + n]
        changed = sum(1 for a, b in zip(before, after) if a != b)
        rows.append([name, f"{va:09X}", f"{n:X}", str(changed), f"{entropy(before):.2f}", f"{entropy(after):.2f}"])
        if changed:
            out[s.PointerToRawData:s.PointerToRawData + n] = after
    text = next(x for x in emu.secs if x[0] == ".text")
    oep = None
    if emu.first_runtime_call:
        oep = find_oep(img, emu.base, text[1], emu.first_runtime_call[1])
    if oep:
        log(f"OEP {oep[0]:X} (CRT entry: sub rsp,28h / call {oep[1]:X} / add rsp,28h / jmp), "
            f"first runtime call returns into {emu.first_runtime_call[1]:X}")
        ep_off = emu.pe.OPTIONAL_HEADER.get_file_offset() + 16
        struct.pack_into("<I", out, ep_off, oep[0] - emu.base)
    else:
        log("OEP not identified; entry point left as the stub's")
    # the image is no longer what was signed: drop the certificate directory entry and the checksum
    sec_dir = emu.pe.OPTIONAL_HEADER.DATA_DIRECTORY[4]
    struct.pack_into("<II", out, sec_dir.__file_offset__, 0, 0)
    struct.pack_into("<I", out, emu.pe.OPTIONAL_HEADER.get_file_offset() + 64, 0)

    dst.write_bytes(out)
    h = hashlib.sha256(out).hexdigest()
    log(f"output {dst.name} sha256 {h}")
    (rdir / "unpack.tsv").write_text("section\tva\tsize\tchanged\tentropy_before\tentropy_after\n"
                                     + "".join("\t".join(r) + "\n" for r in rows))
    (rdir / "unpack.log").write_text("\n".join(lines) + "\n")

    text_row = next(r for r in rows if r[0] == ".text")
    if float(text_row[5]) > 7.2:
        sys.exit(f".text still looks encrypted (entropy {text_row[5]}): {emu.stop_reason}")
    cfg = tomllib.loads((ROOT / "target.toml").read_text())
    want = next(b for b in cfg["build"] if b["id"] == build).get("unpacked_sha256")
    if want and want != h:
        sys.exit(f"unpacked sha256 {h} differs from target.toml unpacked_sha256 {want}")
    if not want:
        print(f"note: pin this in target.toml: unpacked_sha256 = \"{h}\"")


if __name__ == "__main__":
    main()
