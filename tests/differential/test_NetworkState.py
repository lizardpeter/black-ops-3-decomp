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


CASES = [{"symbol": PERFORM, "ret": "int", "inputs": inputs()}]
