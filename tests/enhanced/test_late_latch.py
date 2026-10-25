"""P0021: the late latch (docs/late-latch.md).

What must hold:
- R_LateLatchTurnAxis turns a view by yaw (to the left, about the world's up) and pitch (down), keeping its roll, and
  stops the pitch at 85 degrees (or where it already is, beyond that);
- R_LateLatchRebuildViewParms makes the view matrix and every product of it exactly as the game's own view setup
  (141DE3510, R_SetupViewParms) makes them from the same origin, axis and projections;
- R_LateLatchWidenParms widens the half field of view by the margin at each edge, the projections' scale with it,
  and keeps the products consistent;
- a frame end to end: CL_RenderScene notes the main view (the scene R_RenderScene makes for it) and hands
  R_RenderScene a cull view widened by the margin, once the view follows the client's angles; the render thread's
  scene loop (141D46D30) then turns the scene's view parms by the counts read since the frame's take (times the
  degrees per count CL_MouseMove noted), copies them to the view's slot, makes the reprojection again (141DDC6C0,
  from the turned view and the previous view the frame used, with a copy of the refdef's fields), replaces the
  previous view the next frame starts from, and only then draws; with r_lateLatch off nothing changes;
- in anti-aliasing modes 4 and 5 the reprojection's jitter is put back to the frame's parity;
- while the gun's lists of the latched view are drawn (view-model mode 1 on that viewInfo) the code matrices are the
  ones the original makes from the view as the frame made it; with the mode off, from the turned one.
"""
import math
import random
import struct

import syms
from harness import SCRATCH, _MACHINES, program_write
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

TURN = "?R_LateLatchTurnAxis@@YAXPEAY02MMM@Z"
REBUILD = "?R_LateLatchRebuildViewParms@@YAXPEAD@Z"
WIDEN = "?R_LateLatchWidenParms@@YAXPEADM@Z"
RENDER = "?CL_RenderScene@@YAXPEBDHPEBX1PEAX@Z"
SCENES = "?sub_141D46D30@@YAXXZ"
GET_MATRIX = "?R_GetCodeMatrix@@YAPEBMPEADII@Z"
SETUP = 0x141DE3510            # R_SetupViewParms (refdef, out, skip jitter)
AA_MODE = 0x141D634D0
REGION, REGION_SIZE = 0x20000000, 0x400000
FRONTEND = REGION                      # frontend data (0xF9760)
SCENE_ARRAY = REGION + 0x100000        # scene S's viewInfo lands here
VIEW_SLOT = REGION + 0x2F0000
CODE_INPUT = REGION + 0x300000
CL = REGION + 0x310000
REFDEF = REGION + 0x1A0000             # refdef +0x1A680C must be mapped: 0x1A0000 + 0x1A6820 < 0x400000
BLOCKS = (REGION + 0x380000, REGION + 0x381000)
NEXT_FRONTEND = REGION + 0x390000 - 0x8A364   # only its +0x8A364 (the frame counter) is read
TARGETS = REGION + 0x3A0000
SCENE = 3
VIEW_INFO = SCENE_ARRAY
LATE_DVAR = 0x6300_0000_0100
TOTALS = {"taken": (100, 50), "read": (100, 50)}


def angles_to_axis(yaw, pitch, roll):
    sy, cy = math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
    sp, cp = math.sin(math.radians(pitch)), math.cos(math.radians(pitch))
    sr, cr = math.sin(math.radians(roll)), math.cos(math.radians(roll))
    return [[cp * cy, cp * sy, -sp],
            [sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, sr * cp],
            [cr * sp * cy + sr * sy, cr * sp * sy - sr * cy, cr * cp]]


def f32(values):
    return struct.pack(f"<{len(values)}f", *values)


def floats(data, offset, count):
    return list(struct.unpack_from(f"<{count}f", data, offset))


def _map(mu):
    if not any(start <= REGION < end for start, end, _ in mu.mem_regions()):
        mu.mem_map(REGION, REGION_SIZE)


