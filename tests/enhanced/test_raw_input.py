"""P0013 and P0014: mouse input and the window thread wake on input (enhanced/win32/win_input.cpp, docs/input.md).

What must hold:
- every relative raw mouse report made while the game window is in front is counted exactly, in 64 bits; absolute
  reports, other devices' reports and everything made while another window is in front are not counted;
- taking the counts returns them clamped to int and clears them;
- IN_MouseMove always takes the counts; it hands them to CL_MouseEvent exactly as the original does when the game is
  in front, and throws them away (no call) when it isn't or the system is suspended. In front it is call for call and
  write for write the original, on the faithful test's inputs;
- the raw input thread waits with MsgWaitForMultipleObjectsEx(0, NULL, 10, QS_RAWINPUT, MWMO_INPUTAVAILABLE) instead
  of Sleep(1), and falls back to Sleep(1) without it; it exits and clears its slots and the quit flag as the original;
- the window thread waits with MsgWaitForMultipleObjectsEx(0, NULL, 1, QS_ALLINPUT, 0) where the original sleeps,
  and is otherwise call for call the original on the faithful test's inputs; it falls back to Sleep(1) without it.
"""
import random
import struct

import syms
import test_win_input as faithful
from harness import SCRATCH, _MACHINES, program_write
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

READ = "?IN_ReadRawInput@@YAXXZ"
TAKE = "?IN_TakeRawMouse@@YAXPEAH0@Z"
MOVE = faithful.MOUSE_MOVE
THREAD = faithful.THREAD
WINDOW = faithful.WINDOW_THREAD
WAIT = SCRATCH + 0x70000  # fake MsgWaitForMultipleObjectsEx: hooked, never executed
USER32 = 0x7FF8_0000_0000
QS_RAWINPUT, QS_ALLINPUT, MWMO_INPUTAVAILABLE = 0x400, 0x4FF, 4


def regs(mu):
    return [mu.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]


def stack_arg(mu, i):
    return struct.unpack("<Q", bytes(mu.mem_read(mu.reg_read(UC_X86_REG_RSP) + 8 + 8 * i, 8)))[0]


def record(mu, *values):
    _MACHINES[id(mu)].observed.append(values)


def q(written, addr):
    return struct.unpack("<q", b"".join(written[addr + i] for i in range(8)))[0]


def counters(env, dx, dy, extra=None):
    def setup(w):
        w.write(env.data("s_rawDx"), struct.pack("<q", dx))
        w.write(env.data("s_rawDy"), struct.pack("<q", dy))
        w.u64(syms.va("win_hWnd"), faithful.HWND_GAME)
        if extra:
            extra(w)
    return setup


def buffer_fake(batches):
    """GetRawInputBuffer returning the batches, then 0."""
    state = {"i": 0}

    def fn(mu):
        i = state["i"]
        state["i"] = i + 1
        batch = batches[i] if i < len(batches) else []
        at = regs(mu)[0]
        for kind, size, dx, dy, flags in batch:
            program_write(mu, at, faithful.record_bytes(kind, size, dx, dy, flags))
            at = (at + size + 7) & ~7
        return len(batch)
    return fn


def find_wait(present=True):
    return {"KERNEL32.dll!GetModuleHandleA": lambda mu: USER32,
            "KERNEL32.dll!GetProcAddress": lambda mu: (record(mu, "GetProcAddress", regs(mu)[0],
                                                              _MACHINES[id(mu)].read_cstr(regs(mu)[1])),
                                                       WAIT if present else 0)[1]}


