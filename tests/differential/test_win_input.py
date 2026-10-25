"""Hand-written cases for win32/win_input.cpp (mouse input).

IN_MouseMove reads the OS and the client through imports and functions that are all faked here, identically for both
copies, and recorded with their arguments: GetForegroundWindow (the game window or another), GetCursorPos (inside,
left/right/above/below the window, corners), Dvar_GetInt (r_fullscreen 0/1/2), GetWindowRect, SetCursorPos,
ScreenToClient, timeGetTime (Sys_Milliseconds' base set or not, times either side of the 200 ms hysteresis),
CL_MouseEvent (result 0 or 1), the device-switch functions and CG_GetPredictedPlayerState (null, or a playerState with
the tested flag bit set or clear). The globals it reads are set per case: suspended, the raw counters (zero, either,
both, extreme values), the controller index, the device record (last device 0/1/2, times), the session mode bits and
table entry, and the int compared with 2. Every global written is compared.

sub_1423F4B70 (the raw input thread) runs to completion: GetRawInputBuffer is faked from a script of batches (written
into the buffer it is given; mouse, keyboard and HID records of varied sizes, so the 8-byte record alignment is
exercised; movement values including large and negative ones that wrap the 32-bit counters), Sleep sets the quit flag
after a scripted number of calls, and CreateWindowExA returns a fixed handle. The calls (class and window names,
parent, instance; GetRawInputBuffer's size and header size; Sleep's argument) and the globals written (counters,
window handle, thread slots, quit flag) are compared.

Mutation check: see the commit adding this file.
"""
import random
import struct

import syms
from harness import SCRATCH, _MACHINES, program_write
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

MOUSE_MOVE = "?IN_MouseMove@@YAXXZ"
THREAD = "?sub_1423F4B70@@YAXI@Z"
WINDOW_THREAD = "?sub_1423F49B0@@YAXI@Z"
HWND_GAME = 0x0000_0000_0003_0A12
HWND_OTHER = 0x0000_0000_0005_1F40
FULLSCREEN_DVAR = 0x6000_0000_02F0
PS = SCRATCH + 0x60000


def regs(mu):
    return [mu.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]


def record(mu, *values):
    _MACHINES[id(mu)].observed.append(values)


def stack_arg(mu, i):
    rsp = mu.reg_read(UC_X86_REG_RSP)
    return struct.unpack("<Q", bytes(mu.mem_read(rsp + 8 + 8 * i, 8)))[0]


def i32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v >> 31 else v


# ---- IN_MouseMove ----

def mouse_fakes(r):
    foreground = r.choice([HWND_GAME, HWND_GAME, HWND_GAME, HWND_OTHER])
    rect = r.choice([(0, 0, 1920, 1080), (100, 50, 1380, 770), (-1920, 0, 0, 1080), (0, 0, 0, 0)])
    cursor = r.choice([(500, 400), (rect[0] - 5, rect[1] + 3), (rect[2], rect[3]), (rect[2] + 40, rect[1] - 7),
                       (rect[0], rect[3] - 1), (rect[2] - 1, rect[3] + 1), (-30000, 30000)])
    fullscreen = r.choice([0, 1, 1, 2])
    times = [r.choice([1000, 5000, 5199, 5200, 5201, 900000]) for _ in range(2)]
    event_result = r.choice([0, 1, 1])
    f01050 = r.choice([0, 1])
    ps_choice = r.choice(["null", "set", "clear"])

    def get_cursor(mu):
        program_write(mu, regs(mu)[0], struct.pack("<ii", *cursor))
        return 1

    def get_rect(mu):
        hwnd, out = regs(mu)[0], regs(mu)[1]
        record(mu, "GetWindowRect", hwnd)
        program_write(mu, out, struct.pack("<4i", *rect))
        return 1

    def screen_to_client(mu):
        hwnd, p = regs(mu)[0], regs(mu)[1]
        x, y = struct.unpack("<ii", bytes(mu.mem_read(p, 8)))
        record(mu, "ScreenToClient", hwnd, x, y)
        program_write(mu, p, struct.pack("<ii", x - rect[0], y - rect[1]))
        return 1

    state = {}

    def foreground_window(mu):
        state["clock"] = iter(times + [times[-1]] * 4)  # the first call of every run: both copies see the same clock
        return foreground

    return {
        "USER32.dll!GetForegroundWindow": foreground_window,
        "USER32.dll!GetCursorPos": get_cursor,
        "USER32.dll!GetWindowRect": get_rect,
        "USER32.dll!SetCursorPos": lambda mu: (record(mu, "SetCursorPos", i32(regs(mu)[0]), i32(regs(mu)[1])), 1)[1],
        "USER32.dll!ScreenToClient": screen_to_client,
        "WINMM.dll!timeGetTime": lambda mu: next(state["clock"]),
        "Dvar_GetInt": lambda mu: fullscreen if regs(mu)[0] == FULLSCREEN_DVAR else 0x77,
        "CL_MouseEvent": lambda mu: (record(mu, "CL_MouseEvent", *(i32(v) for v in regs(mu)), i32(stack_arg(mu, 4))),
                                     event_result)[1],
        "sub_1422081C0": lambda mu: record(mu, "1422081C0", i32(regs(mu)[0]), regs(mu)[1] & 0xFF),
        "sub_141F01050": lambda mu: (record(mu, "141F01050", i32(regs(mu)[0])), f01050)[1],
        "sub_141720810": lambda mu: record(mu, "141720810", i32(regs(mu)[0]), i32(regs(mu)[1])),
        "CG_GetPredictedPlayerState": lambda mu: (record(mu, "CG_GetPredictedPlayerState", i32(regs(mu)[0])),
                                                  0 if ps_choice == "null" else PS)[1],
    }, ps_choice