def setup_parms(env, origin, axis, tan_x, tan_y):
    """The game's own view parms for a view (141DE3510 with the jitter skipped)."""
    refdef = bytearray(0xC8)
    struct.pack_into("<2f", refdef, 0x78, tan_x, tan_y)
    struct.pack_into("<3f", refdef, 0x88, *origin)
    struct.pack_into("<9f", refdef, 0xA4, *[v for row in axis for v in row])
    value, bufs, _, _ = env.machine.call(SETUP, [bytes(refdef), bytes(0x290), 1], "void",
                                         fakes={AA_MODE: lambda mu: 0})
    assert not isinstance(value, str), value
    return bufs[1]


def random_view(r):
    yaw, pitch, roll = r.uniform(-180, 180), r.uniform(-80, 80), r.choice([0.0, r.uniform(-10, 10)])
    origin = [r.uniform(-3000, 3000) for _ in range(3)]
    tan_x = math.tan(math.radians(r.uniform(30, 60)))
    return (yaw, pitch, roll), origin, tan_x, tan_x * 9 / 16


def axis_of(parms):
    v = floats(parms, 0x250, 9)
    return [v[0:3], v[3:6], v[6:9]]


def test_turn_axis(env):
    r = random.Random(2101)
    for _ in range(60):
        yaw, pitch, roll = r.uniform(-180, 180), r.choice([r.uniform(-84, 84), 86.0, -87.5]), r.uniform(-15, 15)
        dyaw, dpitch = r.uniform(-8, 8), r.uniform(-8, 8)
        axis = angles_to_axis(yaw, pitch, roll)
        _, bufs, _, _ = env.call(TURN, [f32([v for row in axis for v in row]), ("f", dyaw), ("f", dpitch)])
        got = struct.unpack("<9f", bufs[0])
        lo, hi = min(pitch, -85.0), max(pitch, 85.0)
        want = angles_to_axis(yaw + dyaw, min(max(pitch + dpitch, lo), hi), roll)
        for a, b in zip(got, [v for row in want for v in row]):
            assert abs(a - b) < 2e-4, (yaw, pitch, roll, dyaw, dpitch, got, want)


def test_rebuild_matches_setup(env):
    r = random.Random(2102)
    for _ in range(30):
        angles, origin, tan_x, tan_y = random_view(r)
        parms = setup_parms(env, origin, angles_to_axis(*angles), tan_x, tan_y)
        broken = bytearray(parms)
        for start, end in ((0x0, 0x40), (0xC0, 0x180), (0x1C0, 0x240)):
            broken[start:end] = bytes(end - start)
        _, bufs, _, _ = env.call(REBUILD, [bytes(broken)])
        assert bufs[0] == parms


def test_turned_parms_match_setup(env):
    r = random.Random(2103)
    for _ in range(30):
        angles, origin, tan_x, tan_y = random_view(r)
        parms = bytearray(setup_parms(env, origin, angles_to_axis(*angles), tan_x, tan_y))
        _, bufs, _, _ = env.call(TURN, [bytes(parms[0x250:0x274]), ("f", r.uniform(-5, 5)), ("f", r.uniform(-5, 5))])
        parms[0x250:0x274] = bufs[0]
        _, bufs, _, _ = env.call(REBUILD, [bytes(parms)])
        assert bufs[0] == setup_parms(env, origin, axis_of(bufs[0]), tan_x, tan_y)


def test_widen(env):
    r = random.Random(2104)
    for _ in range(20):
        angles, origin, tan_x, tan_y = random_view(r)
        parms = setup_parms(env, origin, angles_to_axis(*angles), tan_x, tan_y)
        margin = r.uniform(1, 8)
        _, bufs, _, _ = env.call(WIDEN, [parms, ("f", margin)])
        wide = bufs[0]
        new_x, new_y = floats(wide, 0x280, 2)
        assert abs(math.degrees(math.atan(new_x) - math.atan(tan_x)) - margin) < 1e-3
        assert abs(math.degrees(math.atan(new_y) - math.atan(tan_y)) - margin) < 1e-3
        for p in (0x40, 0x80, 0x180):
            assert abs(floats(wide, p, 1)[0] - floats(parms, p, 1)[0] * tan_x / new_x) < 1e-4
            assert abs(floats(wide, p + 0x14, 1)[0] - floats(parms, p + 0x14, 1)[0] * tan_y / new_y) < 1e-4
        assert wide[0x240:0x274] == parms[0x240:0x274]
        _, again, _, _ = env.call(REBUILD, [wide])
        assert again[0] == wide


