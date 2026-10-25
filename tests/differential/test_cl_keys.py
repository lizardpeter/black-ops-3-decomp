"""Hand-written cases for client/cl_keys.cpp.

sub_1413ED0D0: the two local clients' bindings-modified flags (0, 1, other values) are set per case; va is faked to
return a name per case (short, exactly 259 and 260+ characters, or null), sub_1423B4570 and sub_1413ECF90 are faked
and observed with the buffer's contents, so the copied name, the cut at 259 characters, the order of calls and the
flags left behind are compared.

Mutation check: see the commit adding this file.
"""
import random
import struct

import syms
from harness import SCRATCH, _MACHINES
from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8

SYM = "?sub_1413ED0D0@@YAXXZ"
NAMES = SCRATCH + 0x60000


def _record(mu, *values):
    _MACHINES[id(mu)].observed.append(values)


def _va(results):
    def fn(mu):
        m = _MACHINES[id(mu)]
        _record(mu, "va", m.read_cstr(mu.reg_read(UC_X86_REG_RCX)), m.read_cstr(mu.reg_read(UC_X86_REG_RDX)),
                mu.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF)
        return results[mu.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF]
    return fn


def _name(mu, address):
    """The buffer up to its terminator (the bytes after it are the stack's, unwritten)."""
    data = bytes(mu.mem_read(address, 0x104))
    end = data.find(b"\0")
    return data if end < 0 else data[:end + 1]


def _buffer(name):
    def fn(mu):
        m = _MACHINES[id(mu)]
        regs = [mu.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX)]
        if name == "sub_1423B4570":
            _record(mu, name, _name(mu, regs[0]), regs[1] & 0xFFFFFFFF)
        else:
            _record(mu, name, regs[0] & 0xFFFFFFFF, _name(mu, regs[1]))
        return None
    return fn


def inputs():
    r = random.Random(1413)
    out = []
    for _ in range(120):
        flags = [r.choice([0, 1, 1, 2, -1]) for _ in range(2)]
        names = []
        for i in range(2):
            length = r.choice([5, 10, 258, 259, 260, 300])
            names.append(r.choice([None, bytes(r.randrange(33, 127) for _ in range(length))]) if r.random() < 0.2
                         else bytes(r.randrange(33, 127) for _ in range(length)))

        def setup(w, flags=flags, names=names):
            for i, flag in enumerate(flags):
                w.u32(syms.va("key_bindingsModified") + 0x1940 * i, flag)
            for i, name in enumerate(names):
                if name is not None:
                    w.m.mu.mem_write(NAMES + 0x200 * i, name + b"\0")

        results = [0 if names[i] is None else NAMES + 0x200 * i for i in range(2)]
        out.append({"args": [], "setup": setup,
                    "fakes": {"va": _va(results), "sub_1423B4570": _buffer("sub_1423B4570"),
                              "sub_1413ECF90": _buffer("sub_1413ECF90")}})
    return out


CASES = [{"symbol": SYM, "ret": "void", "inputs": inputs()}]
