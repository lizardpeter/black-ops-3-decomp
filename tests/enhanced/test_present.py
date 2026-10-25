"""P0017, P0018, P0019: flip-model presentation, the frame-latency wait, the direct present (docs/presentation.md).

Each test runs the original and the enhanced function on the same inputs (the differential tests' cases, with the
COM model extended by the interfaces only the enhanced build uses) and checks the intended difference, and that
everything else is identical: the same calls with the same arguments in the same order, the same result, the same
writes to the exe's globals.

What must hold:
- the swap chain's creation sends the original description with DXGI_SWAP_EFFECT_FLIP_DISCARD and the flags
  FRAME_LATENCY_WAITABLE_OBJECT and, exactly when IDXGIFactory5 reports support, ALLOW_TEARING; when that is refused,
  the same without the waitable flag; when that is refused too, the original description; then takes the waitable
  object through IDXGISwapChain2 with the latency r_maxFrameLatency asks for (the GPU count if more; not set for 0);
- with a flip-model swap chain the present calls IDXGISwapChain::Present itself (no message, no AMD sleep), with sync
  interval 1 for r_vsync and DXGI_PRESENT_ALLOW_TEARING exactly for a windowed r_vsync 0 with tearing allowed; binds
  the eight render targets and the depth-stencil view it found back after the present and releases them; counts the
  present when it succeeded and a waitable object exists; the errors and 3D Vision are the original's; without flip
  model the present is the original;
- the resize passes the flags the swap chain was made with;
- IN_Frame first waits once per counted present (two refresh periods' timeout, 50 ms to 1 s, alertable), takes every
  pending signal after a timeout, waits for nothing once the swap chain changed (closing the object), then is the
  original;
"""
import random
import struct

import test_r_present as pres
import test_r_swapchain as sw
import test_in_frame as win
import syms
from com import ComModel
from harness import _MACHINES, SCRATCH, TLS_BLOCK, program_write
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

EXE_LO, EXE_HI = 0x140000000, 0x160000000
FAC5, SC2 = "ID3D11CommandList", "ID3D11Query"   # model kinds standing in for IDXGIFactory5 and IDXGISwapChain2
VIEW = "ID3D11View"
WAITABLE = 0xABC0
LATENCY_DVAR = 0x6300_0000_0030
REFRESH_DVAR = 0x6300_0000_0040
QI, RELEASE = 0, 2 * 8
CHECK_FEATURE, SET_LATENCY, GET_WAITABLE = 28 * 8, 31 * 8, 33 * 8
PRESENT, GET_FULLSCREEN, RESIZE_BUFFERS = 8 * 8, 11 * 8, 13 * 8
OM_SET, OM_GET = 33 * 8, 89 * 8
MSGWAIT = SCRATCH + 0x7E000   # fake code for MsgWaitForMultipleObjectsEx
# r_refreshRate -> the wait's timeout: two periods, rounded up, 50 ms to 1 s
TIMEOUTS = {60.0: 50, 240.0: 50, 10.0: 200, 30.0: 67, 1.0: 1000, 0.0: 50, 500.0: 50, -60.0: 50, 1.5: 1000, 2.5: 800}


def regs(mu):
    return [mu.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8)]


def record(mu, *values):
    _MACHINES[id(mu)].observed.append(values)


def run_both(env, symbol, args, ret, setup, fakes):
    hooks = {va: fn for s, fn in fakes.items() for va in env.at(s)}
    original = env.machine.call(env.original(symbol), args, ret, setup, hooks)
    enhanced = env.call(symbol, args, ret, setup, fakes)
    return original, enhanced


def exe_writes(writes):
    return {a: v for a, v in writes.items() if EXE_LO <= a < EXE_HI}


def u32(writes, va, default):
    if va not in writes:
        return default
    return struct.unpack("<I", b"".join(writes.get(va + i, b"\0") for i in range(4)))[0]


def u64(writes, va, default):
    if va not in writes and va + 4 not in writes:
        return default
    return struct.unpack("<Q", b"".join(writes.get(va + i, b"\0") for i in range(8)))[0]