# ---- a frame end to end ------------------------------------------------------------------------------------------

class Frame:
    def __init__(self, env, angles, origin, tan_x, tan_y, client_angles, enabled=True, turn=(-0.02, 0.015)):
        self.env = env
        self.parms = setup_parms(env, origin, angles_to_axis(*angles), tan_x, tan_y)
        self.angles, self.origin, self.tan = angles, origin, (tan_x, tan_y)
        self.client_angles = client_angles
        self.enabled = enabled
        self.turn = turn
        self.cull_seen = None
        self.calls = []
        self.aa_mode = 0          # 141D634D0's answer
        self.reprojected = 0      # 141DDC6C0's
        self.blocks = None        # the reprojection blocks' contents before the scene loop (4 matrices each)

    def regions(self, w):
        mu = w.m.mu
        _map(mu)
        mu.mem_write(REGION, bytes(REGION_SIZE))
        refdef = bytearray(0x1A6820)
        struct.pack_into("<i", refdef, 0x24, 7)
        struct.pack_into("<I", refdef, 0x38, 0x40000)
        struct.pack_into("<f", refdef, 0x74, 0.75)
        struct.pack_into("<2f", refdef, 0x78, *self.tan)
        struct.pack_into("<3f", refdef, 0x88, *self.origin)
        struct.pack_into("<9f", refdef, 0xA4, *floats(self.parms, 0x250, 9))
        struct.pack_into("<i", refdef, 0x1A681C, 1)
        mu.mem_write(REFDEF, bytes(refdef))
        mu.mem_write(VIEW_SLOT, self.parms)
        mu.mem_write(CL + 0xB8C8, struct.pack("<2f", self.client_angles[1], self.client_angles[0]))
        mu.mem_write(FRONTEND + 0xF6570, struct.pack("<Q", SCENE_ARRAY - SCENE * 0xD5F60))
        mu.mem_write(FRONTEND + 0xF9590, struct.pack("<Q", BLOCKS[0]))
        mu.mem_write(FRONTEND + 0xF95A0, struct.pack("<Q", BLOCKS[1]))
        mu.mem_write(VIEW_INFO + 0x400, struct.pack("<Q", CODE_INPUT))
        w.u64(self.env.data("r_lateLatch"), LATE_DVAR)
        w.u64(syms.va("frontEndDataOut"), FRONTEND)
        w.u32(syms.va("dword_14A333F74"), SCENE)
        w.u32(syms.va("dword_1546790B8"), 1)
        w.write(syms.va("r_previousViewParms"), bytes(0x290))

    def fakes(self):
        def get_bool(mu):
            return int(self.enabled and mu.reg_read(UC_X86_REG_RCX) == LATE_DVAR)

        def totals(phase):
            def fn(mu):
                read, taken = TOTALS["read" if phase == "render" else "taken"], TOTALS["taken"]
                regs = [mu.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]
                for reg, v in zip(regs, (read[0], read[1], taken[0], taken[1])):
                    mu.mem_write(reg, struct.pack("<q", v))
            return fn

        def turn(mu):
            mu.mem_write(mu.reg_read(UC_X86_REG_RDX), struct.pack("<f", self.turn[0]))
            mu.mem_write(mu.reg_read(UC_X86_REG_R8), struct.pack("<f", self.turn[1]))
            return 1

        def render_scene(mu):
            # R_RenderScene's part: the scene at index SCENE, a copy of the view; the previous view replaced
            self.cull_seen = bytes(mu.mem_read(mu.reg_read(UC_X86_REG_R9), 0x290))
            self.calls.append(("141DE3D80", mu.reg_read(UC_X86_REG_R8), mu.reg_read(UC_X86_REG_R9)))
            mu.mem_write(FRONTEND + 0xF6568, struct.pack("<ii", SCENE, SCENE + 1))
            mu.mem_write(VIEW_INFO, self.parms)
            program_write(mu, syms.va("r_previousViewParms"), self.parms)

        def reprojection(mu):
            sp = mu.reg_read(UC_X86_REG_RSP)
            stack = struct.unpack("<3Q", bytes(mu.mem_read(sp + 0x28, 24)))
            refdef = mu.reg_read(UC_X86_REG_R9)
            fields = (struct.unpack("<i", bytes(mu.mem_read(refdef + 0x24, 4)))[0],
                      struct.unpack("<I", bytes(mu.mem_read(refdef + 0x38, 4)))[0],
                      struct.unpack("<f", bytes(mu.mem_read(refdef + 0x74, 4)))[0],
                      struct.unpack("<i", bytes(mu.mem_read(refdef + 0x1A681C, 4)))[0])
            self.calls.append(("141DDC6C0", mu.reg_read(UC_X86_REG_RCX), mu.reg_read(UC_X86_REG_RDX),
                               mu.reg_read(UC_X86_REG_R8), refdef != REFDEF, fields, stack[0], stack[1],
                               bytes(mu.mem_read(stack[1], 0x290)), bytes(mu.mem_read(stack[2], 0x290))))
            return self.reprojected

        def draw(mu):
            self.calls.append(("141D4E220", mu.reg_read(UC_X86_REG_R8)))

        return {
            "Dvar_GetBool": get_bool,
            "?IN_RawMouseTotals@@YAXPEA_J000@Z": None,  # replaced per phase
            "?CL_LateLatchTurn@@YA_NHPEAM0@Z": turn,
            "CL_GetLocalClientGlobals": lambda mu: CL,
            "sub_141DE3D80": render_scene,
            "sub_141DDC6C0": reprojection,
            AA_MODE: lambda mu: self.aa_mode,
            "sub_141D4E220": draw,
            "_totals": totals,
        }

    def run(self, writes_before):
        """CL_RenderScene twice (the first notes the angles the second compares with), then the scene loop.
        Returns the image writes after all three, and the viewInfo's view parms afterwards."""
        fakes = self.fakes()
        totals = fakes.pop("_totals")
        fakes.pop("?IN_RawMouseTotals@@YAXPEA_J000@Z")
        writes = dict(writes_before)

        def setup(w):
            self.regions(w)
            for a, v in sorted(writes.items()):
                w.write(a, v)

        main = dict(fakes, **{"?IN_RawMouseTotals@@YAXPEA_J000@Z": totals("main")})
        value, _, w1, _ = self.env.call(RENDER, [REFDEF, 0, VIEW_SLOT, VIEW_SLOT, 0], "void", setup, main)
        assert not isinstance(value, str), value
        writes.update(w1)

        def setup_render(w):
            setup(w)
            mu = w.m.mu
            mu.mem_write(FRONTEND + 0xF6568, struct.pack("<ii", SCENE, SCENE + 1))
            mu.mem_write(VIEW_INFO, self.parms)
            w.u64(syms.va("backEndData"), FRONTEND)
            w.u32(syms.va("dword_1486BEEA0"), 2)
            # the main thread has begun the next frame: its frontend data, the other parity
            w.u64(syms.va("frontEndDataOut"), NEXT_FRONTEND)
            mu.mem_write(FRONTEND + 0x8A364, struct.pack("<I", 0x1234))
            mu.mem_write(NEXT_FRONTEND + 0x8A364, struct.pack("<I", 0x1235))
            w.u64(syms.va("unk_148705550"), TARGETS)
            mu.mem_write(TARGETS + 0x6CC0, struct.pack("<2H", 2560, 1440))
            if self.blocks:
                mu.mem_write(BLOCKS[0], self.blocks[0])
                mu.mem_write(BLOCKS[1], self.blocks[1])

        render = dict(fakes, **{"?IN_RawMouseTotals@@YAXPEA_J000@Z": totals("render")})
        self.calls.clear()
        value, _, w2, _ = self.env.call(SCENES, [], "void", setup_render, render)
        assert not isinstance(value, str), value
        writes.update(w2)
        mu = self.env.machine.mu
        return writes, bytes(mu.mem_read(VIEW_INFO, 0x290)), bytes(mu.mem_read(VIEW_SLOT, 0x290))