def mouse_setup(r, ps_choice):
    suspended = r.choice([0, 0, 0, 0, 1])
    dx = r.choice([0, 0, 1, -1, 37, -2500, 0x7FFFFFFF, -0x80000000])
    dy = r.choice([0, 0, 1, -1, 12, 4000])
    controller = r.choice([0, 0, 1, 3])
    device = [r.choice([controller, controller, 2]), r.choice([0, 1]), r.choice([0, 1]), 0, 0,
              r.choice([0, 0, 1, 2]), r.choice([0, 4000, 4999, 5000, 5001, -10])]
    mode_bits = r.choice([0x2, 0x2, 0x1, 0xA, 0xE, 0x12, 0x3C2])
    mode_entry = r.choice([1, 1, 0, 2])
    unk = r.choice([0, 1, 2])
    time_init = r.choice([0, 1])
    flag = r.choice([0x20000000000000, 0x20000000000000 | 0x5, 0x10, 0])

    def apply(w):
        w.u32(syms.va("win_suspended"), suspended)
        w.u64(syms.va("win_hWnd"), HWND_GAME)
        w.u32(syms.va("win_rawMouseDx"), dx & 0xFFFFFFFF)
        w.u32(syms.va("win_rawMouseDy"), dy & 0xFFFFFFFF)
        w.u64(syms.va("r_fullscreen"), FULLSCREEN_DVAR)
        w.u32(syms.va("cl_inputDeviceController"), controller)
        w.write(syms.va("cl_inputDevice") + 0x24 * controller, struct.pack("<7i", *device))
        w.u32(syms.va("com_sessionModeState"), mode_bits)
        mode = (mode_bits << 28 & 0xFFFFFFFF)
        mode = (mode - (1 << 32) if mode >> 31 else mode) >> 28
        w.u32(syms.va("com_sessionModeInfo") + 0x18 * mode, mode_entry)
        w.u32(syms.va("unk_1494B2DC8"), unk)
        w.u32(syms.va("sys_timeInitialized"), time_init)
        w.u32(syms.va("sys_timeBase"), 777)
        w.u32(syms.va("win_windowCenterX"), 0x4444)
        w.u32(syms.va("win_windowCenterY"), 0x5555)
        w.write(PS, bytes(0x10) + struct.pack("<Q", flag if ps_choice == "set" else flag & ~0x20000000000000))
    return apply


def mouse_inputs():
    r = random.Random(1423)
    out = []
    for _ in range(400):
        fakes, ps_choice = mouse_fakes(r)
        out.append({"args": [], "setup": mouse_setup(r, ps_choice), "fakes": fakes})
    return out


# ---- the raw input thread ----

