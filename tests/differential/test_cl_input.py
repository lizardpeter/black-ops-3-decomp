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


# ---- CL_MouseMove ---------------------------------------------------------------------------------------------------
#
# Everything CL_MouseMove reads comes from fakes or per-case state, and everything it writes is compared:
# - the clientActive entry is a third buffer argument (ignored by the function as a parameter): the faked
#   CL_GetLocalClientGlobals returns its address, so the harness reads it back and compares it like the command;
# - the scaled movement (sub_1413ACDF0, faked for both copies), the animation lock (sub_142756F90), aim assist's
#   gate (sub_1408A5010), and the dvars m_yaw, m_pitch, m_side, m_forward, cl_freelook (faked by pointer);
# - aim assist (AimAssist_UpdateMouseInput) and the mouse-direction path (sub_140104EA0, Dvar_SetVec2,
#   sub_142396BB0) are faked: they record every AimInput field (not the unwritten padding) and write an output;
# - the cgame's speed limits (cl +0xB7D0/0xB7D4) inside and outside (0, 360], the `limited` state, NaN and huge
#   movement, +strafe, +mlook, the movement lock, demo playback, the player-state flag that picks the path.
MOUSE_MOVE = "?CL_MouseMove@@YAXHPEAUusercmd_s@@@Z"
CL_SIZE = 0xB900
PS = 0x0055_0000           # scratch: the faked predicted player state
AIM_DVAR = 0x0056_0000     # scratch: the mouse-direction vec2 dvar and its session variant
MOUSE_DVARS = {name: 0x6100_0000_0000 + 0x100 * i for i, name in enumerate(
    ("m_yaw", "m_pitch", "m_side", "m_forward", "cl_freelook"))}


def _record(mu, *values):
    _MACHINES[id(mu)].observed.append(values)


def _aim_input(mu, address):
    raw = bytes(mu.mem_read(address, 0x50))
    fields = struct.unpack_from("<10IH", raw, 0) + struct.unpack_from("<3Ii", raw, 0x2C) \
        + struct.unpack_from("<QIHH", raw, 0x40)
    return fields


def _floats_out(mx, my):
    def fn(mu):
        from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_RDX
        mu.mem_write(mu.reg_read(UC_X86_REG_RDX), struct.pack("<f", mx))
        mu.mem_write(mu.reg_read(UC_X86_REG_R8), struct.pack("<f", my))
        return None
    return fn


def _aim_assist(pitch, yaw):
    def fn(mu):
        from unicorn.x86_const import UC_X86_REG_RDX
        _record(mu, "AimAssist_UpdateMouseInput", _aim_input(mu, mu.reg_read(UC_X86_REG_RCX)))
        mu.mem_write(mu.reg_read(UC_X86_REG_RDX), struct.pack("<ffHH", pitch, yaw, 0x1234, 0x5678))
        return None
    return fn


def _direction_aim(mu):
    from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_RDX
    out = mu.reg_read(UC_X86_REG_R8)
    _record(mu, "sub_140104EA0", mu.reg_read(UC_X86_REG_RCX), _aim_input(mu, mu.reg_read(UC_X86_REG_RDX)),
            bytes(mu.mem_read(out, 12)))
    pitch, yaw = struct.unpack("<ff", bytes(mu.mem_read(out, 8)))
    mu.mem_write(out, struct.pack("<ff", pitch + 1.5, yaw - 2.25))
    return None


def _set_vec2(mu):
    from unicorn.x86_const import UC_X86_REG_XMM1, UC_X86_REG_XMM2
    _record(mu, "Dvar_SetVec2", mu.reg_read(UC_X86_REG_RCX), mu.reg_read(UC_X86_REG_XMM1) & 0xFFFFFFFF,
            mu.reg_read(UC_X86_REG_XMM2) & 0xFFFFFFFF)
    return None


def _session_variant(mu):
    from unicorn.x86_const import UC_X86_REG_RDX
    _record(mu, "sub_142396BB0", mu.reg_read(UC_X86_REG_RCX), mu.reg_read(UC_X86_REG_RDX) & 0xFFFFFFFF)
    return AIM_DVAR + 0x100


