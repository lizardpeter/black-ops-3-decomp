"""A small model of the Win32 calls the input code makes, for differential tests.

Each test input builds a Win32 state (foreground window, cursor position, window rectangle, client-area origin,
cursor display count) and installs it on the machine from its setup. Imports then behave like the real ones on
that state, and every call is logged with its arguments into the machine's observed calls, so the original and
the reconstruction must make the same calls in the same order with the same arguments, not just leave the same
globals behind.
"""
import struct
from dataclasses import dataclass

from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_RDX

HWND_GAME = 0x10010


@dataclass
class Win32:
    foreground: int = HWND_GAME
    cursor: tuple = (400, 300)
    window: tuple = (100, 50, 900, 650)  # left, top, right, bottom (screen)
    client_origin: tuple = (108, 80)      # screen position of the client area's top-left
    client_size: tuple = (784, 562)
    show_count: int = 0                   # ShowCursor display count

    def install(self, m):
        s = self

        def u32(v):
            return v & 0xFFFFFFFF

        def signed(v):
            v &= 0xFFFFFFFF
            return v - (1 << 32) if v & 0x80000000 else v

        def log(name, *args):
            m.observed.append(("import", name, *args))

        def ret(mu, v):
            mu.reg_write(UC_X86_REG_RAX, v & 0xFFFFFFFFFFFFFFFF)

        def get_foreground(mu):
            log("GetForegroundWindow")
            ret(mu, s.foreground)

        def get_cursor_pos(mu):
            log("GetCursorPos")
            mu.mem_write(mu.reg_read(UC_X86_REG_RCX), struct.pack("<ii", *s.cursor))
            ret(mu, 1)

        def set_cursor_pos(mu):
            x, y = signed(mu.reg_read(UC_X86_REG_RCX)), signed(mu.reg_read(UC_X86_REG_RDX))
            log("SetCursorPos", x, y)
            s.cursor = (x, y)
            ret(mu, 1)

        def clip_cursor(mu):
            p = mu.reg_read(UC_X86_REG_RCX)
            log("ClipCursor", struct.unpack("<4i", bytes(mu.mem_read(p, 16))) if p else None)
            ret(mu, 1)

        def show_cursor(mu):
            show = u32(mu.reg_read(UC_X86_REG_RCX))
            s.show_count += 1 if show else -1
            log("ShowCursor", show)
            ret(mu, u32(s.show_count))

        def get_window_rect(mu):
            hwnd = mu.reg_read(UC_X86_REG_RCX)
            log("GetWindowRect", hwnd)
            mu.mem_write(mu.reg_read(UC_X86_REG_RDX), struct.pack("<4i", *s.window))
            ret(mu, 1)

        def get_client_rect(mu):
            hwnd = mu.reg_read(UC_X86_REG_RCX)
            log("GetClientRect", hwnd)
            mu.mem_write(mu.reg_read(UC_X86_REG_RDX), struct.pack("<4i", 0, 0, *s.client_size))
            ret(mu, 1)

        def to_client(sign):
            def run(mu):
                hwnd, p = mu.reg_read(UC_X86_REG_RCX), mu.reg_read(UC_X86_REG_RDX)
                x, y = struct.unpack("<ii", bytes(mu.mem_read(p, 8)))
                log("ScreenToClient" if sign < 0 else "ClientToScreen", hwnd, x, y)
                nx, ny = (signed(v + sign * o) for v, o in zip((x, y), s.client_origin))
                mu.mem_write(p, struct.pack("<ii", nx, ny))
                ret(mu, 1)
            return run

        def post_message(mu):
            log("PostMessageA", mu.reg_read(UC_X86_REG_RCX), u32(mu.reg_read(UC_X86_REG_RDX)),
                mu.reg_read(UC_X86_REG_R8), mu.reg_read(UC_X86_REG_R9))
            ret(mu, 1)

        for name, fn in {"GetForegroundWindow": get_foreground, "GetCursorPos": get_cursor_pos,
                         "SetCursorPos": set_cursor_pos, "ClipCursor": clip_cursor, "ShowCursor": show_cursor,
                         "GetWindowRect": get_window_rect, "GetClientRect": get_client_rect,
                         "ScreenToClient": to_client(-1), "ClientToScreen": to_client(1),
                         "PostMessageA": post_message}.items():
            m.on_import("user32.dll!" + name, fn)