# ---- the swap chain's creation --------------------------------------------------------------------------------

def creation_case(r):
    c = {
        "qi_hr": r.choice([0] * 12 + [0x80004002]), "adapter_hr": 0, "factory_hr": 0, "create_hr": 0,
        "old_swapchain": r.choice([0, 1]), "output": r.choice([0, 1]), "hmonitor": 0x10001, "monitor_ok": 1,
        "monitor_rect": (0, 0, 2560, 1440), "metrics": {0: 1920, 1: 1080}, "is_fullscreen": r.choice([0, 1]),
        "backbuffers": r.choice([2, 3]), "new_size": (1280, 720),
        "factory5": r.choice([0, 1, 1]), "tearing": r.choice([0, 1]), "flip_ok": r.choice([0, 1, 1, 1]),
        "waitable_ok": r.choice([0, 1, 1]), "swapchain2": r.choice([0, 1, 1]), "latency": r.choice([0, 1, 2, 4]),
        "gpus": r.choice([1, 2, 4]), "create_status": r.choice([0, 0, 1]), "fullscreen": r.choice([0, 1]),
    }
    return c


def creation_setup(c, box):
    def apply(w):
        sigs = dict(sw.SIGS)
        sigs.update({(sw.FAC, QI): "pp", (FAC5, CHECK_FEATURE): "ipi", (FAC5, RELEASE): "", (sw.SWC, QI): "pp",
                     (SC2, SET_LATENCY): "i", (SC2, GET_WAITABLE): "", (SC2, RELEASE): ""})
        dumps = dict(sw.DUMPS)
        dumps.update({(sw.FAC, QI): {0: 16}, (sw.SWC, QI): {0: 16}})

        def qi(call):
            if c["qi_hr"]:
                return c["qi_hr"]
            return call.out_object(1, sw.UNK) and 0

        def parent(kind):
            return lambda call: call.out_object(1, kind) and 0

        def containing_output(call):
            if c["output"]:
                call.out_object(0, sw.OUT)
            else:
                call.write(call.arg(0), struct.pack("<Q", 0))
            return 0

        def output_desc(call):
            call.write(call.arg(0), bytes(0x58) + struct.pack("<Q", c["hmonitor"]))
            return 0

        def fullscreen_state(call):
            call.write(call.arg(0), struct.pack("<I", c["is_fullscreen"]))
            return 0

        def factory_qi(call):
            if not c["factory5"]:
                call.write(call.arg(1), struct.pack("<Q", 0))
                return 0x80004002
            call.write(call.arg(1), struct.pack("<Q", box[1]))
            return 0

        def check_feature(call):
            call.write(call.arg(1), struct.pack("<I", c["tearing"]))
            return 0

        def swapchain_qi(call):
            if not c["swapchain2"]:
                return 0x80004002
            call.write(call.arg(1), struct.pack("<Q", box[2]))
            return 0

        model = ComModel(sigs, {(sw.DEV, QI): qi, (sw.UNK, sw.GET_PARENT): parent(sw.ADP),
                                (sw.ADP, sw.GET_PARENT): parent(sw.FAC), (sw.SWC, 15 * 8): containing_output,
                                (sw.OUT, 7 * 8): output_desc, (sw.SWC, 11 * 8): fullscreen_state,
                                (sw.FAC, QI): factory_qi, (FAC5, CHECK_FEATURE): check_feature,
                                (sw.SWC, QI): swapchain_qi, (SC2, GET_WAITABLE): lambda call: WAITABLE}, dumps)
        model.install(w.m)
        box[0] = model
        box[1] = model.new(FAC5)
        box[2] = model.new(SC2)
        w.u64(syms.va("dx_device"), model.new(sw.DEV))
        w.u64(syms.va("dx_context"), model.new(sw.CTX))
        w.u64(syms.va("dx_swapChain"), model.new(sw.SWC) if c["old_swapchain"] else 0)
        w.u64(syms.va("g_hWnd"), sw.HWND)
        w.u64(syms.va("g_hWndInput"), 0x0003_0099)
        w.u64(syms.va("r_backBufferCount"), sw.BACKBUFFER_DVAR)
        w.u64(syms.va("r_fullscreen"), sw.FULLSCREEN_DVAR)
        w.u64(syms.va("r_maxFrameLatency"), LATENCY_DVAR)
        w.u32(syms.va("dx_gpuCount"), c["gpus"])
        w.u32(syms.va("dx_monitorCount"), 1)
        w.u32(syms.va("dx_modeCount"), 0)
    return apply