def previous_frame_writes(env, angles, origin, tan_x, tan_y, client_angles):
    """One CL_RenderScene so the next one has angles to compare with."""
    frame = Frame(env, angles, origin, tan_x, tan_y, client_angles)
    fakes = frame.fakes()
    totals = fakes.pop("_totals")
    fakes["?IN_RawMouseTotals@@YAXPEA_J000@Z"] = totals("main")
    value, _, writes, _ = env.call(RENDER, [REFDEF, 0, VIEW_SLOT, VIEW_SLOT, 0], "void", frame.regions, fakes)
    assert not isinstance(value, str), value
    return writes


def latch_case(env, r, enabled=True, configure=None):
    yaw, pitch = r.uniform(-170, 170), r.uniform(-60, 60)
    origin = [r.uniform(-2000, 2000) for _ in range(3)]
    tan_x = math.tan(math.radians(r.uniform(35, 55)))
    tan_y = tan_x * 9 / 16
    client = (r.uniform(-500, 500), r.uniform(-60, 60))
    turned = (r.uniform(1, 4), r.uniform(-2, 2))
    before = previous_frame_writes(env, (yaw, pitch, 0.0), origin, tan_x, tan_y, client)
    previous = setup_parms(env, origin, angles_to_axis(yaw, pitch, 0.0), tan_x, tan_y)
    frame = Frame(env, (yaw + turned[0], pitch + turned[1], 0.0), origin, tan_x, tan_y,
                  (client[0] + turned[0], client[1] + turned[1]), enabled)
    counts = (r.randrange(-90, 91), r.randrange(-90, 91))   # past the 1-degree margin too
    TOTALS["taken"] = (1000, 2000)
    TOTALS["read"] = (1000 + counts[0], 2000 + counts[1])
    if configure:
        configure(frame)
    writes, view_info, slot = frame.run(before)
    frame.previous = previous
    return frame, counts, writes, view_info, slot