def test_relative_reports_in_front_are_counted(env):
    r = random.Random(13)
    for _ in range(80):
        batches = [[(r.choice([0, 0, 0, 1, 2]), r.choice([48, 48, 52, 56]), r.choice([0, 1, -1, 300, -7000, 0x7FFFFFF0]),
                     r.choice([0, 2, -2, 150, -0x7FFFFFF0]), r.choice([0, 0, 1, 2, 3])) for _ in range(r.choice([1, 4, 12]))]
                   for _ in range(r.choice([1, 2, 3]))]
        start = (r.choice([0, 1 << 40, -5]), r.choice([0, -(1 << 40), 9]))
        fakes = {"USER32.dll!GetRawInputBuffer": buffer_fake(batches),
                 "USER32.dll!GetForegroundWindow": lambda mu: faithful.HWND_GAME}
        _, _, written, _ = env.call(READ, [], setup=counters(env, *start), fakes=fakes)
        want_x = start[0] + sum(dx for b in batches for kind, _, dx, _, fl in b if kind == 0 and not fl & 1)
        want_y = start[1] + sum(dy for b in batches for kind, _, _, dy, fl in b if kind == 0 and not fl & 1)
        got_x = q(written, env.data("s_rawDx")) if env.data("s_rawDx") in written else start[0]
        got_y = q(written, env.data("s_rawDy")) if env.data("s_rawDy") in written else start[1]
        assert (got_x, got_y) == (want_x, want_y), (batches, start, got_x, got_y)


def test_background_movement_is_not_counted(env):
    batches = [[(0, 48, 500, -300, 0), (0, 48, 7, 7, 0)], [(0, 48, 1, 1, 0)]]
    fakes = {"USER32.dll!GetRawInputBuffer": buffer_fake(batches),
             "USER32.dll!GetForegroundWindow": lambda mu: faithful.HWND_OTHER}
    _, _, written, _ = env.call(READ, [], setup=counters(env, 11, 22), fakes=fakes)
    assert env.data("s_rawDx") not in written and env.data("s_rawDy") not in written


def test_take_returns_clamps_and_clears(env):
    for start, want in (((37, -12), (37, -12)), ((1 << 40, -(1 << 40)), (0x7FFFFFFF, -0x7FFFFFFF)), ((0, 0), (0, 0))):
        _, bufs, written, _ = env.call(TAKE, [bytes(4), bytes(4)], setup=counters(env, *start))
        assert struct.unpack("<ii", bufs[0] + bufs[1]) == want
        assert all(q(written, env.data(n)) == 0 for n in ("s_rawDx", "s_rawDy") if env.data(n) in written)


def without(written, *addrs):
    drop = {a + i for a in addrs for i in range(8)}
    return {a: v for a, v in written.items() if a not in drop}


def test_mouse_move_matches_original_in_front_and_drops_otherwise(env):
    for inp in faithful.mouse_inputs():
        # the faithful setup puts the counts in win_rawMouseDx/Dy; the enhanced build takes them from s_rawDx/Dy
        state = {}

        def capture(w, inp=inp):
            inp["setup"](w)
            state["dx"], state["dy"] = (struct.unpack("<i", bytes(w.m.mu.mem_read(syms.va(n), 4)))[0]
                                        for n in ("win_rawMouseDx", "win_rawMouseDy"))
            w.write(env.data("s_rawDx"), struct.pack("<q", state["dx"]))
            w.write(env.data("s_rawDy"), struct.pack("<q", state["dy"]))

        hooks = {va: fn for s, fn in inp["fakes"].items() for va in env.at(s)}
        original = env.machine.call(env.original(MOVE), [], "void", capture, hooks)
        enhanced = env.call(MOVE, [], "void", capture, inp["fakes"])
        counts = (syms.va("win_rawMouseDx"), syms.va("win_rawMouseDy"), env.data("s_rawDx"), env.data("s_rawDy"),
                  env.data("s_takenTotalX"), env.data("s_takenTotalY"))
        made_event = any(c[0] == "CL_MouseEvent" for c in original[3])
        if made_event and -0x80000000 in (state["dx"], state["dy"]):
            # the 64-bit counts are clamped to +-0x7FFFFFFF: -2^31 is handed on as -0x7FFFFFFF
            event = [c for c in enhanced[3] if c[0] == "CL_MouseEvent"][0]
            assert event[4:6] == tuple(max(v, -0x7FFFFFFF) for v in (state["dx"], state["dy"]))
        elif made_event:
            assert enhanced[3] == original[3], (state, original[3], enhanced[3])
            assert without(enhanced[2], *counts) == without(original[2], *counts)
        else:
            # suspended or not in front: the original leaves the counts for later, the enhanced build drops them
            assert not any(c[0] == "CL_MouseEvent" for c in enhanced[3])
            assert without(enhanced[2], *counts) == without(original[2], *counts)
        # the counts are always taken, and added to the running totals the late latch reads (P0021)
        for n, k in (("s_rawDx", "dx"), ("s_rawDy", "dy")):
            assert (q(enhanced[2], env.data(n)) if env.data(n) in enhanced[2] else state[k]) == 0
        for n, k in (("s_takenTotalX", "dx"), ("s_takenTotalY", "dy")):
            assert (q(enhanced[2], env.data(n)) if env.data(n) in enhanced[2] else 0) == state[k]


