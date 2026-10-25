"""Run original and reconstructed x64 functions side by side in one emulator.

The original exe (verified by sha256 against target.toml) and build/recon.dll are both mapped into a single
Unicorn x86-64 address space. A call follows the Win64 calling convention, runs to a sentinel return address,
then reads RAX/XMM0 and every buffer passed by pointer. Comparing the two runs on the same inputs checks
behaviour, independent of which compiler built the reconstruction.

Ported from black-ops-1-decomp's x86-32 harness. What changed for x64 (docs/verification.md):
- Win64 arguments: position i < 4 goes in RCX/RDX/R8/R9, or XMM0..XMM3 for float/double (by position, not by
  count of each kind); later arguments on the stack above 32 bytes of shadow space; RSP is 16-byte aligned
  before the call, so RSP % 16 == 8 at entry.
- Returns in RAX, or XMM0 for float/double. No x87 state: x64 MSVC does all floating point in SSE.
- A TEB is reachable through GS (self pointer, stack base/limit for __chkstk, PEB with the image base).
- Thread-local storage: gs:[0x58] points at a one-slot TLS array whose block is a copy of the original's TLS
  template (`__declspec(thread)` variables such as dvar_modifiedFlags). The reconstruction reaches the same block,
  since its `_tls_index` and TLS offsets resolve to the original's (tools/build_recon.py). Writes to the block are
  journaled and compared like writes to globals.
- Imports: every import address table slot of the original points at a stub that returns 0, so code calling the
  OS (EnterCriticalSection, timeGetTime, ...) runs deterministically instead of faulting. A test can give a stub
  behaviour with Machine.on_import(name, fn).
- rdtsc is deterministic: a counter that restarts with every call and advances by a fixed step (time bases such as
  sys_counterBase come from it).
- Inputs can set up state first: an input may be {"args": [...], "setup": fn(writer)}; see Writer.
- Calls into the original can be observed and faked, for both runs alike: `observe` records the argument
  registers of every call to the given addresses (to check what a function passes to a callee whose effect is
  invisible, such as an empty function in this build); `fakes` replaces an original function with Python
  (fn(mu) -> return value) for state the emulator lacks (dvars that were never registered, error state).
"""
import hashlib
import math
import os
import struct
import tomllib
from pathlib import Path

import pefile
from unicorn.unicorn_py3.arch.intel import HOOK_INSN_CPUID_CFUNC  # rdtsc hooks share the cpuid callback type
from unicorn.unicorn_py3.unicorn import uccallback
from unicorn import UC_ARCH_X86, UC_HOOK_CODE, UC_HOOK_INSN, UC_HOOK_MEM_WRITE, UC_MODE_64, Uc, UcError
from unicorn import x86_const
from unicorn.x86_const import (UC_X86_REG_RIP, UC_X86_INS_RDTSC, UC_X86_INS_RDTSCP, UC_X86_REG_MXCSR, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RAX, UC_X86_REG_RBP,
                               UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP, UC_X86_REG_XMM0,
                               UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3)

ROOT = Path(__file__).resolve().parents[2]
STACK, STACK_SIZE = 0x00100000, 0x00100000
HEAP, HEAP_SIZE = 0x00300000, 0x00100000
SENTINEL = 0x00200000
TEB = 0x00400000
TLS_BLOCK = 0x00410000
STUBS, STUBS_SIZE = 0x00420000, 0x00010000
SCRATCH, SCRATCH_SIZE = 0x00500000, 0x00100000
INT_REGS = (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)
RESET_REGS = [getattr(x86_const, f"UC_X86_REG_{n}") for n in (
    "RAX", "RBX", "RCX", "RDX", "RSI", "RDI", "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15",
    *(f"XMM{i}" for i in range(16)))]
XMM_REGS = (UC_X86_REG_XMM0, UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3)
MASK64 = (1 << 64) - 1


def _page(n):
    return (n + 0xFFF) & ~0xFFF