def record_bytes(kind, size, dx, dy, flags=0):
    header = struct.pack("<IIQQ", kind, size, 0x1234_5678, 0)
    body = struct.pack("<HHIIiiI", flags, 0, 0, 0, dx, dy, 0) if kind == 0 else bytes(24)
    blob = header + body
    return blob[:size] + bytes(max(0, size - len(blob)))


def thread_case(r):
    batches = []
    for _ in range(r.choice([0, 1, 2, 5])):
        recs = []
        for _ in range(r.choice([1, 1, 2, 6, 12])):
            kind = r.choice([0, 0, 0, 1, 2])
            size = r.choice([48, 48, 48, 41, 52, 56])
            recs.append((kind, size, r.choice([0, 1, -1, 300, -7000, 0x7FFFFFF0, -0x7FFFFFF0]),
                         r.choice([0, 2, -2, 150]), r.choice([0, 0, 1])))
        batches.append(recs)
    # the script: each GetRawInputBuffer call returns the next batch (an empty one ends a drain); Sleep k sets quit
    script = []
    for b in batches:
        script.append(b)
        if r.random() < 0.5:
            script.append([])
    sleeps_before_quit = r.choice([1, 1, 2, 3])
    return script, sleeps_before_quit


def thread_fakes(script, sleeps_before_quit):
    state = {}

    def create_window(mu):
        m = _MACHINES[id(mu)]
        state["call"], state["sleeps"] = 0, 0
        # DWORD and int arguments: only their low 32 bits are defined
        record(mu, "CreateWindowExA", regs(mu)[0] & 0xFFFFFFFF, m.read_cstr(regs(mu)[1]), m.read_cstr(regs(mu)[2]),
               regs(mu)[3] & 0xFFFFFFFF, *(stack_arg(mu, i) & 0xFFFFFFFF for i in range(4, 8)),
               *(stack_arg(mu, i) for i in range(8, 12)))
        return 0x0000_0000_000C_0DE0

    def get_buffer(mu):
        buf, size_p, header = regs(mu)[0], regs(mu)[1], regs(mu)[2]
        size = struct.unpack("<I", bytes(mu.mem_read(size_p, 4)))[0]
        record(mu, "GetRawInputBuffer", buf == syms.va("win_rawInputBuffer"), size, header & 0xFFFFFFFF)
        i = state["call"]
        state["call"] = i + 1
        batch = script[i] if i < len(script) else []
        at = buf
        for kind, rsize, dx, dy, flags in batch:
            program_write(mu, at, record_bytes(kind, rsize, dx, dy, flags))
            at = (at + rsize + 7) & ~7
        return len(batch)

    def sleep(mu):
        record(mu, "Sleep", regs(mu)[0] & 0xFFFFFFFF)
        state["sleeps"] += 1
        if state["sleeps"] >= sleeps_before_quit:
            program_write(mu, syms.va("sys_rawInputThreadQuit"), b"\x01")

    return {"USER32.dll!CreateWindowExA": create_window, "USER32.dll!GetRawInputBuffer": get_buffer,
            "KERNEL32.dll!Sleep": sleep}


def thread_setup(dx, dy):
    def apply(w):
        w.u64(syms.va("win_hInstance"), 0x1_4000_0000)
        w.u32(syms.va("win_rawMouseDx"), dx & 0xFFFFFFFF)
        w.u32(syms.va("win_rawMouseDy"), dy & 0xFFFFFFFF)
        w.u64(syms.va("sys_threadHandle") + 8 * 0x16, 0xAAAA)
        w.u64(syms.va("sys_threadFunc") + 8 * 0x16, 0xBBBB)
    return apply


def thread_inputs():
    r = random.Random(4870)
    out = []
    for _ in range(160):
        script, sleeps = thread_case(r)
        out.append({"args": [0x16], "setup": thread_setup(r.choice([0, 5, -0x7FFFFFFF]), r.choice([0, -3])),
                    "fakes": thread_fakes(script, sleeps)})
    return out


# ---- the window thread ----

