"""Hand-written cases for ui/lua_cod_luacalls.cpp (UI Lua calls).

Lua_CoD_LuaCall_GetAvailableRefreshRates gets a lua_State built in its argument buffer (at the harness heap, so every
pointer in it is known): the header's top/base and a value stack holding the call's three arguments (width, height,
monitor) as numbers or nil. hks_obj_tonumber runs for real. The table, string and settable routines are faked to
record their arguments and move the stack top as the real ones do; sprintf is faked to format "%.3f" itself and
records its format and the double it got. The whole lua_State buffer (every value pushed) and the recorded calls are
compared. Because the buffer sits below 4 GB, the original's pushed table value has a zero pad word (it copies a
stack temporary whose upper half held the high half of the lua_State pointer), as the reconstruction writes.

The display modes are set up per monitor as the game leaves them (sorted by size, then rate), with lists both shorter
and longer than 128 modes and the asked-for size both inside and past the first 128, so the 128-mode window (B0013) is
covered; monitors 0, 9 and negative take the "no table entries" path.

Mutation check: see the commit adding this file.
"""
import random
import struct

import syms
from harness import HEAP, SCRATCH, _MACHINES
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_RCX, UC_X86_REG_RDX

SYM = "?Lua_CoD_LuaCall_GetAvailableRefreshRates@@YAHPEAUlua_State@@@Z"
L = HEAP
STACK = L + 0x100
TABLE = 0x0000_7E00_0000_1230
MODES = SCRATCH + 0x40000
SIZES = [(800, 600), (1024, 768), (1280, 720), (1600, 900), (1920, 1080), (1920, 1200), (2560, 1080), (2560, 1440),
         (3440, 1440), (3840, 2160)]
RATES = [(60, 1), (59940, 1000), (75, 1), (100, 1), (120, 1), (144, 1), (143998, 1000), (165, 1), (240, 1), (280, 1),
         (360, 1), (359999, 1000), (500, 1), (5, 0)]


def record(mu, *values):
    _MACHINES[id(mu)].observed.append(values)


def top(mu):
    return struct.unpack("<Q", bytes(mu.mem_read(L + 0x48, 8)))[0]


def set_top(mu, value):
    mu.mem_write(L + 0x48, struct.pack("<Q", value))


def pushlstring(mu):
    m = _MACHINES[id(mu)]
    s, n = mu.reg_read(UC_X86_REG_RDX), mu.reg_read(UC_X86_REG_R8)
    record(mu, "pushlstring", m.read_cstr(s), n)
    t = top(mu)
    mu.mem_write(t, struct.pack("<IIQ", 4, 0, 0x5757))
    set_top(mu, t + 0x10)


def settable(mu):
    record(mu, "settable", mu.reg_read(UC_X86_REG_RDX) & 0xFFFFFFFF)
    set_top(mu, top(mu) - 0x20)


def createtable(mu):
    record(mu, "createtable", mu.reg_read(UC_X86_REG_RDX) & 0xFFFFFFFF, mu.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF)
    return TABLE


def sprintf(mu):
    m = _MACHINES[id(mu)]
    buf, fmt, bits = mu.reg_read(UC_X86_REG_RCX), mu.reg_read(UC_X86_REG_RDX), mu.reg_read(UC_X86_REG_R8)
    value = struct.unpack("<d", struct.pack("<Q", bits))[0]
    record(mu, "sprintf", m.read_cstr(fmt), bits)
    text = (m.read_cstr(fmt).decode() % value).encode()
    mu.mem_write(buf, text + b"\0")
    return len(text)


FAKES = {"lua_createtable": createtable, "hksi_lua_pushlstring": pushlstring, "lua_settable": settable,
         "sprintf": sprintf}


def setup(lists):
    def apply(w):
        at = MODES
        for i in range(8):
            modes = lists[i]
            w.u32(syms.va("dx_modeCount") + 4 * i, len(modes))
            w.u64(syms.va("dx_modes") + 8 * i, at if modes else 0)
            for mode in modes:
                w.write(at, mode)
                at += 0x1C
    return apply


def mode_list(r):
    n = r.choice([0, 3, 20, 127, 128, 129, 150, 220])
    modes = sorted(((*r.choice(SIZES), *r.choice(RATES)) for _ in range(n)),
                   key=lambda m: (m[0], m[1], m[2] / m[3] if m[3] else float("inf")))
    return [struct.pack("<7I", w, h, num, den, 28, 0, r.randrange(3)) for w, h, num, den in modes]


def lua_state(args):
    head = bytearray(0x100)
    head[0x48:0x50] = struct.pack("<Q", STACK + 0x10 * len(args))
    head[0x50:0x58] = struct.pack("<Q", STACK)
    stack = bytearray(0x500)
    for i, a in enumerate(args):
        stack[0x10 * i:0x10 * i + 16] = struct.pack("<IIfI", 0, 0, 0.0, 0) if a is None else \
            struct.pack("<IIfI", 3, 0, float(a), 0)
    return bytes(head + stack)


def inputs():
    r = random.Random(1420)
    out = []
    for _ in range(220):
        lists = [mode_list(r) for _ in range(8)]
        monitor = r.choice([1, 1, 2, 3, 8, 0, 9, -1])
        modes = lists[monitor - 1] if 1 <= monitor <= 8 else []
        if modes and r.random() < 0.8:
            w, h = struct.unpack("<II", r.choice(modes)[:8])
        else:
            w, h = r.choice(SIZES)
        args = [w, h, monitor]
        if r.random() < 0.05:
            args[r.randrange(3)] = None
        out.append({"args": [lua_state(args)], "setup": setup(lists)})
    return out


CASES = [{"symbol": SYM, "ret": "int", "fakes": FAKES, "inputs": inputs()}]
