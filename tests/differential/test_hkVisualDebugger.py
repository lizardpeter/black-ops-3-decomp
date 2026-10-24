"""Hand-written cases for _external/havok/Common/Visualize/hkVisualDebugger.cpp.

serve() talks to Havok through objects: the timer sink (s_hkTimers), the socket factory (hkSocket::s_create) and the
socket it makes, whose listen and deleteThis are vtable slots. The test builds those objects in scratch memory with
vtables pointing at fake code (addresses the harness hooks), so every call serve makes is recorded with its arguments:
the timer's name and hash, the port listen gets, each string and number written to the message, the report's file and
line (with the socket's reference count at that moment, so the inlined removeReference is compared), the destructor and
deleteThis. The output stream itself is faked, so its buffer is never compared. The inputs cover a server that already
exists, a factory that returns nothing, listen failing and succeeding, and sockets that are reference counted or not.

Mutation check: see the commit adding this file.
"""
import random
import struct

import syms
from harness import SCRATCH, _MACHINES
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX

SERVE = "?serve@hkVisualDebugger@@QEAAXH@Z"
CODE = SCRATCH + 0x70000          # fake code: each entry point is hooked, never executed
TIMERS = SCRATCH + 0x71000        # the timer sink object and its vtable
SOCKET = SCRATCH + 0x72000        # the socket object and its vtable
TIMER_BEGIN, TIMER_END, CREATE, LISTEN, DELETE = (CODE + 0x10 * i for i in range(5))


def regs(mu):
    return [mu.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]


def record(mu, *values):
    _MACHINES[id(mu)].observed.append(values)


def cstr(mu, a):
    return _MACHINES[id(mu)].read_cstr(a)


def fakes(socket_made, listen_result):
    def listen(mu):
        this, result, port, _ = regs(mu)
        record(mu, "listen", this, port & 0xFFFFFFFF)
        mu.mem_write(result, struct.pack("<i", listen_result))
        return result

    return {
        TIMER_BEGIN: lambda mu: record(mu, "timerBegin", regs(mu)[0], regs(mu)[1] & 0xFFFFFFFF, cstr(mu, regs(mu)[2])),
        TIMER_END: lambda mu: record(mu, "timerEnd", regs(mu)[0]),
        CREATE: lambda mu: (record(mu, "s_create"), socket_made)[1],
        LISTEN: listen,
        DELETE: lambda mu: record(mu, "deleteThis", regs(mu)[0]),
        "sub_142A289C0": lambda mu: record(mu, "ostream", regs(mu)[2] & 0xFFFFFFFF),
        "sub_142A22450": lambda mu: (record(mu, "<<", cstr(mu, regs(mu)[1])), regs(mu)[0])[1],
        "sub_142A22520": lambda mu: (record(mu, "<<", regs(mu)[1] & 0xFFFFFFFF), regs(mu)[0])[1],
        "sub_142A28A80": lambda mu: record(mu, "~ostream"),
        "sub_142A3A300": lambda mu: record(mu, "report", regs(mu)[0] & 0xFFFFFFFF, cstr(mu, regs(mu)[2]),
                                           regs(mu)[3] & 0xFFFFFFFF,
                                           struct.unpack("<I", bytes(mu.mem_read(SOCKET + 8, 4)))[0]),
    }


def setup(refcount):
    def apply(w):
        mu = w.m.mu
        timers_vtable = TIMERS + 0x100
        mu.mem_write(TIMERS, struct.pack("<Q", timers_vtable))
        mu.mem_write(timers_vtable + 0x50, struct.pack("<QQ", TIMER_BEGIN, TIMER_END))
        socket_vtable = SOCKET + 0x100
        mu.mem_write(SOCKET, struct.pack("<QI", socket_vtable, refcount))
        mu.mem_write(socket_vtable + 0x18, struct.pack("<Q", DELETE))
        mu.mem_write(socket_vtable + 0x48, struct.pack("<Q", LISTEN))
        w.u64(syms.va("s_hkTimers"), TIMERS)
        w.u64(syms.va("hkSocket::s_create"), CREATE)
    return apply


def inputs():
    r = random.Random(501)
    out = []
    for _ in range(160):
        debugger = bytearray(r.randbytes(0x18))
        debugger[0x10:0x18] = struct.pack("<Q", r.choice([0, 0, 0, 0x7FF0_0000_5000]))
        refcount = r.choice([0x0010_0001, 0x0010_0002, 0x0000_0001, 0x0010_0000, 0xFFFF_0001])
        out.append({"args": [bytes(debugger), r.choice([25001, 0, -1, 80])], "setup": setup(refcount),
                    "fakes": fakes(r.choice([SOCKET, SOCKET, 0]), r.choice([0, 1, -1]))})
    return out


CASES = [{"symbol": SERVE, "ret": "void", "inputs": inputs()}]
