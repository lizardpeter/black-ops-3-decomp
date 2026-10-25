"""P0015 and P0016: the FOV setting in MW2019's unit, shown exactly (docs/fov.md).

P0015: the enhanced Dvar_Init registers cg_fov_default with the range 60-120 (original 65-120), default 80, and
makes every other registration exactly as the original (same calls, order, arguments and stored globals).

P0016: sub_1405B6690 runs with the real CG_CalcFOVfromLens and the real decoders. A cg_t, a cgs_t and a lens table
are laid out in memory mapped for the test; where the decoders leave the cg and cgs pointers (the standalone copy's
returns, the original's inline copy at 1405B7E4C, CG_CalcFOVfromLens's two at 1405B1226 and 1405B2B21) the test
puts those addresses, so both copies of sub_1405B6690 see the same state. The lens is set as 1405B2E80 sets it for
the player's FOV h: focal length 7 / (tan(h/2) * 9/16). Checked:
- hip fire, depth of field off: the horizontal FOV at 16:9 is h (within 0.01 degrees) for h 60-120, and the vertical
  FOV is the same at 21:9 (Hor+);
- aimed down sights: exactly the original's values; half way: the original's tanHalfFovY plus half of 7/500;
- depth of field on, the cg_drawMinimap lens, a fixed FOV from a scripted camera: exactly the original's values.
"""
import math
import struct

import test_dvar as init
import test_r_dvars as regs
from unicorn import UcError
from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RBP, UC_X86_REG_RCX, UC_X86_REG_XMM0, UC_X86_REG_XMM1

SYM = "?sub_1405B6690@@YAXHM@Z"
RET_SITE = 0x1405639E0
CG, CGS, LENS = 0x10000000, 0x10400000, 0x10500000
DECODER_RETS = [0x1414070A5, 0x141407234, 0x14140738D, 0x141407517, 0x1414076AE, 0x14140780B, 0x1414079A1,
                0x141407B11, 0x141407C98, 0x141407DDE, 0x141407F4C, 0x1414080CB, 0x141408267, 0x1414083C5,
                0x141408526, 0x141408683]


