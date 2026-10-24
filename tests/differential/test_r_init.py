"""Hand-written cases for gfx_d3d/r_init.cpp (display modes and the swap chain description).

sub_141DAA730 (the mode-list comparator) gets pairs of DXGI_MODE_DESC: equal and different sizes (including sizes
whose difference overflows int), equal and different rates, rates with a zero denominator (inf, NaN).

sub_141DA7A00 gets a garbage-filled description to fill and window parameters across every gate: fullscreen or not (a bool: 0 or 1, as 141DABB90 stores it),
hz zero / negative zero / NaN / typical / above 240, monitor 0, in range and past dx_monitorCount, with mode lists set
up in scratch memory: several rates per size, the requested size missing, duplicates with equal distance (the first
must win), zero-denominator modes, and rates above 240 Hz. Dvar_GetInt (r_backBufferCount) is faked to a per-case
value. The whole description is compared, so the copied mode and every fixed field are checked.

Mutation check: see the commit adding this file.
"""
import random
import struct

import syms
from harness import SCRATCH
from unicorn.x86_const import UC_X86_REG_RCX

COMPARE = "?sub_141DAA730@@YAHPEBX0@Z"
SWAPCHAIN = "?sub_141DA7A00@@YAXPEAUDXGI_SWAP_CHAIN_DESC@@PEBUGfxWindowParms@@@Z"
BACKBUFFER_DVAR = 0x6000_0000_0260
MODES = SCRATCH + 0x40000


def mode(w, h, num, den, fmt=28, scan=0, scale=0):
    return struct.pack("<7I", w & 0xFFFFFFFF, h & 0xFFFFFFFF, num, den, fmt, scan, scale)


def rates(r):
    return r.choice([(60, 1), (59940, 1000), (144, 1), (143998, 1000), (165, 1), (240, 1), (239760, 1000), (280, 1),
                     (360, 1), (359999, 1000), (500, 1), (75, 1), (120, 1), (0, 0), (5, 0), (0, 1)])


def compare_inputs():
    r = random.Random(730)
    sizes = [(1920, 1080), (2560, 1440), (3840, 2160), (800, 600), (0x7FFFFFFF, 1), (0x80000000, 1)]
    out = []
    for _ in range(240):
        a = (*r.choice(sizes), *rates(r))
        b = r.choice([a, (*a[:2], *rates(r)), (*r.choice(sizes), *rates(r))])
        out.append([mode(*a, fmt=r.randrange(100)), mode(*b, fmt=r.randrange(100))])
    return out


def swapchain_setup(monitor_count, lists):
    def apply(w):
        w.u32(syms.va("dx_monitorCount"), monitor_count)
        at = MODES
        for i in range(8):
            modes = lists[i] if i < len(lists) else []
            w.u32(syms.va("dx_modeCount") + 4 * i, len(modes))
            w.u64(syms.va("dx_modes") + 8 * i, at if modes else 0)
            for m in modes:
                w.write(at, m)
                at += 0x1C
        w.u64(syms.va("r_backBufferCount"), BACKBUFFER_DVAR)
    return apply


def swapchain_inputs():
    r = random.Random(7_000)
    sizes = [(1920, 1080), (1920, 1200), (2560, 1440), (2560, 1080), (3840, 2160), (1280, 720)]
    hz_bits = [struct.unpack("<I", struct.pack("<f", x))[0] for x in (60.0, 144.0, 165.0, 240.0, 239.76, 1.0, 59.94)]
    hz_bits += [0, 0x80000000, 0x7FC00000, 0xC2700000, struct.unpack("<I", struct.pack("<f", 360.0))[0]]
    out = []
    for _ in range(260):
        monitor_count = r.choice([0, 1, 2, 3, 8])
        lists = []
        for _ in range(r.choice([1, 2, 3, 8])):
            modes = [mode(*r.choice(sizes), *rates(r), fmt=r.choice([28, 87]), scan=r.randrange(3), scale=r.randrange(3))
                     for _ in range(r.choice([0, 1, 4, 12, 30]))]
            lists.append(modes)
        w, h = r.choice(sizes + [(1600, 900)])
        params = (struct.pack("<Q", r.getrandbits(64)) + struct.pack("<I", r.choice(hz_bits))
                  + bytes([r.choice([0, 1, 1])]) + r.randbytes(3)
                  + struct.pack("<i", r.choice([0, 1, 2, 3, 8, 9, -1]))
                  + struct.pack("<4i", *(r.getrandbits(31) for _ in range(4)))
                  + struct.pack("<ii", w, h) + r.randbytes(4))
        assert len(params) == 0x30
        backbuffers = r.choice([2, 3])
        out.append({"args": [r.randbytes(0x48), params], "setup": swapchain_setup(monitor_count, lists),
                    "fakes": {"Dvar_GetInt": (lambda n: lambda mu: n if mu.reg_read(UC_X86_REG_RCX) == BACKBUFFER_DVAR
                                              else 0xBAD)(backbuffers)}})
    return out


CASES = [
    {"symbol": COMPARE, "ret": "int", "inputs": compare_inputs()},
    {"symbol": SWAPCHAIN, "ret": "void", "inputs": swapchain_inputs()},
]
