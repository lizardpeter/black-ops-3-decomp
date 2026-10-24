"""Hand-written cases for libs/DemonWareGDK/bdHTTP/bdHTTPWorker/bdHTTPWorkerWinHTTP.cpp.

initializeWinHTTP is driven through every branch: already initialized or not, network ready or not (s_networkReady),
XNetworking available or not (XGameRuntimeIsFeatureAvailable, faked: AL only, with junk in the upper bits), WinHttpOpen
failing or returning a session, WinHttpSetStatusCallback failing, returning no previous callback or a previous one, and
GetLastError codes that are zero, positive and already HRESULTs. The WinHTTP imports are faked for both runs and
record their arguments (the user agent read as UTF-16, the option's value, the callback address, which compares as
the original's 142D136B0 whichever copy passed it); every log line is recorded whole (bdlog.py). The worker object is
a buffer, so the flag and session it writes are compared.

Mutation check: see the commit adding this file.
"""
import random
import struct

import bdlog
import syms
from harness import _MACHINES
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

INIT = "?initializeWinHTTP@bdHTTPWorkerWinHTTPImpl@@QEAA_NXZ"
FEATURE = "XGameRuntimeIsFeatureAvailable"
OPEN = "winhttp.dll!WinHttpOpen"
OPTION = "winhttp.dll!WinHttpSetOption"
CALLBACK = "winhttp.dll!WinHttpSetStatusCallback"
CLOSE = "winhttp.dll!WinHttpCloseHandle"
LAST_ERROR = "kernel32.dll!GetLastError"


def arg(mu, i):
    if i < 4:
        return mu.reg_read((UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)[i])
    return struct.unpack("<Q", bytes(mu.mem_read(mu.reg_read(UC_X86_REG_RSP) + 8 + 8 * i, 8)))[0]


def wide(mu, a):
    data = bytes(mu.mem_read(a, 256))
    end = next((i for i in range(0, len(data), 2) if data[i:i + 2] == b"\0\0"), len(data))
    return data[:end].decode("utf-16-le")


def recording(name, result, describe):
    def fn(mu):
        _MACHINES[id(mu)].observed.append((name, *describe(mu)))
        return result
    return fn


def fakes(feature, session, previous, errors):
    errs = list(errors)

    def last_error(mu):
        _MACHINES[id(mu)].observed.append(("GetLastError",))
        return errs.pop(0) if errs else 0

    def reset():
        errs[:] = list(errors)

    return {
        FEATURE: recording("XGameRuntimeIsFeatureAvailable", feature, lambda mu: (arg(mu, 0) & 0xFFFFFFFF,)),
        OPEN: recording("WinHttpOpen", session, lambda mu: (wide(mu, arg(mu, 0)), arg(mu, 1) & 0xFFFFFFFF, arg(mu, 2),
                                                             arg(mu, 3), arg(mu, 4) & 0xFFFFFFFF)),
        OPTION: recording("WinHttpSetOption", 1, lambda mu: (arg(mu, 0), arg(mu, 1) & 0xFFFFFFFF,
                                                              struct.unpack("<I", bytes(mu.mem_read(arg(mu, 2), 4)))[0],
                                                              arg(mu, 3) & 0xFFFFFFFF)),
        CALLBACK: recording("WinHttpSetStatusCallback", previous, lambda mu: (arg(mu, 0), arg(mu, 1),
                                                                               arg(mu, 2) & 0xFFFFFFFF, arg(mu, 3))),
        CLOSE: recording("WinHttpCloseHandle", 1, lambda mu: (arg(mu, 0),)),
        LAST_ERROR: last_error,
        **bdlog.FAKES,
    }, reset


def setup(ready, reset):
    def apply(w):
        reset()  # the GetLastError sequence starts over for each of the two runs
        w.write(syms.va("s_networkReady"), bytes([ready]))
    return apply


def inputs():
    r = random.Random(301)
    out = []
    for i in range(300):
        worker = bytearray(r.randbytes(0xA8))
        worker[0x98] = r.choice([0, 0, 1])  # a bool: only 0 and 1 are states the game can be in
        ready = r.choice([1, 1, 0])  # a bool too
        f, reset = fakes(feature=r.choice([0, 1, 0x100, 0xFF01]),
                         session=r.choice([0, 0x0000_7FF0_0012_3400, 0x0000_7FF0_0012_3400, 1]),
                         previous=r.choice([0, 0, (1 << 64) - 1, 0x1_4000_1000]),
                         errors=[r.choice([0, 5, 12029, 0x80072EFD, 0x7FFFFFFF, 0x10005]) for _ in range(2)])
        out.append({"args": [bytes(worker)], "setup": setup(ready, reset), "fakes": f})
    return out


CASES = [{"symbol": INIT, "ret": "char", "inputs": inputs()}]