def window_fakes(passes, sleeps_before_quit, cursor_start):
    """passes: per loop pass, the messages PeekMessageA returns (message, time)."""
    state = {}

    def create_window(mu):
        m = _MACHINES[id(mu)]
        state.update(pass_=0, i=0, sleeps=0, cursor=cursor_start)
        record(mu, "CreateWindowExA", regs(mu)[0] & 0xFFFFFFFF, m.read_cstr(regs(mu)[1]), m.read_cstr(regs(mu)[2]),
               regs(mu)[3] & 0xFFFFFFFF, *(stack_arg(mu, i) & 0xFFFFFFFF for i in range(4, 8)),
               *(stack_arg(mu, i) for i in range(8, 12)))
        return 0x0000_0000_0007_7770

    def peek(mu):
        msg_p, hwnd, lo, hi = regs(mu)
        record(mu, "PeekMessageA", hwnd, lo & 0xFFFFFFFF, hi & 0xFFFFFFFF, stack_arg(mu, 4) & 0xFFFFFFFF)
        msgs = passes[state["pass_"]] if state["pass_"] < len(passes) else []
        if state["i"] >= len(msgs):
            state["i"] = 0
            state["pass_"] += 1
            return 0
        message, time = msgs[state["i"]]
        state["i"] += 1
        mu.mem_write(msg_p, struct.pack("<QIIQQIiiI", hwnd, message, 0, 0x11, 0x22, time, 5, 6, 0))
        return 1

    def sleep(mu):
        record(mu, "Sleep", regs(mu)[0] & 0xFFFFFFFF)
        state["sleeps"] += 1
        # the window handle can change between passes (another thread recreates the window): the next pass must use
        # the new one
        program_write(mu, syms.va("win_hWnd"), struct.pack("<Q", 0x7770 + 0x10 * state["sleeps"]))
        if state["sleeps"] >= sleeps_before_quit:
            program_write(mu, syms.va("sys_windowThreadQuit"), b"\x01")

    def show_cursor(mu):
        show = regs(mu)[0] & 0xFFFFFFFF
        state["cursor"] += 1 if show else -1
        record(mu, "ShowCursor", show, state["cursor"])
        return state["cursor"] & 0xFFFFFFFF

    def message_of(mu):
        return struct.unpack("<I", bytes(mu.mem_read(regs(mu)[0] + 8, 4)))[0]

    return {"USER32.dll!CreateWindowExA": create_window, "USER32.dll!PeekMessageA": peek,
            "USER32.dll!TranslateMessage": lambda mu: (record(mu, "TranslateMessage", message_of(mu)), 1)[1],
            "USER32.dll!DispatchMessageA": lambda mu: (record(mu, "DispatchMessageA", message_of(mu)), 0)[1],
            "KERNEL32.dll!SetEvent": lambda mu: (record(mu, "SetEvent", regs(mu)[0]), 1)[1],
            "KERNEL32.dll!Sleep": sleep, "USER32.dll!ShowCursor": show_cursor}


def window_setup(show, unk):
    def apply(w):
        w.u64(syms.va("win_hInstance"), 0x1_4000_0000)
        w.u32(syms.va("win_style"), 0xCC0000)
        w.u32(syms.va("win_x"), 3)
        w.u32(syms.va("win_y"), 22)
        w.u32(syms.va("win_width"), 1936)
        w.u32(syms.va("win_height"), 1119)
        w.u64(syms.va("sys_quitEvent"), 0x5EE)
        w.u32(syms.va("win_showCursor"), show)
        w.u32(syms.va("unk_1490E7E44"), unk)
        w.u64(syms.va("sys_threadHandle") + 8 * 0x15, 0xAAAA)
        w.u64(syms.va("sys_threadFunc") + 8 * 0x15, 0xBBBB)
    return apply


def window_inputs():
    r = random.Random(1490)
    out = []
    for _ in range(160):
        passes = [[(r.choice([0x100, 0x101, 0x201, 0x0F, 0x8043, 0x12]), r.getrandbits(32))
                   for _ in range(r.choice([0, 0, 1, 3]))] for _ in range(r.choice([1, 2, 4]))]
        out.append({"args": [0x15], "setup": window_setup(r.choice([0, 0, 1]), r.choice([0, 0, 1])),
                    "fakes": window_fakes(passes, r.choice([1, 2, 3, 9]), r.choice([0, -1, -3, 2, 1]))})
    return out


CASES = [
    {"symbol": MOUSE_MOVE, "ret": "void", "inputs": mouse_inputs()},
    {"symbol": THREAD, "ret": "void", "inputs": thread_inputs()},
    {"symbol": WINDOW_THREAD, "ret": "void", "inputs": window_inputs()},
]