def creation_fakes(c, box):
    def send(mu):
        hwnd, msg, wparam, lparam = [mu.reg_read(x) for x in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8)] + [
            mu.reg_read(__import__("unicorn").x86_const.UC_X86_REG_R9)]
        desc = bytes(mu.mem_read(lparam, 0x48))
        record(mu, "SendMessageA", hwnd, msg & 0xFFFFFFFF, box[0].objects.get(wparam, (None, wparam))[1], desc)
        effect, flags = struct.unpack_from("<II", desc, 0x3C)
        if effect == 4 and not c["flip_ok"]:
            return 0x887A0001
        if flags & 0x40 and not c["waitable_ok"]:
            return 0x887A0001
        program_write(mu, syms.va("dx_swapChain"), struct.pack("<Q", box[0].new(sw.SWC, mu)))
        return c["create_status"]

    def get_int(mu):
        p = regs(mu)[0]
        record(mu, "Dvar_GetInt", p)
        return c["latency"] if p == LATENCY_DVAR else c["backbuffers"]

    fakes = sw.create_fakes(c, box)
    fakes.update({"USER32.dll!SendMessageA": send, "Dvar_GetInt": get_int,
                  "KERNEL32.dll!CloseHandle": lambda mu: (record(mu, "CloseHandle", regs(mu)[0]), 1)[1]})
    return fakes


def test_creation(env):
    r = random.Random(17)
    for _ in range(200):
        c = creation_case(r)
        box = [None, None, None]
        args = [sw.parms_bytes(r, c["fullscreen"])]
        o, e = run_both(env, "?sub_141DAB250@@YAJPEBUGfxWindowParms@@@Z", args, "int", creation_setup(c, box),
                        creation_fakes(c, box))
        o_sends = [x for x in o[3] if x[0] == "SendMessageA"]
        e_sends = [x for x in e[3] if x[0] == "SendMessageA"]
        if not o_sends:  # the device's QueryInterface failed: nothing else happens in either
            assert e[0] == o[0] and e[3] == o[3], (e, o)
            continue
        desc = o_sends[0][4]
        flags = struct.unpack_from("<I", desc, 0x40)[0]
        tearing = bool(c["factory5"] and c["tearing"])
        flip = desc[:0x3C] + struct.pack("<II", 4, flags | 0x40 | (0x800 if tearing else 0)) + desc[0x44:]
        expected = [flip]
        if not c["flip_ok"] or not c["waitable_ok"]:
            expected.append(flip[:0x40] + struct.pack("<I", flags | (0x800 if tearing else 0)) + flip[0x44:])
            if not c["flip_ok"]:
                expected.append(desc)
        assert [s[4] for s in e_sends] == expected, (c, [s[4].hex() for s in e_sends])
        made_flip = c["flip_ok"] == 1
        made_flags = (flags | (0x800 if tearing else 0) | (0x40 if c["waitable_ok"] else 0)) if made_flip else flags
        assert u32(e[2], env.data("r_swapChainFlags"), 2) == made_flags
        assert (e[2].get(env.data("r_flipModel"), b"\0") == b"\x01") == made_flip
        assert (e[2].get(env.data("r_flipAllowTearing"), b"\0") == b"\x01") == (made_flip and tearing)
        com = [x for x in e[3] if x[0] == "com" and x[1] in (FAC5, SC2)]
        waitable = made_flip and c["waitable_ok"] and c["swapchain2"]
        want = []
        if waitable:
            if c["latency"]:
                want.append(("com", SC2, SET_LATENCY, 2, max(c["latency"], c["gpus"])))
            want += [("com", SC2, GET_WAITABLE, 2), ("com", SC2, RELEASE, 2)]
        if c["factory5"]:
            want = [("com", FAC5, CHECK_FEATURE, 1, 0, ("ptr",), 4), ("com", FAC5, RELEASE, 1)] + want
        assert com == want, (c, com, want)
        assert u64(e[2], env.data("s_frameLatencyWaitable"), 0) == (WAITABLE if waitable else 0)
        # everything else is the original's
        def rest(calls):
            return [x for x in calls if x[0] != "SendMessageA" and not (x[0] == "com" and x[1] in (FAC5, SC2))
                    and not (x[0] == "com" and x[2] == QI and x[1] in (sw.FAC, sw.SWC))
                    and not (x[0] == "Dvar_GetInt" and x[1] == LATENCY_DVAR)]
        assert rest(e[3]) == rest(o[3])
        # the description that was taken makes the same swap chain object, so the results and globals match
        assert e[0] == o[0]
        assert exe_writes(e[2]) == exe_writes(o[2])