def thread_fakes_with_wait(base, wait_args, present=True, sleep_key="KERNEL32.dll!Sleep"):
    """The faithful thread fakes, with MsgWaitForMultipleObjectsEx standing in for Sleep(1)."""
    fakes = dict(base)
    sleep = base[sleep_key]

    def wait(mu):
        args = (regs(mu)[0] & 0xFFFFFFFF, regs(mu)[1], regs(mu)[2] & 0xFFFFFFFF, regs(mu)[3] & 0xFFFFFFFF,
                stack_arg(mu, 4) & 0xFFFFFFFF)
        assert args == wait_args, args
        mu.reg_write(UC_X86_REG_RCX, 1)  # record it as the Sleep(1) it replaces
        sleep(mu)
        return 0x102  # WAIT_TIMEOUT
    fakes[WAIT] = wait
    fakes.update(find_wait(present))
    return fakes


def test_raw_input_thread_waits_for_input(env):
    r = random.Random(14)
    for _ in range(40):
        script, sleeps = faithful.thread_case(r)
        base = faithful.thread_fakes(script, sleeps)
        base["USER32.dll!GetForegroundWindow"] = lambda mu: faithful.HWND_GAME
        for present in (True, False):
            fakes = thread_fakes_with_wait(base, (0, 0, 10, QS_RAWINPUT, MWMO_INPUTAVAILABLE), present)
            _, _, written, observed = env.call(THREAD, [0x16], setup=counters(env, 0, 0, faithful.thread_setup(0, 0)),
                                               fakes=fakes)
            calls = [c for c in observed if c[0] in ("Sleep", "CreateWindowExA", "GetProcAddress")]
            assert calls[0][0] == "CreateWindowExA" and calls[0][2] == b"CoDBlackOpsInputs"
            assert calls[1] == ("GetProcAddress", USER32, b"MsgWaitForMultipleObjectsEx")
            assert [c for c in calls if c[0] == "Sleep"] == [("Sleep", 1)] * sleeps
            for name, slot in (("sys_threadHandle", 0x16), ("sys_threadFunc", 0x16)):
                assert q(written, syms.va(name) + 8 * slot) == 0
            assert syms.va("sys_rawInputThreadQuit") not in written or written[syms.va("sys_rawInputThreadQuit")] == b"\0"
            reads = sum(1 for c in observed if c[0] == "GetRawInputBuffer")
            want_x = sum(dx for b in script[:reads] for kind, _, dx, _, fl in b if kind == 0 and not fl & 1)
            got_x = q(written, env.data("s_rawDx")) if env.data("s_rawDx") in written else 0
            assert got_x == want_x, (present, script, sleeps, got_x, want_x, observed)


def test_window_thread_waits_for_messages_and_is_otherwise_original(env):
    for inp in faithful.window_inputs()[:80]:
        hooks = {va: fn for s, fn in inp["fakes"].items() for va in env.at(s)}
        original = env.machine.call(env.original(WINDOW), inp["args"], "void", inp["setup"], hooks)
        for present in (True, False):
            fakes = thread_fakes_with_wait(inp["fakes"], (0, 0, 1, QS_ALLINPUT, 0), present)
            enhanced = env.call(WINDOW, inp["args"], "void", inp["setup"], fakes)
            assert [c for c in enhanced[3] if c[0] != "GetProcAddress"] == original[3]
            assert enhanced[2] == original[2]
