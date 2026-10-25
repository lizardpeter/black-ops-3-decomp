"""Hand-written cases for client/cl_input.cpp (mouse movement and its scale).

CL_GetMouseMovement: the double-buffered counts (cl_mouseDx/Dy, cl_mouseIndex), the eight-frame history and the
last result are set per case; m_filter and m_mouseFilter come from faked Dvar_GetBool/Dvar_GetFloat (filter values
0, between, at the 10 maximum, negative); local clients 0 and 1; consume true and false (false only repeats the
last result). Outputs, every global written and the dvar calls are compared.

sub_1413ACDF0: the last movement (s_lastMouseX/Y), cls_frametime, m_mouseSensitivity and m_mouseAcceleration
(faked, told apart by the dvar pointer), the weapon's ADS sensitivity (sub_1427D0FC0 faked, its argument observed),
the ADS fraction and the cgame's tan(half vertical FOV). The cgame is real memory reached through the encrypted
pointer (tests/differential/obfuscation.py encrypts with the game's own code), so the inline decode in the original
and the reconstruction's decode copy must agree; cases also cover no cgame (pointer 0: the tangent is read from the
null cg_t's offset 0x131D6C, as the original does), a localClientNum past cg_localClientCount, zero speed and NaN.

sub_141405E50: every Dvar_Register* is faked and records its arguments and returns a pointer per hash and salt, as
in test_r_dvars.py; the inlined player_name registration (Dvar_RegisterVariant with type 8 and an empty domain) is
recorded as the Dvar_RegisterString it is; sub_141410080 is faked and recorded.

Mutation check: see the commit adding this file.
"""
import random
import struct

import obfuscation
import syms
import test_r_dvars as regs
from harness import _MACHINES
from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RSP, UC_X86_REG_XMM0

GET_MOVEMENT = "?CL_GetMouseMovement@@YAXHPEAM0_N@Z"
SCALE = "?sub_1413ACDF0@@YAXHPEAM0@Z"
REGISTER = "?sub_141405E50@@YAXXZ"
GET_BOOL = "?Dvar_GetBool@@YA_NPEBUdvar_t@@@Z"
GET_FLOAT = "?Dvar_GetFloat@@YAMPEBUdvar_t@@@Z"
CG_BASE = 0x2000_0000
NULL_CG = 0                               # with no cgame the original reads through a null cg_t
DVARS = {name: 0x6000_0000_0000 + 0x100 * i for i, name in enumerate(
    ("m_filter", "m_mouseFilter", "m_mouseSensitivity", "m_mouseAcceleration"))}


