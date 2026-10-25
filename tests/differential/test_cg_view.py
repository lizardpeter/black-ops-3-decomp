"""Hand-written cases for cgame/cg_view.cpp (the view's field of view).

sub_1405B6690 decodes the cg array pointer (149B25A20) and calls CG_CalcFOVfromLens. The original decodes inline; the
reconstruction calls the standalone decoder 141406ED0 through the exe (tools/recon/include/t7_exe_call.h). Both run
for real on the same encoded value, with the harness's PEB, and return into the exe (ret_site: the call in 140562000),
so the test also shows the two decodings agree: where each one's result appears (the original at 1405B7E4C, the copy
at its returns) it is recorded, then replaced by a cg_t placed so that the fields the function writes fall in the
exe's .data, where writes are compared. CG_CalcFOVfromLens is faked: it records the local client and the FOV it gets
and answers with per-input values, rewriting the FOV too, so every store is checked. Inputs: encoded values (zero:
no cg, the original faults and the input is skipped), local clients 0-2 against slot counts 0-2, FOVs negative
(lens), zero and positive.

Mutation check: see the commit adding this file.
"""
import random
import struct

from harness import _MACHINES
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RAX, UC_X86_REG_RBP, UC_X86_REG_RCX, \
    UC_X86_REG_RDX, UC_X86_REG_RSP

import syms

SYM = "?sub_1405B6690@@YAXHM@Z"
RET_SITE = 0x1405639E0             # after 140562000's call to 1405B6690
CG = 0x15A3F7DF0 - 0x131D68        # cg+0x131D68..0x131D77 inside .data
ENCODED = 0x149B25A20
INLINE_DONE = 0x1405B7E4C          # the original's decoded pointer is at [rbp-0x18] here
DECODER = 0x141406ED0
DECODER_RETS = [0x1414070A5, 0x141407234, 0x14140738D, 0x141407517, 0x1414076AE, 0x14140780B, 0x1414079A1,
                0x141407B11, 0x141407C98, 0x141407DDE, 0x141407F4C, 0x1414080CB, 0x141408267, 0x1414083C5,
                0x141408526, 0x141408683]


def record(mu, *values):
    _MACHINES[id(mu)].observed.append(values)


def inline_done(mu):
    slot = mu.reg_read(UC_X86_REG_RBP) - 0x18
    decoded = struct.unpack("<Q", bytes(mu.mem_read(slot, 8)))[0]
    record(mu, "decoded", decoded)
    if decoded:
        mu.mem_write(slot, struct.pack("<Q", CG))


def decoder_ret(mu):
    decoded = mu.reg_read(UC_X86_REG_RAX)
    record(mu, "decoded", decoded)
    if decoded:
        mu.reg_write(UC_X86_REG_RAX, CG)


def lens(answer):
    def fn(mu):
        lc, fov_at, half_at, x_at = (mu.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8,
                                                               UC_X86_REG_R9))
        y_at = struct.unpack("<Q", bytes(mu.mem_read(mu.reg_read(UC_X86_REG_RSP) + 0x28, 8)))[0]
        fov = bytes(mu.mem_read(fov_at, 4))
        record(mu, "lens", lc & 0xFFFFFFFF, fov)
        for at, value in zip((fov_at, half_at, x_at, y_at), answer):
            mu.mem_write(at, struct.pack("<f", value))
    return fn


def setup(encoded, slots):
    def apply(w):
        w.u64(ENCODED, encoded)
        w.u32(syms.va("dword_1440A99A4"), slots)
    return apply


def inputs():
    r = random.Random(1405)
    out = []
    for _ in range(80):
        encoded = r.choice([0, r.getrandbits(64), r.getrandbits(64), 0x0000_7FF6_1234_5678])
        lc = r.choice([0, 0, 0, 1, 2])
        slots = r.choice([0, 1, 1, 2])
        fov = r.choice([-1.0, -1.0, 0.0, 15.0, 50.0, 65.0, r.uniform(-5, 170)])
        answer = [r.uniform(1, 170), r.uniform(0, 3), r.uniform(0, 3), r.uniform(0, 3)]
        out.append({"args": [lc, ("f", fov)], "setup": setup(encoded, slots),
                    "fakes": {"CG_CalcFOVfromLens": lens(answer)}})
    return out


CASES = [{"symbol": SYM, "ret": "void", "ret_site": RET_SITE, "inputs": inputs(),
          "at": {INLINE_DONE: inline_done, **{a: decoder_ret for a in DECODER_RETS}}}]
