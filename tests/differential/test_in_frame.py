"""Hand-written cases for win32/win_input.cpp's IN_Frame.

IN_Frame reads three dvars (ClickToContinue, dvar_64DA587E, in_mouse), three mouse globals and the foreground window.
Each case sets the globals, gives the dvar pointers sentinel values that the faked Dvar_GetBool answers for, and fakes
the imports it calls: PostMessageA (recorded), GetForegroundWindow (a scripted answer per call) and ShowCursor, which
models the display counter (starting anywhere from -3 to 3) and records each call. IN_MouseMove and sub_1423BCD30 are
faked and recorded. The globals it writes (s_mouseActive, win_showCursor) are compared.

Mutation check: see the commit adding this file.
"""
import random

import syms
from harness import _MACHINES, program_write
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX

IN_FRAME = "?IN_Frame@@YAXXZ"
HWND, OTHER = 0x0001_0042, 0x0002_0077
DVARS = {"ClickToContinue": 0x6100_0000_0010, "dvar_64DA587E": 0x6100_0000_0020, "in_mouse": 0x6100_0000_0030}


def regs(mu):
    return [mu.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]


def record(mu, *values):
    _MACHINES[id(mu)].observed.append(values)


class State:
    """Per-case fake state, reset by the case's setup before each of the two runs."""

    def __init__(self, cursor, foreground, dvars):
        self.cursor0, self.foreground0, self.dvars = cursor, foreground, dvars

    def reset(self):
        self.cursor, self.foreground = self.cursor0, list(self.foreground0)


def show_cursor(state):
    def fn(mu):
        show = regs(mu)[0] & 0xFFFFFFFF
        state.cursor += 1 if show else -1
        record(mu, "ShowCursor", show, state.cursor)
        return state.cursor & 0xFFFFFFFF
    return fn


def foreground(state):
    def fn(mu):
        h = state.foreground.pop(0) if state.foreground else HWND
        record(mu, "GetForegroundWindow", h)
        return h
    return fn


def dvar_get_bool(state):
    def fn(mu):
        p = regs(mu)[0]
        name = next(n for n, v in DVARS.items() if v == p)
        record(mu, "Dvar_GetBool", name)
        return state.dvars[name]
    return fn


def frame_fakes(state):
    return {
        "Dvar_GetBool": dvar_get_bool(state),
        "USER32.dll!ShowCursor": show_cursor(state),
        "USER32.dll!GetForegroundWindow": foreground(state),
        "USER32.dll!PostMessageA": lambda mu: (record(mu, "PostMessageA", *regs(mu)), 1)[1],
        "?IN_MouseMove@@YAXXZ": lambda mu: record(mu, "IN_MouseMove"),
        "sub_1423BCD30": cursor_update(state),
    }


def cursor_update(state):
    # sub_1423BCD30 may shut the mouse down (IN_Frame reads s_mouseInitialized again after it)
    def fn(mu):
        record(mu, "sub_1423BCD30")
        if state.dvars.get("uninit"):
            program_write(mu, syms.va("s_mouseInitialized"), b"\x00")
    return fn


def frame_setup(state, initialized, app_active, mouse_active, show_cursor_flag):
    def apply(w):
        state.reset()
        for name, p in DVARS.items():
            w.u64(syms.va(name), p)
        w.write(syms.va("s_mouseInitialized"), bytes([initialized]))
        w.write(syms.va("s_mouseActive"), bytes([mouse_active]))
        w.u32(syms.va("win_appActive"), app_active)
        w.u32(syms.va("win_showCursor"), show_cursor_flag)
        w.u64(syms.va("win_hWnd"), HWND)
    return apply


def frame_inputs():
    r = random.Random(1423)
    out = []
    for _ in range(240):
        state = State(cursor=r.randint(-3, 3), foreground=[r.choice([HWND, HWND, OTHER]) for _ in range(3)],
                      dvars={n: r.choice([0, 1, 0x100]) for n in DVARS})
        state.dvars["uninit"] = r.choice([0, 0, 1])
        out.append({"args": [], "fakes": frame_fakes(state),
                    "setup": frame_setup(state, r.choice([0, 1, 1, 1]), r.choice([0, 1, 5]), r.choice([0, 1]),
                                         r.choice([0, 1]))})
    return out


CASES = [{"symbol": IN_FRAME, "ret": "void", "inputs": frame_inputs()}]
