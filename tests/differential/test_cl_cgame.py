"""Hand-written cases for client/cl_cgame.cpp.

CL_RenderScene: a refdef in scratch with random floats at the view origin (+0x88) and axis (+0xA4); the stored origin
and forward row (cl_viewOrigin, cl_viewForward) are compared as writes, and 141DE3D80 is faked and observed with all
five arguments (the fifth from the stack), so the tail call's arguments are checked.

Mutation check: see the commit adding this file.
"""
import random
import struct

from harness import SCRATCH, _MACHINES
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

SYM = "?CL_RenderScene@@YAXPEBDHPEBX1PEAX@Z"
REFDEF = SCRATCH + 0x1000


def _scene(mu):
    sp = mu.reg_read(UC_X86_REG_RSP)
    fifth = struct.unpack("<Q", bytes(mu.mem_read(sp + 0x28, 8)))[0]
    _MACHINES[id(mu)].observed.append(("141DE3D80", mu.reg_read(UC_X86_REG_RCX), mu.reg_read(UC_X86_REG_RDX) & 0xFFFFFFFF,
                                       mu.reg_read(UC_X86_REG_R8), mu.reg_read(UC_X86_REG_R9), fifth))
    return None


def inputs():
    r = random.Random(0x1413C9540)
    out = []
    for _ in range(60):
        values = [r.uniform(-5000.0, 5000.0) if r.random() < 0.9 else r.choice([0.0, -0.0]) for _ in range(12)]

        def setup(w, values=values):
            w.m.mu.mem_write(REFDEF + 0x88, struct.pack("<12f", *values))

        view = SCRATCH + 0x2000
        cull = r.choice([view, SCRATCH + 0x3000])
        out.append({"args": [REFDEF, r.randrange(-5, 1 << 31), view, cull, r.randrange(0, 1 << 48)], "setup": setup})
    return out


CASES = [{"symbol": SYM, "ret": "void", "inputs": inputs(), "fakes": {"sub_141DE3D80": _scene}}]