def test_frame_latched(env):
    r = random.Random(2105)
    for _ in range(12):
        frame, counts, writes, view_info, slot = latch_case(env, r)
        yaw, pitch, roll = frame.angles
        dyaw = max(-1.0, min(1.0, counts[0] * frame.turn[0]))   # margin: 1 degree with no earlier latch
        dpitch = max(-1.0, min(1.0, counts[1] * frame.turn[1]))
        # the cull view handed to R_RenderScene: the view widened by the margin
        cull_x = floats(frame.cull_seen, 0x280, 1)[0]
        assert abs(math.degrees(math.atan(cull_x) - math.atan(frame.tan[0])) - 1.0) < 1e-3
        if dyaw == 0 and dpitch == 0:
            assert view_info == frame.parms and frame.calls == [("141D4E220", VIEW_INFO)]
            continue
        want_axis = angles_to_axis(yaw + dyaw, pitch + dpitch, roll)
        got_axis = axis_of(view_info)
        for a, b in zip([v for row in got_axis for v in row], [v for row in want_axis for v in row]):
            assert abs(a - b) < 2e-4
        assert view_info == setup_parms(env, frame.origin, got_axis, *frame.tan)
        assert slot == view_info
        names = [c[0] for c in frame.calls]
        assert names == ["141DDC6C0", "141D4E220"], names
        _, b1, b2, vi, fake_refdef, fields, input_ptr, cur_ptr, cur, prev = frame.calls[0]
        assert (b1, b2, vi, fake_refdef, fields, input_ptr, cur_ptr) == \
            (BLOCKS[0], BLOCKS[1], VIEW_INFO, True, (7, 0x40000, 0.75, 1), CODE_INPUT + 0x1D30, VIEW_INFO)
        assert cur == view_info
        assert prev == frame.previous   # the previous view as this frame's reprojection used it
        prev_va = syms.va("r_previousViewParms")
        assert b"".join(writes.get(prev_va + i, b"\0") for i in range(0x290)) == view_info  # unwritten: the zeros of setup


