"""Hand-written cases for win32/crash_report.cpp (the Store port's crash reporter).

sub_1423B9DE0 is all decisions around four calls, so the cases drive every input those decisions read and compare
the calls it makes:

- the module's statics: the signature (empty or set), the last report time, and the three dvar pointers (null,
  or a sentinel that the faked Dvar_GetBool / Dvar_GetFloat answer for);
- the imports, faked identically for both copies: `_time64` (a chosen "now", also stored through its argument),
  `rand` (values either side of the 0.05 sample threshold), and real `strrchr`, `_strdup` and `strncpy`;
- the two senders it calls, faked (they would touch the registry, curl and the file system) and observed with
  their string arguments, so the file name it derives (path stripped, '#' replaced, ".log" suffix) is compared.

Mutation check: see the commit adding this file (11 mutations, all killed).
"""
import random
import struct

from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_XMM0

import syms
from harness import program_write

SYM = "?sub_1423B9DE0@@YA_NPEBD00@Z"
SEND_EVENT = "?sub_1423B87C0@@YA_NPEBD@Z"
WRITE_REPORT = "?sub_1423B8BA0@@YA_NPEBD00@Z"
TIME = "api-ms-win-crt-time-l1-1-0.dll!_time64"
RAND = "api-ms-win-crt-utility-l1-1-0.dll!rand"
STRRCHR = "vcruntime140.dll!strrchr"
STRDUP = "api-ms-win-crt-string-l1-1-0.dll!_strdup"
STRNCPY = "api-ms-win-crt-string-l1-1-0.dll!strncpy"

ENABLE, UPLOAD, RATE = 0x1111_0000, 0x2222_0000, 0x3333_0000
DUP_AREA = 0x0058_0000  # inside the harness's scratch region, cleared before every call


def cstr_at(mu, va, limit=512):
    data = bytes(mu.mem_read(va, limit))
    return data.split(b"\0", 1)[0]


def ret(value):
    def fn(mu):
        return value
    return fn


def fake_time(now):
    def fn(mu):
        p = mu.reg_read(UC_X86_REG_RCX)
        if p:
            program_write(mu, p, struct.pack("<q", now))
        return now & 0xFFFFFFFFFFFFFFFF
    return fn


def fake_strrchr(mu):
    s, c = mu.reg_read(UC_X86_REG_RCX), mu.reg_read(UC_X86_REG_RDX) & 0xFF
    if not s:
        return 0
    text = cstr_at(mu, s) + b"\0"
    i = text.rfind(bytes([c]))
    return s + i if i >= 0 else 0


def fake_strdup(mu):
    s = mu.reg_read(UC_X86_REG_RCX)
    if not s:
        return 0
    mu.mem_write(DUP_AREA, cstr_at(mu, s) + b"\0")
    return DUP_AREA


def fake_strncpy(mu):
    dst, src, n = (mu.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8))
    data = cstr_at(mu, src)[:n]
    mu.mem_write(dst, data + b"\0" * (n - len(data)))
    return dst


def fake_bool(enable, upload):
    def fn(mu):
        return {ENABLE: enable, UPLOAD: upload}.get(mu.reg_read(UC_X86_REG_RCX), 0x5A)
    return fn


def fake_float(rate):
    def fn(mu):
        mu.reg_write(UC_X86_REG_XMM0, struct.unpack("<I", struct.pack("<f", rate))[0])
        return None
    return fn


def setup(signature, last, enable, upload, rate):
    def apply(w):
        w.write(syms.va("s_crashSignature"), signature.ljust(34, b"\0")[:34])
        w.u64(syms.va("s_lastCrashReportTime"), last)
        w.u64(syms.va("s_crashReportEnable"), ENABLE if enable is not None else 0)
        w.u64(syms.va("s_crashReportUploadLog"), UPLOAD if upload is not None else 0)
        w.u64(syms.va("s_crashReportSampleRate"), RATE if rate is not None else 0)
    return apply


PATHS = [b"C:\\Users\\p\\crash_reports\\BlackOps3_20261024#1.dmp", b"dump#2.dmp", b"plain.dmp",
         b"C:\\a\\b\\no_hash_here.dmp", b"\\lead.dmp", b"C:\\x#y\\z#w.dmp", b"#####.dmp"]


def inputs():
    r = random.Random(7)
    out = []
    for i in range(240):
        now = 1_800_000_000 + r.randint(0, 5000)
        last = now - r.choice([0, 1, 599, 600, 601, 100000, -5, now])
        signature = r.choice([b"", b"0123456789abcdef0123456789abcdef", b"x"])
        enable = r.choice([None, 0, 1])
        upload = r.choice([None, 0, 1])
        rate = r.choice([None, 0.0, 0.05, 1.0, float("nan"), -1.0, 0.5])
        rnd = r.choice([0, 1, 1638, 1639, 16384, 32767])
        first, second = r.choice([0, 1]), r.choice([0, 1])
        if i < 120:  # most cases get past the early returns, so the later decisions are reached often
            signature, last = b"0123456789abcdef0123456789abcdef", now - 1000
        out.append({
            "args": [r.choice(PATHS) + b"\0", b"C:\\logs\\console.log\0", r.choice([b"xbox", b"pc", b""]) + b"\0"],
            "setup": setup(signature, last & 0xFFFFFFFFFFFFFFFF, enable, upload, rate),
            "fakes": {
                TIME: fake_time(now), RAND: ret(rnd), STRRCHR: fake_strrchr, STRDUP: fake_strdup,
                STRNCPY: fake_strncpy, "?Dvar_GetBool@@YA_NPEBUdvar_t@@@Z": fake_bool(enable, upload),
                "?Dvar_GetFloat@@YAMPEBUdvar_t@@@Z": fake_float(rate if rate is not None else 0.0),
                SEND_EVENT: ret(1), WRITE_REPORT: _report_results(first, second),
            },
        })
    return out


def _report_results(first, second):
    """The dump report gets `first`, the log report (its name ends in .log) `second`: decided by the argument, not
    by a call count, so the original's run and the reconstruction's see the same answers."""
    def fn(mu):
        return second if cstr_at(mu, mu.reg_read(UC_X86_REG_RDX)).endswith(b".log") else first
    return fn


CASES = [{
    "symbol": SYM, "ret": "char", "inputs": inputs(),
    "observe": {SEND_EVENT: "s", WRITE_REPORT: "sss", TIME: "", "?Dvar_GetBool@@YA_NPEBUdvar_t@@@Z": "q",
                "?Dvar_GetFloat@@YAMPEBUdvar_t@@@Z": "q", RAND: "", STRNCPY: "qsq"},
}]