class Image:
    def __init__(self, path: Path):
        self.pe = pefile.PE(str(path), fast_load=True)
        self.pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY[d] for d in (
            "IMAGE_DIRECTORY_ENTRY_EXPORT", "IMAGE_DIRECTORY_ENTRY_IMPORT", "IMAGE_DIRECTORY_ENTRY_TLS")])
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.size = _page(self.pe.OPTIONAL_HEADER.SizeOfImage)
        self.data = self.pe.get_memory_mapped_image()
        self.exports = {}
        if hasattr(self.pe, "DIRECTORY_ENTRY_EXPORT"):
            for e in self.pe.DIRECTORY_ENTRY_EXPORT.symbols:
                self.exports[e.name.decode()] = self.base + e.address
        # import address table slots: va -> "dll!name"
        self.iat = {}
        for d in getattr(self.pe, "DIRECTORY_ENTRY_IMPORT", []):
            for imp in d.imports:
                name = imp.name.decode() if imp.name else f"#{imp.ordinal}"
                self.iat[imp.address] = f"{d.dll.decode().lower()}!{name}"
        self.rdata = [(self.base + sec.VirtualAddress, self.base + sec.VirtualAddress + sec.Misc_VirtualSize)
                      for sec in self.pe.sections if sec.Name.rstrip(b"\0") == b".rdata"]
        self.tls = None  # (template bytes, va of the TLS index variable)
        if hasattr(self.pe, "DIRECTORY_ENTRY_TLS"):
            t = self.pe.DIRECTORY_ENTRY_TLS.struct
            start, end = t.StartAddressOfRawData - self.base, t.EndAddressOfRawData - self.base
            self.tls = (bytes(self.data[start:end]) + b"\0" * t.SizeOfZeroFill, t.AddressOfIndex)


def reference_build() -> str:
    """The build tests run against: the first reference build with a MAP in target.toml, or the first retail build
    when there is none (BO3)."""
    cfg = tomllib.loads((ROOT / "target.toml").read_text())
    builds = cfg.get("build", [])
    ref = next((b["id"] for b in builds if b.get("kind") == "reference" and "map" in b), None)
    return ref or next(b["id"] for b in builds if b.get("kind") == "retail")


