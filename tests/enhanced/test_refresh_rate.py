"""P0009 and P0010: refresh rates above 240 Hz (docs/refresh-rate.md).

P0009: the enhanced registration must register r_refreshRate with the domain [1, 1000] and default 60, and make every
other registration exactly as the original does (same calls, same order, same arguments, same globals stored); P0021
adds r_lateLatch after them all.

P0010: GetAvailableRefreshRates must list the rates of modes past the first 128 of a monitor's list, highest first,
at most 128 of them; on every list of up to 128 modes, and on every faithful input whose answer lies in the first 128,
it must build exactly the original's table.
"""
import random
import struct

import test_lua_cod_luacalls as lua
import test_r_dvars as regs

R_REFRESH_RATE = 0x3727533B


def f32(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def both(env, symbol, inp, ret, fakes):
    """(original, enhanced) results of one input."""
    hooks = {va: fn for s, fn in fakes.items() for va in env.at(s)}
    original = env.machine.call(env.original(symbol), inp["args"], ret, inp.get("setup"), hooks)
    enhanced = env.call(symbol, inp["args"], ret, inp.get("setup"), fakes)
    return original, enhanced


def test_refresh_rate_domain(env):
    for inp in regs.inputs():
        original, enhanced = both(env, regs.SYM, inp, "void", inp["fakes"])
        want = [list(c) for c in original[3]]
        for c in want:
            if c[0] == "Dvar_RegisterFloat" and c[1] == R_REFRESH_RATE:
                assert c[3:6] == [f32(60.0), f32(1.0), f32(240.0)], c
                c[5] = f32(1000.0)
        # P0021: r_lateLatch (new) is registered last, default on, and stored in the enhanced DLL's own global
        want.append(["Dvar_RegisterBool", 0x4113CAB2, b"", 1, 0, b"", 0])
        assert [list(c) for c in enhanced[3]] == want
        late = env.data("r_lateLatch")
        exe = {a: v for a, v in enhanced[2].items() if not late <= a < late + 8}
        assert exe == original[2]
        stored = struct.unpack("<Q", b"".join(enhanced[2][late + i] for i in range(8)))[0]
        assert stored & ~0xFF_0000_0000 == 0x7F00_4113_CAB2, hex(stored)   # the fake's handle for it


def modes(entries):
    return [struct.pack("<7I", w, h, num, den, 28, 0, 0) for w, h, num, den in entries]


def listed(observed):
    return [c[1].decode() for c in observed if c[0] == "pushlstring"]


def run(env, mode_list, width, height, monitor=1, original=False):
    lists = [mode_list] + [[] for _ in range(7)]
    inp = {"args": [lua.lua_state([width, height, monitor])], "setup": lua.setup(lists)}
    o, e = both(env, lua.SYM, inp, "int", lua.FAKES)
    return o if original else e


def test_native_mode_past_128(env):
    # 9 smaller sizes x 15 rates come first; the native 2560x1440 modes sit at indexes 135..139
    small = [(w, h, r, 1) for w, h in lua.SIZES[:7] + [(1920, 1200), (2560, 1080)] for r in range(60, 75)]
    native = [(2560, 1440, r, 1) for r in (60, 120, 144, 240, 360)]
    mode_list = modes(small + native)
    assert len(mode_list) > 128
    assert listed(run(env, mode_list, 2560, 1440, original=True)[3]) == []
    got = run(env, mode_list, 2560, 1440)
    assert got[0] == 1 and listed(got[3]) == ["360.000", "240.000", "144.000", "120.000", "60.000"], listed(got[3])


def test_at_most_128_highest_first(env):
    mode_list = modes([(1920, 1080, r, 1) for r in range(60, 260)])
    got = listed(run(env, mode_list, 1920, 1080)[3])
    assert got == [f"{r}.000" for r in range(259, 131, -1)], got[:3]


def test_same_as_original_up_to_128_modes(env):
    for inp in lua.inputs():
        original, enhanced = both(env, lua.SYM, inp, "int", lua.FAKES)
        # inputs whose answer lies within the first 128 modes: the original's table is complete
        if len(listed(enhanced[3])) == len(listed(original[3])):
            assert enhanced[:2] == original[:2] and enhanced[3] == original[3]


def test_short_lists_match_exactly(env):
    r = random.Random(128)
    for _ in range(60):
        entries = sorted((*r.choice(lua.SIZES), *r.choice(lua.RATES)) for _ in range(r.randrange(129)))
        w, h = r.choice(lua.SIZES)
        o, e = run(env, modes(entries), w, h, original=True), run(env, modes(entries), w, h)
        assert e[:2] == o[:2] and e[3] == o[3]
