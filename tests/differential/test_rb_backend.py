"""Hand-written cases for gfx_d3d/rb_backend.cpp (the render thread's 3D scenes).

sub_141D46D30: backEndData points at a fake frontend whose scene count, last scene index and scene array are set per
case; the scenes' +0xB24C8 (draw the one before too) and +0x1430 (input block) are placed in a
region the first setup maps. dword_1486BEEA0
is 0 or 2 and word_1486F0DA4 random. 141D4E220, 141DF1770 and 141DEECD0 are faked and observed with their arguments,
so which scenes are drawn, in which order and how are compared (141DEECD0's technique is a u16: only DX is
the argument). Indexes include 0 (the scene before is at index -1)
and 0x7FFFFFFF/0x80000000 around the signed wrap (with the sign bit set the loop reaches scenes 2^32
scenes away: passed on to the fakes, or, read through, a fault in the original and the input is skipped).

Mutation check: see the commit adding this file.
"""
import random

import syms
from harness import SCRATCH, _MACHINES
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_RCX, UC_X86_REG_RDX

SYM = "?sub_141D46D30@@YAXXZ"
STRIDE = 0xD5F60
FRONTEND_FIELDS = SCRATCH + 0x100        # where the frontend's +0xF6568.. lands
REGION, REGION_SIZE = 0x10000000, 0x200000   # mapped by the first setup: two scenes' fields, 0xD5F60 apart
SCENE_PREV = REGION + 0x1000
SCENE_LAST = SCENE_PREV + STRIDE


def _record(name, rdx_mask=0xFFFFFFFFFFFFFFFF):
    def fn(mu):
        _MACHINES[id(mu)].observed.append(
            (name, mu.reg_read(UC_X86_REG_RCX), mu.reg_read(UC_X86_REG_RDX) & rdx_mask, mu.reg_read(UC_X86_REG_R8)))
        return None
    return fn


def _map(mu):
    if not any(start <= REGION < end for start, end, _ in mu.mem_regions()):
        mu.mem_map(REGION, REGION_SIZE)


def inputs():
    r = random.Random(0x141D46D30)
    out = []
    for _ in range(120):
        count = r.choice([0, 1, 1, 2, 5])
        last = r.choice([0, 1, 2, 7, 0x7FFFFFFF, 0x80000000, r.randrange(0, 1 << 32)])
        draw_previous = r.choice([0, 1, 0x80])
        ready = r.choice([0, 2, 2])
        technique = r.randrange(0, 0x10000)
        frontend = FRONTEND_FIELDS - 0xF6568
        # scenes + last * STRIDE (the index as unsigned and as signed agree on the low 64 bits only when the sign
        # bit is clear: the original reads the flag through the unsigned index and loops with the signed one)
        scenes = (SCENE_LAST - last * STRIDE) & 0xFFFFFFFFFFFFFFFF

        def setup(w, count=count, last=last, draw_previous=draw_previous, ready=ready, technique=technique,
                  frontend=frontend, scenes=scenes):
            mu = w.m.mu
            _map(mu)
            mu.mem_write(REGION, b"\0" * REGION_SIZE)
            w.u64(syms.va("backEndData"), frontend)
            w.u32(syms.va("dword_1486BEEA0"), ready)
            w.write(syms.va("word_1486F0DA4"), technique.to_bytes(2, "little"))
            mu.mem_write(FRONTEND_FIELDS, last.to_bytes(4, "little") + count.to_bytes(4, "little")
                         + scenes.to_bytes(8, "little"))
            mu.mem_write(SCENE_LAST + 0xB24C8, bytes([draw_previous]))
            mu.mem_write(SCENE_LAST + 0x1430, (0xA111).to_bytes(8, "little"))
            mu.mem_write(SCENE_PREV + 0x1430, (0xA222).to_bytes(8, "little"))

        out.append({"args": [], "setup": setup})
    return out


CASES = [{"symbol": SYM, "ret": "void", "inputs": inputs(),
          "fakes": {"sub_141D4E220": _record("4E220"), "sub_141DF1770": _record("F1770"),
                    "sub_141DEECD0": _record("EECD0", 0xFFFF)}}]