def original_exe(build: str | None = None) -> Path:
    """Locate the original exe: $T7_ORIGINALS/<build>.exe, verified against target.toml."""
    build = build or reference_build()
    cfg = tomllib.loads((ROOT / "target.toml").read_text())
    spec = next(b for b in cfg["build"] if b["id"] == build)
    # Arxan-protected builds are tested from their unpacked image (tools/unpack/arxan.py)
    want = spec.get("unpacked_sha256") or spec["exe"]["sha256"]
    path = Path(os.environ.get("T7_ORIGINALS", ROOT / ".work" / "originals")) / f"{build}.exe"
    if not path.exists():
        raise SystemExit(f"missing {path}: run tools/fetch_originals.py {build} {path.parent}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != want:
        raise SystemExit(f"{path} does not match target.toml sha256")
    return path


def _is_float(a):
    return isinstance(a, tuple) and a[0] in ("f", "d")


def _float_bits(a) -> int:
    return struct.unpack("<I", struct.pack("<f", a[1]))[0] if a[0] == "f" else struct.unpack("<Q", struct.pack("<d", a[1]))[0]


def _xmm_double(mu):
    return struct.unpack("<d", struct.pack("<Q", mu.reg_read(UC_X86_REG_XMM0) & MASK64))[0]


def _xmm_float(mu):
    return struct.unpack("<f", struct.pack("<I", mu.reg_read(UC_X86_REG_XMM0) & 0xFFFFFFFF))[0]


def _ret_double(mu, x):
    mu.reg_write(UC_X86_REG_XMM0, struct.unpack("<Q", struct.pack("<d", x))[0])


def _ret_float(mu, x):
    mu.reg_write(UC_X86_REG_XMM0, struct.unpack("<I", struct.pack("<f", x))[0])


def _rounding(fn, single):
    """A CRT rounding function: exact, and NaN/inf/huge values pass through as in the CRT."""
    def run(mu):
        x = _xmm_float(mu) if single else _xmm_double(mu)
        y = x if (math.isnan(x) or math.isinf(x) or abs(x) >= 2.0 ** 52) else float(fn(x))
        if y == 0.0:
            y = math.copysign(0.0, x)
        (_ret_float if single else _ret_double)(mu, y)
    return run


def _sqrt(single):
    def run(mu):
        x = _xmm_float(mu) if single else _xmm_double(mu)
        # a negative input gives the x64 default NaN (sign set), as sqrtss/sqrtsd and the CRT do
        y = math.sqrt(x) if x >= 0 or math.isnan(x) else -float("nan")
        (_ret_float if single else _ret_double)(mu, y)
    return run


def _atan2(single):
    """atan2(y in xmm0, x in xmm1). Not bit-exact with the CRT, but deterministic: both runs reach the same stub,
    so callers are compared on real angles instead of on whatever xmm0 held."""
    def run(mu):
        if single:
            y, x = (struct.unpack("<f", struct.pack("<I", mu.reg_read(r) & 0xFFFFFFFF))[0] for r in XMM_REGS[:2])
        else:
            y, x = (struct.unpack("<d", struct.pack("<Q", mu.reg_read(r) & MASK64))[0] for r in XMM_REGS[:2])
        (_ret_float if single else _ret_double)(mu, math.atan2(y, x))
    return run


def _unary(fn, single):
    """A one-argument CRT math routine (tan, sin, ...): Python's libm result, not necessarily bit-exact with the
    CRT, but both runs reach the same stub, so callers are compared on real values."""
    def run(mu):
        x = _xmm_float(mu) if single else _xmm_double(mu)
        try:
            y = fn(x)
        except (ValueError, OverflowError):
            y = float("nan")
        (_ret_float if single else _ret_double)(mu, y)
    return run


# CRT routines a build imports (the Store build links the CRT dynamically): exact Python versions, so code that
# rounds or takes square roots through an import gets real results. Both runs reach the same stub.
CRT_IMPORTS = {
    "floor": _rounding(math.floor, False), "floorf": _rounding(math.floor, True),
    "ceil": _rounding(math.ceil, False), "ceilf": _rounding(math.ceil, True),
    "sqrt": _sqrt(False), "sqrtf": _sqrt(True),
    "atan2": _atan2(False), "atan2f": _atan2(True),
    **{name + suffix: _unary(getattr(math, name), suffix == "f")
       for name in ("tan", "sin", "cos", "atan", "asin", "acos", "exp", "log") for suffix in ("", "f")},
}


def _ctype(fn):
    """A <ctype.h> routine in the C locale (the game never calls setlocale): fn(c) for 0..255, the argument
    unchanged otherwise (EOF, and the sign-extended chars that are undefined behaviour to pass)."""
    def run(mu):
        c = mu.reg_read(UC_X86_REG_RCX) & 0xFFFFFFFF
        c = c - (1 << 32) if c & 0x80000000 else c
        mu.reg_write(UC_X86_REG_RAX, (fn(c) if 0 <= c <= 255 else c) & 0xFFFFFFFF)
    return run


CTYPE_IMPORTS = {
    "tolower": _ctype(lambda c: c + 32 if 65 <= c <= 90 else c),
    "toupper": _ctype(lambda c: c - 32 if 97 <= c <= 122 else c),
    "isdigit": _ctype(lambda c: 4 if 48 <= c <= 57 else 0),  # the UCRT's _DIGIT mask
    "isalpha": _ctype(lambda c: 0x101 if 65 <= c <= 90 else 0x102 if 97 <= c <= 122 else 0),  # _UPPER|_ALPHA, _LOWER|_ALPHA
}


class Writer:
    """Sets up state for one call: writes into the images are undone afterwards, and scratch memory
    (strings, argv arrays) is handed out from a region cleared before every call."""

    def __init__(self, machine):
        self.m = machine
        self.next = SCRATCH

    def write(self, va, data: bytes):
        self.m._setup_write(va, bytes(data))

    def u32(self, va, v):
        self.write(va, struct.pack("<I", v & 0xFFFFFFFF))

    def u64(self, va, v):
        self.write(va, struct.pack("<Q", v & MASK64))

    def alloc(self, data: bytes) -> int:
        va = self.next
        self.m.mu.mem_write(va, bytes(data))
        self.next = (va + len(data) + 15) & ~15
        return va

    def cstr(self, s: str | bytes) -> int:
        return self.alloc((s.encode("latin1") if isinstance(s, str) else s) + b"\0")  # one byte per char


_MACHINES = {}


def program_write(mu, va, data):
    """For a fake standing in for a function: write `data` at `va` on the program's behalf, journaled like the
    emulated code's own writes, so a write into the original's globals is compared and rolled back. (A plain
    mu.mem_write is invisible to the comparison.)"""
    _MACHINES[id(mu)]._emulated_write(va, data)


class Machine:
    def __init__(self, *images: Image):
        self.mu = Uc(UC_ARCH_X86, UC_MODE_64)
        _MACHINES[id(self.mu)] = self
        for img in images:
            self.mu.mem_map(img.base, img.size)
            self.mu.mem_write(img.base, img.data[:img.size])
        self.mu.mem_map(STACK, STACK_SIZE)
        self.mu.mem_map(HEAP, HEAP_SIZE)
        self.mu.mem_map(SENTINEL, 0x1000)
        # The bytes before the return address look like `call rel32`, as at any real call site: the game's
        # obfuscated pointer and dvar decoders inspect their caller's bytes and never finish when the call site
        # doesn't look like a call (docs/obfuscation.md).
        self.mu.mem_write(SENTINEL - 5, b"\xe8\x00\x00\x00\x00")
        self.mu.mem_map(TEB, 0x10000)
        self.mu.mem_write(TEB + 0x08, struct.pack("<Q", STACK + STACK_SIZE))  # NT_TIB.StackBase
        self.mu.mem_write(TEB + 0x10, struct.pack("<Q", STACK))               # NT_TIB.StackLimit
        self.mu.mem_write(TEB + 0x30, struct.pack("<Q", TEB))                 # NT_TIB.Self
        self.mu.mem_write(TEB + 0x60, struct.pack("<Q", TEB + 0x2000))        # PEB
        if images:
            self.mu.mem_write(TEB + 0x2000 + 0x10, struct.pack("<Q", images[0].base))  # PEB.ImageBaseAddress
        self.mu.msr_write(0xC0000101, TEB)                                    # IA32_GS_BASE
        # TLS: gs:[0x58] -> [block]; the original's TLS index variable stays 0, the slot the loader gives an exe
        self.mu.mem_map(TLS_BLOCK, 0x10000)
        self.mu.mem_write(TEB + 0x58, struct.pack("<Q", TEB + 0x3000))
        self.mu.mem_write(TEB + 0x3000, struct.pack("<Q", TLS_BLOCK))
        if images and images[0].tls:
            self.mu.mem_write(TLS_BLOCK, images[0].tls[0])
        # import stubs: `xor eax, eax; ret`, with Python behaviour hooked on the ret
        self.mu.mem_map(STUBS, STUBS_SIZE)
        self.mu.mem_map(SCRATCH, SCRATCH_SIZE)
        self._stub_names, self._import_fns = {}, {}
        for img in images:
            for slot, name in img.iat.items():
                stub = STUBS + 0x10 * len(self._stub_names)
                self._stub_names[stub + 2] = name
                self.mu.mem_write(stub, b"\x31\xc0\xc3")
                self.mu.mem_write(slot, struct.pack("<Q", stub))
        self.mu.hook_add(UC_HOOK_CODE, self._on_stub, begin=STUBS, end=STUBS + STUBS_SIZE - 1)
        for name in self._stub_names.values():
            if name.split("!", 1)[1] in CRT_IMPORTS and name.startswith("api-ms-win-crt-math"):
                self._import_fns[name.lower()] = CRT_IMPORTS[name.split("!", 1)[1]]
            elif name.split("!", 1)[1] in CTYPE_IMPORTS and name.startswith("api-ms-win-crt-string"):
                self._import_fns[name.lower()] = CTYPE_IMPORTS[name.split("!", 1)[1]]
            # memory routines (VCRUNTIME140.dll in the Store build) really copy and fill, with their writes journaled
            # like an instruction's, so they are compared and rolled back
            elif name.split("!", 1)[1] in ("memcpy", "memmove"):
                self._import_fns[name.lower()] = self._memmove
            elif name.split("!", 1)[1] == "memset":
                self._import_fns[name.lower()] = self._memset
        self.imports_called = []
        # Writes into any mapped image (the original's globals) are journaled so each call can be
        # rolled back and its side effects compared: see call().
        self.images = images
        self._ranges = [(img.base, img.base + img.size) for img in images] + [(TLS_BLOCK, TLS_BLOCK + 0x10000)]
        self._journal = {}
        self._setup_journal = {}
        self.mu.hook_add(UC_HOOK_MEM_WRITE, self._on_write)
        self.tsc = 0
        self._hooked, self._fakes, self._observe, self.observed = set(), {}, {}, []
        self._rdtsc_cb = uccallback(self.mu, HOOK_INSN_CPUID_CFUNC)(self._on_rdtsc)
        for insn in (UC_X86_INS_RDTSC, UC_X86_INS_RDTSCP):
            self.mu._Uc__do_hook_add(UC_HOOK_INSN, self._rdtsc_cb, 1, 0, insn)

    def _on_rdtsc(self, mu, user):
        self.tsc += 0x400
        mu.reg_write(UC_X86_REG_RAX, self.tsc & 0xFFFFFFFF)
        mu.reg_write(UC_X86_REG_RDX, self.tsc >> 32)
        return 1  # skip the real instruction

    def _on_write(self, mu, access, address, size, value, user):
        for lo, hi in self._ranges:
            if lo <= address < hi:
                for a in range(address, address + size):
                    if a not in self._journal:
                        self._journal[a] = bytes(mu.mem_read(a, 1))
                return

    def _emulated_write(self, va, data):
        """A write made for the program by Python (an import such as memcpy): journaled as _on_write does."""
        for lo, hi in self._ranges:
            a0, a1 = max(va, lo), min(va + len(data), hi)
            if a0 < a1:
                old = bytes(self.mu.mem_read(a0, a1 - a0))
                for i in range(a1 - a0):
                    self._journal.setdefault(a0 + i, old[i:i + 1])
        self.mu.mem_write(va, bytes(data))

    def _memmove(self, mu):
        dst, src, n = mu.reg_read(UC_X86_REG_RCX), mu.reg_read(UC_X86_REG_RDX), mu.reg_read(UC_X86_REG_R8)
        if n:
            self._emulated_write(dst, mu.mem_read(src, n))
        mu.reg_write(UC_X86_REG_RAX, dst)

    def _memset(self, mu):
        dst, c, n = mu.reg_read(UC_X86_REG_RCX), mu.reg_read(UC_X86_REG_RDX) & 0xFF, mu.reg_read(UC_X86_REG_R8)
        if n:
            self._emulated_write(dst, bytes([c]) * n)
        mu.reg_write(UC_X86_REG_RAX, dst)

    def _setup_write(self, va, data):
        for i in range(len(data)):
            if va + i not in self._setup_journal:
                self._setup_journal[va + i] = bytes(self.mu.mem_read(va + i, 1))
        self.mu.mem_write(va, data)

    def read_cstr(self, va, limit=512):
        try:
            data = bytes(self.mu.mem_read(va, limit))
        except UcError:
            return f"<unreadable {va:#x}>"
        return data.split(b"\0", 1)[0]

    def import_stub(self, name):
        """Entry address of the stub behind import `name` ("api-ms-win-crt-time-l1-1-0.dll!_time64", any case), or
        None. Fakes and observations keyed by an import name hook here, so they see every caller: the original
        calls the stub through its IAT slot, and the reconstruction through the same slot (hybrid link)."""
        if not hasattr(self, "_stub_by_name"):
            self._stub_by_name = {n.lower(): a - 2 for a, n in self._stub_names.items()}
        return self._stub_by_name.get(name.lower())

    def on_import(self, name, fn):
        """fn(mu) runs when the original calls import `name` ("user32.dll!GetCursorPos"); it may set RAX and
        write through the argument registers. Without one, an import returns 0."""
        self._import_fns[name.lower()] = fn

    def _on_stub(self, mu, address, size, user):
        name = self._stub_names.get(address)
        if name is None:
            return
        self.imports_called.append(name)
        fn = self._import_fns.get(name.lower())
        if fn:
            fn(mu)

    def poke(self, va, data: bytes):
        self.mu.mem_write(va, data)

    def _hook_at(self, va):
        if va not in self._hooked:
            self._hooked.add(va)
            self.mu.hook_add(UC_HOOK_CODE, self._on_hooked, begin=va, end=va)

    def _on_hooked(self, mu, address, size, user):
        spec = self._observe.get(address)
        if spec is not None:
            # spec: one letter per argument: b = bool/char (low byte; the rest of the register is undefined),
            # i = 32-bit integer, q = 64-bit, f = float, s = C string pointer
            # arguments past the fourth are read from the stack: at the entry [rsp] is the return address, then
            # 32 bytes of shadow space (a float there is read as its 32-bit pattern too)
            got = []
            rsp = mu.reg_read(UC_X86_REG_RSP)
            for i, kind in enumerate(spec):
                if i < 4:
                    raw = mu.reg_read(XMM_REGS[i]) if kind == "f" else mu.reg_read(INT_REGS[i])
                else:
                    raw = struct.unpack("<Q", bytes(mu.mem_read(rsp + 8 + 8 * i, 8)))[0]
                if kind == "f":
                    got.append(raw & 0xFFFFFFFF)
                elif kind == "s":
                    got.append(self.read_cstr(raw))
                else:
                    got.append(raw & {"q": MASK64, "b": 0xFF}.get(kind, 0xFFFFFFFF))
            self.observed.append((address, *got))
        fn = self._fakes.get(address)
        if fn:
            value = fn(mu)
            rsp = mu.reg_read(UC_X86_REG_RSP)
            ret = struct.unpack("<Q", bytes(mu.mem_read(rsp, 8)))[0]
            if value is not None:
                mu.reg_write(UC_X86_REG_RAX, value & MASK64)
            mu.reg_write(UC_X86_REG_RSP, rsp + 8)
            mu.reg_write(UC_X86_REG_RIP, ret)

    def call(self, va, args, ret="int", setup=None, fakes=None, observe=None):
        """args: ints, floats ('f', x), doubles ('d', x), or bytes (passed by pointer, read back after).
        ret: int (32-bit), int64, char, short, float, double, void, or cstr (a returned char pointer, compared as
        the string it points to: a string literal lives at different addresses in the original and the
        reconstruction).

        Returns (return value, [buffer contents after the call], {address: byte} written in mapped images,
        [observed calls]).
        Image writes are rolled back afterwards, so calls never see each other's state.
        A crash returns ("fault: ...", [], writes)."""
        mu = self.mu
        mu.mem_write(HEAP, b"\0" * HEAP_SIZE)
        mu.mem_write(SCRATCH, b"\0" * SCRATCH_SIZE)
        self._setup_journal = {}
        self.imports_called = []
        self.tsc = 0x100000000
        self._fakes, self._observe, self.observed = dict(fakes or {}), dict(observe or {}), []
        for a in list(self._fakes) + list(self._observe):
            self._hook_at(a)
        if setup:
            setup(Writer(self))
        heap = HEAP
        slots, bufs = [], []  # slot: (is_float, 64-bit value)
        for a in args:
            if isinstance(a, (bytes, bytearray)):
                mu.mem_write(heap, bytes(a))
                bufs.append((heap, len(a)))
                slots.append((False, heap))
                heap += _page(len(a) + 16)
            elif _is_float(a):
                slots.append((True, _float_bits(a)))
            else:
                slots.append((False, a & MASK64))
        # every call starts from the same registers, so nothing left over from an earlier call can differ
        for r in RESET_REGS:
            mu.reg_write(r, 0)
        # stack: [ret][shadow 4x8][arg5][arg6]... ; RSP % 16 == 8 at entry
        nstack = max(0, len(slots) - 4)
        top = STACK + STACK_SIZE - 0x100
        sp = (top - (8 + 0x20 + 8 * nstack)) & ~0xF
        sp -= 8
        mu.mem_write(sp, struct.pack("<Q", SENTINEL))
        for i, (_, v) in enumerate(slots[4:]):
            mu.mem_write(sp + 8 + 0x20 + 8 * i, struct.pack("<Q", v))
        for i, (isf, v) in enumerate(slots[:4]):
            if isf:
                mu.reg_write(XMM_REGS[i], v)
            # MSVC also passes floating-point values of varargs in the integer register; harmless otherwise
            mu.reg_write(INT_REGS[i], v)
        mu.reg_write(UC_X86_REG_RSP, sp)
        mu.reg_write(UC_X86_REG_RBP, 0)
        mu.reg_write(UC_X86_REG_MXCSR, 0x1F80)  # all SSE exceptions masked, round to nearest
        self._journal = {}
        try:
            mu.emu_start(va, SENTINEL, count=2_000_000)
            fault = None
        except UcError as e:
            fault = f"fault: {e} at {mu.reg_read(UC_X86_REG_RIP):#x}"
        # Net changes only (storing the value a byte already had is not a behavioural difference), reported as
        # whole aligned qwords, so a stored pointer can be recognised (run.py normalize_writes).
        changed = {a & ~7 for a in self._journal if bytes(mu.mem_read(a, 1)) != self._journal[a]}
        globals_written = {a + i: bytes(mu.mem_read(a + i, 1)) for a in sorted(changed) for i in range(8)}
        returned_str = None
        if ret == "cstr" and not fault:
            ptr = mu.reg_read(UC_X86_REG_RAX)
            returned_str = self.read_cstr(ptr) if ptr else None  # before rollback: it may point at a written global
        for a, old in self._journal.items():
            mu.mem_write(a, old)
        for a, old in self._setup_journal.items():
            mu.mem_write(a, old)
        self._journal = {}
        self._setup_journal = {}
        observed, self._fakes, self._observe = self.observed, {}, {}
        if fault:
            return fault, [], globals_written, observed
        rax = mu.reg_read(UC_X86_REG_RAX)
        xmm0 = mu.reg_read(UC_X86_REG_XMM0)
        eax = rax & 0xFFFFFFFF
        value = {
            "int": eax if eax < 1 << 31 else eax - (1 << 32),
            "int64": rax if rax < 1 << 63 else rax - (1 << 64),
            "char": struct.unpack("<b", bytes([rax & 0xFF]))[0],
            "short": struct.unpack("<h", struct.pack("<H", rax & 0xFFFF))[0],
            "float": struct.unpack("<f", struct.pack("<I", xmm0 & 0xFFFFFFFF))[0],
            "double": struct.unpack("<d", struct.pack("<Q", xmm0 & MASK64))[0],
            "void": None,
            "cstr": None,
        }[ret]
        if ret == "cstr":
            value = returned_str
        return value, [bytes(mu.mem_read(a, n)) for a, n in bufs], globals_written, observed
