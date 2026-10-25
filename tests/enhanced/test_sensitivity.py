"""P0011: mouse aim in MW2019 units, the same at any FOV (docs/input-sensitivity.md).

- Registration: exactly the original's calls, except m_mouseSensitivity, which is 1.5 in 0.01..100.
- CL_GetMouseMovement: the plain counts, with the original's buffer flip and clearing, and no dvar read (no
  m_filter, no m_mouseFilter); compared with the original on every faithful input where those are off.
- sub_1413ACDF0: the last movement times m_mouseSensitivity * 0.0066 / 0.022, whatever the cgame's FOV, the ADS
  fraction, the weapon, the frame time and the acceleration; the weapon is never asked.
- Through CL_MouseMove's m_yaw multiplication at its default 0.022, one count turns the view by
  m_mouseSensitivity * 0.0066 degrees (single-precision: within 1e-6 relative).
"""
import struct

import test_cl_input as faithful
import test_r_dvars as regs

SENS = 0x247B172F


def f32(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def as_float(b):
    return struct.unpack("<f", b)[0]


def both(env, symbol, inp, ret, fakes, observe=None):
    hooks = {va: fn for s, fn in fakes.items() for va in env.at(s)}
    obs = {va: spec for s, spec in (observe or {}).items() for va in env.at(s)}
    original = env.machine.call(env.original(symbol), inp["args"], ret, inp.get("setup"), hooks, obs)
    enhanced = env.call(symbol, inp["args"], ret, inp.get("setup"), fakes, observe)
    return original, enhanced


def test_registration(env):
    for inp in faithful.register_inputs():
        original, enhanced = both(env, faithful.REGISTER, inp, "void", inp["fakes"])
        want = [list(c) for c in original[3]]
        for c in want:
            if c[0] == "Dvar_RegisterFloat" and c[1] == SENS:
                assert c[3:6] == [f32(2.0), f32(0.1), f32(30.0)], c
                c[3:6] = [f32(1.5), f32(0.01), f32(100.0)]
        assert [list(c) for c in enhanced[3]] == want
        assert enhanced[2] == original[2]


def test_movement_is_plain_counts(env):
    def forbid(mu):
        raise AssertionError("a filter dvar was read")

    for inp in faithful.movement_inputs():
        setup = inp["setup"]
        lc, consume = inp["args"][0], inp["args"][3]
        value, buffers, writes, observed = env.call(
            faithful.GET_MOVEMENT, inp["args"], "void", setup,
            {faithful.GET_BOOL: forbid, faithful.GET_FLOAT: forbid})
        # the original with its filters off answers the same
        off = {faithful.DVARS["m_filter"]: False, faithful.DVARS["m_mouseFilter"]: 0.0}
        fakes = {faithful.GET_BOOL: faithful.ret_bool(off), faithful.GET_FLOAT: faithful.ret_float(off)}
        original, _ = both(env, faithful.GET_MOVEMENT, inp, "void", fakes)
        assert buffers == original[1] and writes == original[2], (inp["args"], buffers, original[1])


def test_scale_ignores_fov_ads_speed(env):
    for i, inp in enumerate(faithful.scale_inputs()):
        sens = (1.5, 0.37, 8.0)[i % 3]
        last = (float(i % 41 - 20), float(13 - i % 29))

        def setup(w, base=inp["setup"], last=last):
            base(w)  # the faithful case's cgame, FOV, ADS fraction, frame time and dvars
            w.write(faithful.syms.va("s_lastMouseX"), struct.pack("<f", last[0]))
            w.write(faithful.syms.va("s_lastMouseY"), struct.pack("<f", last[1]))

        fakes = {faithful.GET_FLOAT: lambda mu, s=sens: (mu.reg_write(faithful.UC_X86_REG_XMM0, f32(s)), None)[1],
                 "sub_1427D0FC0": lambda mu: (_ for _ in ()).throw(AssertionError("weapon asked"))}
        value, buffers, writes, observed = env.call(faithful.SCALE, inp["args"], "void", setup, fakes)
        scale = as_float(struct.pack("<f", as_float(struct.pack("<f", sens)) * as_float(struct.pack("<f", 0.0066 / 0.022))))
        assert as_float(buffers[0]) == as_float(struct.pack("<f", scale * last[0])), (sens, last, buffers)
        assert as_float(buffers[1]) == as_float(struct.pack("<f", scale * last[1]))
        assert not writes


def test_degrees_per_count(env):
    for sens in (1.5, 0.5, 2.37, 10.0):
        for counts in (1, 3, -7, 1000):
            inp = {"args": [0, bytes(4), bytes(4)],
                   "setup": lambda w, c=counts: (w.write(faithful.syms.va("s_lastMouseX"), struct.pack("<f", c)),
                                                 w.write(faithful.syms.va("s_lastMouseY"), struct.pack("<f", -c)))}
            fakes = {faithful.GET_FLOAT: lambda mu, s=sens: (mu.reg_write(faithful.UC_X86_REG_XMM0, f32(s)), None)[1]}
            _, buffers, _, _ = env.call(faithful.SCALE, inp["args"], "void", inp["setup"], fakes)
            mx, my = as_float(buffers[0]), as_float(buffers[1])
            m_yaw = as_float(struct.pack("<f", 0.022))
            yaw = as_float(struct.pack("<f", m_yaw * mx))   # CL_MouseMove: m_yaw * mx, single precision
            want = sens * 0.0066 * counts
            assert abs(yaw - want) <= 1e-6 * abs(want), (sens, counts, yaw, want)
            assert my == -mx


# ---- P0012: CL_MouseMove in double precision --------------------------------------------------------------------

def _f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def _ulps(a, b):
    ia, ib = (struct.unpack("<i", struct.pack("<f", v))[0] for v in (a, b))
    return abs(ia - ib)


def test_mouse_move_matches_original_but_rounding(env):
    """Every faithful input: the command, the calls and everything but the two view angles are the original's; the
    angles differ by at most one float ulp (the original rounds the turn and the sum to float, the enhanced build
    adds in double and rounds once)."""
    for inp in faithful.mouse_move_inputs():
        fakes = inp["fakes"]
        original, enhanced = both(env, faithful.MOUSE_MOVE, inp, "void", fakes)
        assert enhanced[1][0] == original[1][0], "command"
        want_cl, got_cl = bytearray(original[1][1]), bytearray(enhanced[1][1])
        for off in (0xB8C8, 0xB8CC):
            a, b = struct.unpack_from("<f", want_cl, off)[0], struct.unpack_from("<f", got_cl, off)[0]
            assert a == b or _ulps(a, b) <= 1 or (a != a and b != b), (hex(off), a, b)
            got_cl[off:off + 4] = want_cl[off:off + 4]
        assert got_cl == want_cl
        # aim assist sees the angles: compare its records with the angles masked
        strip = lambda calls: [tuple(x if not isinstance(x, tuple) else x[:2] + x[3:5] + x[6:] for x in c)
                               for c in calls]
        assert strip(enhanced[3]) == strip(original[3])


def test_mouse_move_accumulates_in_double(env):
    """With the double angles in sync with the float ones, a turn of `counts` lands at float(previous - turn) computed
    in double: a yaw far from zero keeps every count's turn instead of rounding it to the float grid."""
    address = env.call("?CL_EnhancedViewAngles@@YAPEANXZ", [], ret="int64")[0]
    base = faithful.mouse_move_inputs()[0]
    # 36000 - 0.4 ulp: as a float it is 36000; one 0.1-sensitivity count (0.00066 degrees, 0.17 ulp) then crosses to
    # the next float down only if the residue was kept
    for previous, sens in ((36000.0 - 0.4 * 2.0 ** -8, 0.1), (36000.123456789, 1.5), (-7200.000001, 1.5), (12.5, 1.5)):
        for counts in (1, 2, 5):
            mx = _f32(counts * _f32(sens * _f32(0.0066 / 0.022)))
            cl = bytearray(base["args"][2])
            struct.pack_into("<Q", cl, 0xC0, 0)
            struct.pack_into("<i", cl, 0x10C, 0)
            cl[0xA34] = 0
            struct.pack_into("<I", cl, 0xD0, 0)
            struct.pack_into("<i", cl, 0xB8, 0)
            struct.pack_into("<f", cl, 0xB7D4, 0.0)
            struct.pack_into("<f", cl, 0xB8CC, _f32(previous))

            def setup(w, previous=previous):
                base["setup"](w)
                w.write(faithful.syms.va("kb_strafeActive"), b"\0")
                w.u32(faithful.syms.va("cls_frametime"), 4)
                w.write(address + 8, struct.pack("<d", previous))            # [0][1]: local client 0's yaw
                w.write(address + 32 + 4, struct.pack("<f", _f32(previous)))  # what was last written as float

            fakes = dict(base["fakes"])
            fakes[faithful.SCALE] = faithful._floats_out(mx, 0.0)
            fakes[faithful.GET_FLOAT] = faithful.ret_float({**{v: 0.022 for v in faithful.MOUSE_DVARS.values()}})
            fakes[faithful.GET_BOOL] = faithful.ret_bool({v: True for v in faithful.MOUSE_DVARS.values()})
            fakes["sub_142756F90"] = lambda mu: 0
            fakes["sub_1408A5010"] = lambda mu: 0
            _, buffers, _, _ = env.call(faithful.MOUSE_MOVE, [0, base["args"][1], bytes(cl)], "void", setup, fakes)
            yaw = struct.unpack_from("<f", buffers[1], 0xB8CC)[0]
            want = _f32(previous - _f32(0.022) * mx)
            assert yaw == want, (previous, counts, yaw, want)