def f32(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def ret_float(values):
    def fn(mu):
        mu.reg_write(UC_X86_REG_XMM0, f32(values[mu.reg_read(UC_X86_REG_RCX)]))
        return None
    return fn


def ret_bool(values):
    def fn(mu):
        return int(values[mu.reg_read(UC_X86_REG_RCX)])
    return fn


def dvar_pointers(w):
    for name, pointer in DVARS.items():
        w.u64(syms.va(name), pointer)


def movement_inputs():
    r = random.Random(1413)
    out = []
    for _ in range(300):
        lc = r.choice([0, 0, 1])
        index = r.choice([0, 1])
        dx = [r.choice([0, 1, -1, r.randint(-50, 50), r.randint(-40000, 40000), 0x7FFFFFFF]) for _ in range(2)]
        dy = [r.choice([0, 1, -1, r.randint(-50, 50), r.randint(-40000, 40000), -0x80000000]) for _ in range(2)]
        history = [[r.uniform(-500, 500) for _ in range(8)] for _ in range(4)]
        last = (r.uniform(-100, 100), r.uniform(-100, 100))
        values = {DVARS["m_filter"]: r.choice([False, True]),
                  DVARS["m_mouseFilter"]: r.choice([0.0, 0.0, 0.5, 5.0, 10.0, -1.0, 20.0])}

        def setup(w, dx=dx, dy=dy, index=index, history=history, last=last):
            dvar_pointers(w)
            w.write(syms.va("cl_mouseDx"), struct.pack("<2i", *dx))
            w.write(syms.va("cl_mouseDy"), struct.pack("<2i", *dy))
            w.u32(syms.va("cl_mouseIndex"), index)
            w.write(syms.va("s_mouseHistoryX"), struct.pack("<16f", *history[0], *history[1]))
            w.write(syms.va("s_mouseHistoryY"), struct.pack("<16f", *history[2], *history[3]))
            w.write(syms.va("s_lastMouseX"), struct.pack("<f", last[0]))
            w.write(syms.va("s_lastMouseY"), struct.pack("<f", last[1]))

        out.append({"args": [lc, bytes(4), bytes(4), r.choice([1, 1, 1, 0])], "setup": setup,
                    "fakes": {GET_BOOL: ret_bool(values), GET_FLOAT: ret_float(values)}})
    return out


def scale_inputs():
    r = random.Random(1414)
    out = []
    for _ in range(260):
        lc = r.choice([0, 0, 1, 2])
        count = r.choice([1, 2, 2, 0])
        has_cg = r.random() < 0.75
        last = (r.choice([0.0, r.uniform(-300, 300), 1.0, float("nan")]), r.choice([0.0, r.uniform(-300, 300), -2.0]))
        frametime = r.choice([1, 2, 7, 16, 33])
        tan_y = r.choice([0.47780272, 0.4638, 0.2, 0.1, 0.9])
        ads_fraction = r.choice([0.0, 1.0, 0.5, r.random()])
        ads_sens = r.choice([1.0, 0.5, 0.8, 1.3])
        weapon = r.getrandbits(64)
        values = {DVARS["m_mouseSensitivity"]: r.choice([2.0, 0.1, 30.0, 5.5]),
                  DVARS["m_mouseAcceleration"]: r.choice([0.0, 0.0, 0.5, 1.0])}

        def setup(w, lc=lc, count=count, has_cg=has_cg, last=last, frametime=frametime, tan_y=tan_y,
                  ads_fraction=ads_fraction, weapon=weapon):
            m, mu = w.m, w.m.mu
            obfuscation.map_region(m, CG_BASE, 0x00B00000)
            dvar_pointers(w)
            w.write(syms.va("s_lastMouseX"), struct.pack("<f", last[0]))
            w.write(syms.va("s_lastMouseY"), struct.pack("<f", last[1]))
            w.u32(syms.va("cls_frametime"), frametime)
            w.u32(syms.va("cg_localClientCount"), count)
            w.u64(syms.va("cg_arrayEncoded"), obfuscation.encrypt_cg_array(m, CG_BASE) if has_cg else 0)
            cg = CG_BASE + lc * obfuscation.CG_SIZE if has_cg and lc < count else NULL_CG
            ps = cg + 0x11A8B0
            mu.mem_write(cg + 0x131D6C, struct.pack("<f", tan_y))
            mu.mem_write(ps + 0x2FC, struct.pack("<f", ads_fraction))
            mu.mem_write(ps + 0x2C0, struct.pack("<Q", weapon))

        def ads(mu, value=ads_sens):
            mu.reg_write(UC_X86_REG_XMM0, f32(value))
            return None

        out.append({"args": [lc, bytes(4), bytes(4)], "setup": setup,
                    "fakes": {GET_FLOAT: ret_float(values), "sub_1427D0FC0": ads}})
    return out


def variant(salt):
    """Dvar_RegisterVariant as the original's inlined Dvar_RegisterString uses it (type 8, an empty domain): recorded
    and answered as test_r_dvars' Dvar_RegisterString fake would be."""
    return lambda mu: _variant(mu, salt)


def _variant(mu, salt):
    m = _MACHINES[id(mu)]
    rsp = mu.reg_read(UC_X86_REG_RSP)
    stack = [struct.unpack("<Q", bytes(mu.mem_read(rsp + 8 + 8 * i, 8)))[0] for i in range(8)]
    hash_, name, kind, flags = (mu.reg_read(r) for r in regs.INT)
    value, domain, description, session = stack[4], stack[5], stack[6], stack[7] & 0xFF
    string = m.read_cstr(struct.unpack("<Q", bytes(mu.mem_read(value, 8)))[0])
    if (kind & 0xFFFFFFFF) != 8 or bytes(mu.mem_read(domain, 16)) != bytes(16):
        m.observed.append(("Dvar_RegisterVariant", kind & 0xFFFFFFFF, bytes(mu.mem_read(domain, 16))))
    m.observed.append(("Dvar_RegisterString", hash_ & 0xFFFFFFFF, m.read_cstr(name), string, flags & 0xFFFFFFFF,
                       m.read_cstr(description), session))
    return 0x7F00_0000_0000 | salt << 32 | (hash_ & 0xFFFFFFFF)


def register_inputs():
    out = []
    for salt in (0x11, 0x22, 0x33, 0xA5):
        fakes = {name: regs.fake(name, salt) for name in regs.SPECS}
        fakes["Dvar_RegisterVariant"] = variant(salt)
        fakes["sub_141410080"] = lambda mu: _MACHINES[id(mu)].observed.append(("sub_141410080",))
        out.append({"args": [], "fakes": fakes})
    return out


CASES = [
    {"symbol": GET_MOVEMENT, "ret": "void", "inputs": movement_inputs()},
    {"symbol": SCALE, "ret": "void", "inputs": scale_inputs(), "observe": {"sub_1427D0FC0": "q"}},
    {"symbol": REGISTER, "ret": "void", "inputs": register_inputs()},
]