# ---- the present -------------------------------------------------------------------------------------------------

def present_setup(c, box):
    def apply(w):
        sigs = {(pres.DEV, pres.GET_REMOVED_REASON): "", ("IDXGISwapChain", PRESENT): "ii",
                ("IDXGISwapChain", GET_FULLSCREEN): "pp", ("ID3D11DeviceContext", OM_GET): "ipp",
                ("ID3D11DeviceContext", OM_SET): "ipp", (VIEW, RELEASE): ""}
        dumps = {("ID3D11DeviceContext", OM_SET): {1: 64}}

        def om_get(call):
            views = [box[1] if i == 0 and c["rtv"] else (box[2] if i == 3 and c["rtv2"] else 0) for i in range(8)]
            call.write(call.arg(1), struct.pack("<8Q", *views))
            call.write(call.arg(2), struct.pack("<Q", box[3] if c["dsv"] else 0))
            return 0

        def fullscreen(call):
            call.write(call.arg(0), struct.pack("<I", c["fs"]))
            return 0

        model = ComModel(sigs, {(pres.DEV, pres.GET_REMOVED_REASON): lambda call: c["reason"],
                                ("IDXGISwapChain", PRESENT): lambda call: c["hr"] & 0xFFFFFFFF,
                                ("IDXGISwapChain", GET_FULLSCREEN): fullscreen,
                                ("ID3D11DeviceContext", OM_GET): om_get}, dumps)
        model.install(w.m)
        w.u64(syms.va("dx_device"), model.new(pres.DEV))
        swc = model.new("IDXGISwapChain")
        w.u64(syms.va("dx_swapChain"), swc if c["swapchain"] else 0)
        w.u64(syms.va("dx_context"), model.new("ID3D11DeviceContext"))
        box[1], box[2], box[3] = model.new(VIEW), model.new(VIEW), model.new(VIEW)
        for name, p in pres.DVARS.items():
            w.u64(syms.va(name), p)
        w.write(syms.va("dx_nvapiInitialized"), bytes([c["nvapi"]]))
        w.u32(syms.va("dx_gpuCount"), c["gpus"])
        w.u32(syms.va("s_lastAfrIndex"), c["last_afr"])
        w.write(syms.va("dx_afrIndexRepeated"), bytes([c["repeated"]]))
        w.u32(syms.va("dx_remoteScreenUpdateNesting"), c["nesting"])
        w.u32(syms.va("dx_vendor"), c["vendor"])
        w.u64(syms.va("g_hWnd"), pres.HWND)
        w.u64(syms.va("dx_stereoHandle"), pres.STEREO if c["stereo"] else 0)
        w.write(syms.va("dx_stereoActivated"), bytes([c["was_active"]]))
        w.write(TLS_BLOCK + 0x10, b"\x01")
        w.u64(TLS_BLOCK + 0x20, 0x5C0BE000)
        w.write(box[0]("r_flipModel"), bytes([c["flip"]]))
        w.write(box[0]("r_flipAllowTearing"), bytes([c["tearing"]]))
        w.u64(box[0]("s_frameLatencyWaitable"), WAITABLE if c["waitable"] else 0)
        w.u32(box[0]("s_presentCount"), 41)
    return apply


