"""Hand-written cases for _external/libHttpClient/Source/Global/NetworkState.cpp.

HttpCallPerformAsync's allocator, XAsyncBegin, XTaskQueueCloseHandle and its free are faked for both runs and record
what they get: the context it builds is recorded whole, as qwords, when XAsyncBegin receives it (its code pointers
compare as the original's addresses whichever copy stored them), with the identity name and provider. XAsyncBegin
succeeds or fails with various HRESULTs, and on failure may have left a task queue in the context, so the clean-up
path is driven both ways. (The allocation-failure path throws std::bad_alloc and is not run: the harness has no C++
exception support.)

Mutation check: see the commit adding this file.
"""
import random
import struct

from harness import SCRATCH, _MACHINES, program_write
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

PERFORM = "?HttpCallPerformAsync@NetworkState@httpclient@xbox@@QEAAJPEAUHC_CALL@@PEAUXAsyncBlock@@@Z"
ALLOC = "?sub_142D680C0@@YAPEAX_K@Z"
FREE = "?sub_142D680E0@@YAXPEAX@Z"
BEGIN = "XAsyncBegin"
CLOSE = "XTaskQueueCloseHandle"
CONTEXT = SCRATCH + 0x40000


def arg(mu, i):
    if i < 4:
        return mu.reg_read((UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)[i])
    return struct.unpack("<Q", bytes(mu.mem_read(mu.reg_read(UC_X86_REG_RSP) + 8 + 8 * i, 8)))[0]


def record(mu, *values):
    _MACHINES[id(mu)].observed.append(values)


def fakes(hr, queue):
    def alloc(mu):
        record(mu, "alloc", arg(mu, 0))
        mu.mem_write(CONTEXT, b"\xcd" * 0x50)  # what the allocator hands back is not zeroed
        return CONTEXT

    def begin(mu):
        ctx = arg(mu, 1)
        record(mu, "XAsyncBegin", arg(mu, 0), ctx, arg(mu, 2), _MACHINES[id(mu)].read_cstr(arg(mu, 3)), arg(mu, 4),
               *struct.unpack("<10Q", bytes(mu.mem_read(ctx, 0x50))))
        if queue:  # a queue the failed begin left behind (the internal block's queue field)
            program_write(mu, ctx + 0x18, struct.pack("<Q", queue))
        return hr

    return {
        ALLOC: alloc,
        FREE: lambda mu: record(mu, "free", arg(mu, 0)),
        BEGIN: begin,
        CLOSE: lambda mu: record(mu, "XTaskQueueCloseHandle", arg(mu, 0)),
    }


def inputs():
    r = random.Random(401)
    out = []
    for _ in range(120):
        hr = r.choice([0, 1, 0x7FFFFFFF, -0x7FFFBFFB, -0x7FF8FFF2, -1, -0x76DC_AFFF])
        queue = r.choice([0, 0, 0x7FF0_0000_1000])
        out.append({"args": [r.getrandbits(48), r.getrandbits(48), r.getrandbits(48)], "fakes": fakes(hr, queue)})
    return out


CONNECT = ("?WebSocketConnectAsync@NetworkState@httpclient@xbox@@QEAAJ$$QEAUhttp_internal_string@23@0PEAUHC_WEBSOCKET_"
           "OBSERVER@23@PEAUXAsyncBlock@@@Z")
COUNT = SCRATCH + 0x50000  # the shared_ptr's control block


def string(r, text):
    """An http_internal_string: in the small buffer (capacity 15), or on the heap (a pointer; the buffer itself is
    never read here, only moved and, when the context is destroyed, freed)."""
    if len(text) < 16 and r.random() < 0.7:
        return text.ljust(16, b"\0") + struct.pack("<QQ", len(text), 15)
    return struct.pack("<QQQQ", 0x7FF0_0020_0000 + r.getrandbits(12) * 16, 0, len(text), max(len(text), 16) | 0x1F)


def connect_fakes(hr, queue, uses):
    base = fakes(hr, queue)

    def alloc(mu):
        record(mu, "alloc", arg(mu, 0))
        mu.mem_write(CONTEXT, b"\xcd" * 0xB0)
        return CONTEXT

    def begin(mu):
        ctx = arg(mu, 1)
        record(mu, "XAsyncBegin", arg(mu, 0), ctx, arg(mu, 2), arg(mu, 3), arg(mu, 4),
               *struct.unpack("<22Q", bytes(mu.mem_read(ctx, 0xB0))), bytes(mu.mem_read(COUNT, 16)))
        if queue:
            program_write(mu, ctx + 0x68, struct.pack("<Q", queue))
        return hr

    def setup(w):
        # the control block: no vtable calls happen while the use count stays above one
        w.m.mu.mem_write(COUNT, struct.pack("<Qii", 0, uses, 1))
    return {**base, ALLOC: alloc, BEGIN: begin}, setup


def connect_inputs():
    r = random.Random(402)
    out = []
    for _ in range(160):
        hr = r.choice([0, 1, -0x7FFFBFFB, -1])
        f, setup = connect_fakes(hr, r.choice([0, 0, 0x7FF0_0000_1000]), r.choice([1, 2, 7]))
        handle = struct.pack("<QQQ", r.getrandbits(48), r.getrandbits(48), r.choice([0, COUNT, COUNT]))
        out.append({"args": [r.getrandbits(48), string(r, b"wss://rta.xboxlive.com/connect"),
                             string(r, r.choice([b"", b"rta.xboxlive.com.V2"])), handle, r.getrandbits(48)],
                    "setup": setup, "fakes": f})
    return out


CASES = [{"symbol": PERFORM, "ret": "int", "inputs": inputs()},
         {"symbol": CONNECT, "ret": "int", "inputs": connect_inputs()}]