def test_frame_disabled(env):
    r = random.Random(2106)
    for _ in range(4):
        frame, counts, writes, view_info, slot = latch_case(env, r, enabled=False)
        assert view_info == frame.parms and slot == frame.parms
        assert frame.calls == [("141D4E220", VIEW_INFO)]
        assert frame.cull_seen == frame.parms


def test_gun_keeps_frame_view(env):
    r = random.Random(2107)
    checked = 0
    while checked < 6:
        frame, counts, writes, view_info, slot = latch_case(env, r)
        if view_info == frame.parms:
            continue
        checked += 1
        for mode in (1, 0):
            for index in (0xD5, 0xD6, 0xDD, 0xDE):
                state = bytearray(0x8200)
                state[0x1DF0:0x1DF0 + 0x290] = view_info           # what R_Set3D copied: the turned view
                struct.pack_into("<Q", state, 0x22B0, VIEW_INFO)
                struct.pack_into("<I", state, 0x22B8, mode)
                struct.pack_into("<I", state, 0x8100, r.choice([0, 1]))
                struct.pack_into("<4f", state, 0x22A0, *[r.uniform(-10, 10) for _ in range(4)])
                struct.pack_into("<4H", state, 0x228A, 5, 5, 5, 5)

                def setup(w):
                    for a, v in sorted(writes.items()):
                        w.write(a, v)

                _, got, _, _ = env.call(GET_MATRIX, [bytes(state), index, 0], "int64", setup)
                expected = bytearray(state)
                if mode == 1:
                    expected[0x1DF0:0x1DF0 + 0x290] = frame.parms     # the view as the frame made it
                _, want, _, _ = env.call(GET_MATRIX, [bytes(expected), index, 0], "int64", original=True)
                u = index - 0xD5
                assert got[0][u * 0x40:u * 0x40 + 0x40] == want[0][u * 0x40:u * 0x40 + 0x40], (mode, index)


def test_reprojection_jitter_parity(env):
    """AA modes 4 and 5: 141DDC6C0 run on the render thread jitters by the next frame's parity; the frame's own is
    put back: each matrix's first two columns move by its fourth times (+-0.5 * 2 / size) (here the frame is even,
    the next odd: -0.5 * 2 / 2560 and +0.5 * 2 / 1440). Not in other modes, nor when 141DDC6C0 says the blocks are
    unused."""
    r = random.Random(2108)
    for aa_mode, reprojected in ((4, 1), (5, 1), (3, 1), (4, 0)):
        blocks = [f32([r.uniform(-2, 2) for _ in range(60)]) for _ in range(2)]

        def configure(frame, aa_mode=aa_mode, reprojected=reprojected, blocks=blocks):
            frame.aa_mode, frame.reprojected, frame.blocks = aa_mode, reprojected, blocks

        frame, counts, writes, view_info, slot = latch_case(env, r, configure=configure)
        if view_info == frame.parms:
            continue
        mu = env.machine.mu
        for block, before in zip(BLOCKS, blocks):
            got = floats(bytes(mu.mem_read(block, 0xF0)), 0, 60)
            want = floats(before, 0, 60)
            if aa_mode in (4, 5) and reprojected:
                for m in range(2):
                    for row in range(4):
                        i = m * 16 + row * 4
                        want[i] = struct.unpack("<f", struct.pack("<f", want[i] + want[i + 3] * (-0.5 * (2.0 / 2560))))[0]
                        want[i + 1] = struct.unpack("<f", struct.pack("<f", want[i + 1] + want[i + 3] * (0.5 * (2.0 / 1440))))[0]
            for a, b in zip(got, want):
                assert abs(a - b) < 1e-6, (aa_mode, reprojected, a, b)