def f32bits(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def both(env, symbol, inp, ret, fakes):
    hooks = {va: fn for s, fn in fakes.items() for va in env.at(s)}
    original = env.machine.call(env.original(symbol), inp["args"], ret, inp.get("setup"), hooks)
    enhanced = env.call(symbol, inp["args"], ret, inp.get("setup"), fakes)
    return original, enhanced


def test_fov_minimum_60(env):
    for inp in init.inputs():
        original, enhanced = both(env, init.SYM, inp, "void", inp["fakes"])
        want = [list(c) for c in original[3]]
        changed = 0
        for c in want:
            if c[0] == "Dvar_RegisterFloat" and c[2] == b"cg_fov_default":
                assert c[3:6] == [f32bits(80.0), f32bits(65.0), f32bits(120.0)], c
                c[4] = f32bits(60.0)
                changed += 1
        assert changed == 1
        assert [list(c) for c in enhanced[3]] == want
        assert enhanced[2] == original[2]


# --- P0016 -------------------------------------------------------------------------------------------------------

def put_cg(mu):
    mu.reg_write(UC_X86_REG_RCX, CG)


def put_cgs(mu):
    rbp = mu.reg_read(UC_X86_REG_RBP)
    mu.mem_write(rbp + 0x60, struct.pack("<Q", CGS))


def inline_cg(mu):
    mu.mem_write(mu.reg_read(UC_X86_REG_RBP) - 0x18, struct.pack("<Q", CG))


def decoder_cg(mu):
    if mu.reg_read(UC_X86_REG_RAX):
        mu.reg_write(UC_X86_REG_RAX, CG)


def blend(mu):
    # 14056A350 eases the FOV between two values over cg+0x2D897C seconds; with no easing it returns its argument
    mu.reg_write(UC_X86_REG_XMM0, mu.reg_read(UC_X86_REG_XMM1))


HOOKS = {0x1405B7E4C: inline_cg, 0x1405B1226: put_cg, 0x1405B2B21: put_cgs, **{a: decoder_cg for a in DECODER_RETS}}


def run(env, h, ads=0.0, flags=0, minimap=False, fov=-1.0, aspect=16 / 9, original=False):
    mu = env.machine.mu
    try:
        mu.mem_map(CG, 0x600000)
    except UcError:
        pass
    focal = 7.0 / (math.tan(math.radians(h) / 2) * 0.5625)

    def setup(w):
        w.u64(0x149B25A20, 0x1234_5678)
        w.u64(0x149B25A28, 0x8765_4321)
        w.u32(0x1440A99A4, 1)
        w.write(CG + 0x11ABAC, struct.pack("<f", ads))
        w.u32(CG + 0x131D28, flags)
        w.write(CG + 0x2D8910, struct.pack("<ff", focal, 10000.0))   # focal length (mm), focus (inches)
        w.write(CG + 0x2D908A, b"\0")                                  # lens preset 0
        w.write(CG + 0x2D897C, struct.pack("<f", 0.0))                 # no FOV easing
        w.write(CGS + 0x10, struct.pack("<f", aspect))
        w.u64(0x1486EFDA0, LENS)
        w.u64(LENS + 0x5A0, LENS + 0x1000)
        w.write(LENS + 0x1004, struct.pack("<ff", 1.0, 10000.0))        # focal length limits
        w.write(LENS + 0x1014, struct.pack("<ff", 0.0, 1e6))            # focus limits (inches)
        w.write(0x143112ECB, b"\0")
        w.u64(0x1490FFCE0, 0)
        mu.mem_write(CG + 0x131D68, bytes(16))

    fakes = {0x1405933F0: lambda mu: 0xB,                 # camera mode 11: the lens is set above, not updated
             "Dvar_GetBool": lambda mu: int(minimap), 0x14220B3A0: lambda mu: 0xFFFFFFFF, 0x14056A350: blend}
    value = env.call(SYM, [0, ("f", fov)], "void", setup, fakes, ret_site=RET_SITE, at=HOOKS, original=original)[0]
    assert value is None, value
    x, y, y2, deg = struct.unpack("<4f", bytes(mu.mem_read(CG + 0x131D68, 16)))
    assert y == y2
    return x, y, deg


def screen(tan_half):
    return math.degrees(2 * math.atan(tan_half))


def test_hip_fov_is_exact(env):
    for h in (60, 65, 80, 90, 100, 110, 120):
        ox, oy, odeg = run(env, h, original=True)
        x, y, deg = run(env, h)
        assert abs(screen(x) - h) < 0.01, (h, screen(x), screen(ox))
        assert screen(ox) < h - 0.5, (h, screen(ox))                       # the original shows less
        assert abs(y - math.tan(math.radians(h) / 2) * 0.5625) < 2e-6
        assert abs((deg - odeg) - 2 * math.degrees(math.atan(y / 0.75) - math.atan(oy / 0.75))) < 1e-3
        wx, wy, _ = run(env, h, aspect=21 / 9)
        assert abs(wy - y) < 1e-6 and abs(wx / wy - 21 / 9) < 1e-5            # Hor+: same vertical FOV


def test_ads_keeps_original_zoom(env):
    for h in (65, 80, 120):
        assert run(env, h, ads=1.0) == run(env, h, ads=1.0, original=True)
        ox, oy, _ = run(env, h, ads=0.5, original=True)
        x, y, _ = run(env, h, ads=0.5)
        assert abs(y - (oy + 0.5 * 7 / 500)) < 1e-6 and abs(x / y - ox / oy) < 1e-5


def test_other_lenses_unchanged(env):
    for h in (65, 80, 120):
        for kwargs in ({"flags": 0x10000}, {"flags": 0x20000}, {"minimap": True}, {"fov": 50.0}, {"fov": 0.0}):
            assert run(env, h, **kwargs) == run(env, h, original=True, **kwargs), (h, kwargs)