def mouse_move_inputs():
    r = random.Random(1730)
    out = []
    special = [0.0, float("nan"), 1e9, -1e9, 126.9, 127.5, -0.25]
    for n in range(440):
        forced = n >= 400  # the mouse-direction path with a direction that cancels to zero length
        lc = r.choice([0, 0, 1])
        mx = r.choice([0.0, r.uniform(-300, 300), r.uniform(-3, 3), r.choice(special)])
        my = r.choice([0.0, r.uniform(-300, 300), r.uniform(-3, 3), r.choice(special)])
        cl = bytearray(r.randbytes(CL_SIZE))
        struct.pack_into("<Q", cl, 0xC0, r.choice([0, 0, 0, 0x400000000000000, 0x10000000, 0x1234]))
        struct.pack_into("<i", cl, 0x10C, r.choice([0, 0, 0, 0x3F]))
        cl[0xA34] = r.choice([0, 0, 0, 8, 7])
        struct.pack_into("<I", cl, 0xD0, r.choice([0, 0x200, 0x1FF]))
        struct.pack_into("<i", cl, 0xB8, r.choice([1, 1, 0, 2, 3, 4]))
        cl[0x790] = r.choice([0, 1, 2])
        for off in (0xB7D0, 0xB7D4):
            struct.pack_into("<f", cl, off, r.choice([0.0, 90.0, 360.0, 400.0, -5.0, float("nan"), 1e-3]))
        for off in (0xB8C8, 0xB8CC):
            struct.pack_into("<f", cl, off, r.uniform(-720, 720))
        cmd = bytearray(r.randbytes(0x48))
        values = {MOUSE_DVARS["m_yaw"]: r.choice([0.022, -0.022, 0.0, 1.0]),
                  MOUSE_DVARS["m_pitch"]: r.choice([0.022, -0.022, 0.0]),
                  MOUSE_DVARS["m_side"]: r.choice([0.25, -1.0, 0.0]),
                  MOUSE_DVARS["m_forward"]: r.choice([0.25, 1.0, -0.5]),
                  MOUSE_DVARS["cl_freelook"]: r.choice([True, True, False])}
        frametime = r.choice([0, 1, 4, 16, 50])
        strafe, mlook = r.random() < 0.15, r.random() < 0.2
        demo = r.choice([0, 0, 2])
        active = r.choice([1, 1, 0]) or forced
        aim_gate = r.choice([True, True, False]) or forced
        lock = r.random() < 0.1 and not forced
        ps_flags = 0x20000000000000 if forced else r.choice([0, 0x20000000000000, 0x20000000000000, 0xFF])
        direction = AIM_DVAR if forced else r.choice([0, AIM_DVAR, AIM_DVAR])
        if forced:
            mx, my = r.uniform(-50, 50), r.uniform(-50, 50)
            struct.pack_into("<i", cl, 0xB8, 1)
        direction_type = r.choice([15, 4])
        base = (-mx, -my) if forced or r.random() < 0.2 else (r.uniform(-1, 1), r.uniform(-1, 1))
        session = r.getrandbits(32)

        def setup(w, lc=lc, frametime=frametime, strafe=strafe, mlook=mlook, demo=demo, active=active,
                  ps_flags=ps_flags, direction=direction, direction_type=direction_type, base=base, session=session):
            mu = w.m.mu
            for name, pointer in MOUSE_DVARS.items():
                w.u64(syms.va(name), pointer)
            w.u32(syms.va("cls_frametime"), frametime)
            w.u32(syms.va("cls_aimFrametime"), frametime * 3 + 1)
            w.u32(syms.va("unk_1494B2DC8"), demo)
            w.write(syms.va("kb_strafeActive") + lc * 0x498, bytes([strafe]))
            w.write(syms.va("kb_mlookActive") + lc * 0x498, bytes([mlook]))
            w.u32(syms.va("cl_localClientActive") + lc * 36, active)
            w.u64(syms.va("aim_mouseDirection"), direction)
            w.u32(syms.va("com_sessionModeState"), session)
            ps = bytearray(0x1000)
            struct.pack_into("<Q", ps, 0x10, ps_flags)
            struct.pack_into("<f", ps, 0x2FC, 0.375)
            struct.pack_into("<H", ps, 0x994, 0xA994)
            struct.pack_into("<H", ps, 0x99C, 0xA99C)
            mu.mem_write(PS, bytes(ps))
            dvar = bytearray(0x200)
            struct.pack_into("<i", dvar, 0x1C, direction_type)
            struct.pack_into("<ff", dvar, 0x28, *base)
            struct.pack_into("<ff", dvar, 0x128, *base)  # the session variant (AIM_DVAR + 0x100)
            mu.mem_write(AIM_DVAR, bytes(dvar))

        cl_address = 0x0030_0000 + ((len(cmd) + 16 + 0xFFF) & ~0xFFF)  # the harness heap: the third argument
        fakes = {
            "CL_GetLocalClientGlobals": lambda mu, a=cl_address: a,
            SCALE: _floats_out(mx, my),
            "CG_GetPredictedPlayerState": lambda mu: PS,
            "sub_142756F90": lambda mu, v=lock: int(v),
            "sub_1408A5010": lambda mu, v=aim_gate: int(v),
            GET_FLOAT: ret_float(values),
            GET_BOOL: ret_bool(values),
            "AimAssist_UpdateMouseInput": _aim_assist(r.uniform(-90, 90), r.uniform(-180, 180)),
            "sub_140104EA0": _direction_aim,
            "Dvar_SetVec2": _set_vec2,
            "sub_142396BB0": _session_variant,
        }
        out.append({"args": [lc, bytes(cmd), bytes(cl)], "setup": setup, "fakes": fakes})
    return out


CASES.append({"symbol": MOUSE_MOVE, "ret": "void", "inputs": mouse_move_inputs(),
              "observe": {GET_FLOAT: "q", GET_BOOL: "q", "sub_1408A5010": "i", "sub_142756F90": "q",
                          "api-ms-win-crt-math-l1-1-0.dll!floorf": "f"}})