def test_present(env):
    r = random.Random(46721)
    data = env.data
    for inp in pres.inputs()[:240]:
        c = dict(inp["case"])
        c.update({"flip": r.choice([0, 1, 1]), "tearing": r.choice([0, 1]), "waitable": r.choice([0, 1]),
                  "swapchain": r.choice([1, 1, 1, 0]), "fs": r.choice([0, 1]), "rtv": r.choice([0, 1, 1]),
                  "rtv2": r.choice([0, 1]), "dsv": r.choice([0, 1])})
        box = [data, 0, 0, 0]
        o, e = run_both(env, "?sub_141D46720@@YAXXZ", [], "void", present_setup(c, box), pres.fakes(c))
        flip = c["flip"] and c["swapchain"]
        if not flip:
            assert e[3] == o[3] and exe_writes(e[2]) == exe_writes(o[2]), c
            continue
        hr = c["hr"] & 0xFFFFFFFF
        sync = 1 if c["vsync"] else 0
        com = [x for x in e[3] if x[0] == "com" and x[1] in ("IDXGISwapChain", "ID3D11DeviceContext", VIEW)]
        want = []
        if not c["vsync"] and c["tearing"]:
            want.append(("com", "IDXGISwapChain", GET_FULLSCREEN, 2, ("ptr",), 0))
        views = [box[1] if c["rtv"] else 0, 0, 0, box[2] if c["rtv2"] else 0, 0, 0, 0, 0]
        dsv = box[3] if c["dsv"] else 0
        objid = {box[1]: 4, box[2]: 5, box[3]: 6}
        want.append(("com", "ID3D11DeviceContext", OM_GET, 3, 8, ("ptr",), ("ptr",)))
        tear = 0x200 if (not c["vsync"] and c["tearing"] and not c["fs"]) else 0
        want.append(("com", "IDXGISwapChain", PRESENT, 2, sync, tear))
        want.append(("com", "ID3D11DeviceContext", OM_SET, 3, 8, ("bytes", struct.pack("<8Q", *views)),
                     ("obj", 6) if dsv else 0))
        want += [("com", VIEW, RELEASE, objid[v]) for v in views if v]
        if dsv:
            want.append(("com", VIEW, RELEASE, 6))
        assert com == want, (c, com, want)
        assert not [x for x in e[3] if x[0] in ("SendMessageA", "Sleep")]
        counted = c["waitable"] and hr < 0x80000000
        assert u32(e[2], data("s_presentCount"), 41) == (42 if counted else 41)

        def rest(calls, enhanced):
            out = [x for x in calls if not (x[0] == "com" and x[1] in ("IDXGISwapChain", "ID3D11DeviceContext", VIEW))]
            return [x for x in out if x[0] not in ("SendMessageA", "Sleep")
                    and not (x[0] == "Dvar_GetFloat" and x[1] == "r_refreshRate")]
        assert rest(e[3], True) == rest(o[3], False), c
        assert exe_writes(e[2]) == exe_writes(o[2]), c


# ---- the resize ----------------------------------------------------------------------------------------------

def test_resize_flags(env):
    r = random.Random(13)
    for inp in sw.resize_inputs()[:40]:
        flags = r.choice([2, 2 | 0x40, 2 | 0x40 | 0x800, 2 | 0x800])
        setup = inp["setup"]

        def both_setup(w, setup=setup, flags=flags):
            setup(w)
            w.u32(env.data("r_swapChainFlags"), flags)
        o, e = run_both(env, "?sub_141DAD0C0@@YAXXZ", inp["args"], "void", both_setup, inp["fakes"])
        resize_o = [x for x in o[3] if x[0] == "com" and x[2] == RESIZE_BUFFERS]
        resize_e = [x for x in e[3] if x[0] == "com" and x[2] == RESIZE_BUFFERS]
        assert [x[-1] for x in resize_o] == [2] * len(resize_o)
        assert [x[:-1] for x in resize_e] == [x[:-1] for x in resize_o]
        assert [x[-1] for x in resize_e] == [flags] * len(resize_e)
        assert [x for x in e[3] if x not in resize_e] == [x for x in o[3] if x not in resize_o]
        assert e[1] == o[1] and exe_writes(e[2]) == exe_writes(o[2])


# ---- IN_Frame's wait -----------------------------------------------------------------------------------------

def test_frame_wait(env):
    r = random.Random(32)
    data = env.data
    for inp in win.frame_inputs()[:200]:
        presented = r.randint(0, 6)
        waited = presented - r.choice([0, 1, 1, 2, 3])
        script = [r.choice([0, 0, 0, 0, 0x102, 0xC0]) for _ in range(12)]
        resync = r.choice([0, 0, 1])
        same = r.choice([1, 1, 1, 0])
        has = r.choice([1, 1, 0])
        hz = r.choice(sorted(TIMEOUTS))
        swapchain = 0x7777_0000

        state = {}

        def setup(w, base=inp["setup"]):
            base(w)
            state["script"] = list(script)
            w.u64(syms.va("dx_swapChain"), swapchain)
            w.u64(syms.va("r_refreshRate"), REFRESH_DVAR)
            w.u64(data("s_frameLatencyWaitable"), WAITABLE if has else 0)
            w.u64(data("s_frameLatencySwapChain"), swapchain if same else 0x1234)
            w.u32(data("s_presentCount"), presented)
            w.u32(data("s_waitedPresentCount"), waited & 0xFFFFFFFF)
            w.write(data("s_resyncFrameLatency"), bytes([resync]))

        def wait(mu):
            h, ms, alertable = regs(mu)
            record(mu, "Wait", h, ms & 0xFFFFFFFF, alertable & 0xFFFFFFFF)
            return state["script"].pop(0) if state["script"] else 0x102  # no signal left: the wait times out

        fakes = dict(inp["fakes"])
        fakes.update({
            "KERNEL32.dll!WaitForSingleObjectEx": wait,
            "KERNEL32.dll!CloseHandle": lambda mu: (record(mu, "CloseHandle", regs(mu)[0]), 1)[1],
            "Dvar_GetFloat": lambda mu: (record(mu, "Dvar_GetFloat", regs(mu)[0]),
                                         mu.reg_write(__import__("unicorn").x86_const.UC_X86_REG_XMM0,
                                                      struct.unpack("<I", struct.pack("<f", hz))[0]))[0],
        })
        o, e = run_both(env, "?IN_Frame@@YAXXZ", [], "void", setup, fakes)
        n = len([x for x in e[3] if x[0] in ("Wait", "CloseHandle", "Dvar_GetFloat")])
        head, tail = e[3][:n], e[3][n:]
        assert tail == o[3], (tail, o[3])
        assert exe_writes(e[2]) == exe_writes(o[2])
        if not has:
            assert head == []
            continue
        if not same:
            assert head == [("CloseHandle", WAITABLE)]
            assert u64(e[2], data("s_frameLatencyWaitable"), WAITABLE) == 0
            continue
        if resync:
            want, k = [], 0
            while True:  # every pending signal (0), past I/O completions (0xC0), until anything else
                result = script[k] if k < len(script) else 0x102
                want.append(("Wait", WAITABLE, 0, 1))
                k += 1
                if result not in (0, 0xC0):
                    break
            assert head == want, (head, want)
            assert u32(e[2], data("s_waitedPresentCount"), waited & 0xFFFFFFFF) == presented
            continue
        timeout = TIMEOUTS[hz]
        want, k, count = [("Dvar_GetFloat", REFRESH_DVAR)], 0, waited
        timed_out = False
        while count != presented:
            count += 1
            while True:
                result = script[k] if k < len(script) else 0x102
                k += 1
                want.append(("Wait", WAITABLE, timeout, 1))
                if result != 0xC0:
                    break
            if result != 0:
                timed_out = True
                break
        assert head == want, (head, want, hz)
        assert u32(e[2], data("s_waitedPresentCount"), waited & 0xFFFFFFFF) == presented
        assert (e[2].get(data("s_resyncFrameLatency"), bytes([resync])) == b"\x01") == timed_out
