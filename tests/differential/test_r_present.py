"""Hand-written cases for gfx_d3d/r_present.cpp (sub_141D46720, presenting a frame).

The function reads the dx globals and three dvars and calls out for everything else, so each case sets the globals
(NvAPI up or not, 1-4 GPUs, the last SLI frame index, the loading-screen nesting, the vendor, a 3D Vision handle or
none) and fakes and records every callee with its arguments:
- Dvar_GetBool / Dvar_GetFloat by dvar (r_vsync, r_refreshRate including rates that make the AMD pace 0 or negative,
  r_convergence);
- the critical section the SLI query is made under (Sys_Enter/LeaveCriticalSection; the original constructs the
  scoped lock inline, the reconstruction calls the out-of-line constructor, which must come to the same thing; the
  thread's TLS guard byte is set, so no on-demand initialization runs, and the lock chain at TLS+0x20 must be left
  as it was);
- NvAPI_D3D_GetCurrentSLIState (status and frame index), Sleep, SendMessageA (the present's HRESULT: success, removed,
  reset, other failures), the device's GetDeviceRemovedReason through a COM model (every reason the code maps),
  Com_Error_ (file, line, code, format and reason compared as strings), NvAPI_Stereo_IsActivated (status and answer)
  and NvAPI_Stereo_SetConvergence (the float it gets).

Mutation check: see the commit adding this file.
"""
import random
import struct

import syms
from com import ComModel
from harness import _MACHINES, TLS_BLOCK
from unicorn.x86_const import (UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP,
                               UC_X86_REG_XMM1)

SYM = "?sub_141D46720@@YAXXZ"
DEV = "ID3D11Device"
GET_REMOVED_REASON = 39 * 8
DVARS = {"r_vsync": 0x6200_0000_0010, "r_refreshRate": 0x6200_0000_0020, "r_convergence": 0x6200_0000_0030}
HWND = 0x0001_0042
STEREO = 0x0000_5700_0000_1000
HRESULTS = [0, 1, 0x887A0005, 0x887A0007, 0x887A0001, 0x80004005, 0x887A0006]
REASONS = [0x887A0001, 0x887A0005, 0x887A0006, 0x887A0007, 0x887A0020, 0x80004005, 0]


def regs(mu):
    return [mu.reg_read(r) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]


def stack(mu, i):
    return struct.unpack("<Q", bytes(mu.mem_read(mu.reg_read(UC_X86_REG_RSP) + 8 + 8 * i, 8)))[0]


def record(mu, *values):
    _MACHINES[id(mu)].observed.append(values)


def f32(x):
    return struct.unpack("<I", struct.pack("<f", x))[0]


def fakes(c):
    def dvar(kind):
        def fn(mu):
            p = regs(mu)[0]
            name = next(n for n, v in DVARS.items() if v == p)
            record(mu, kind, name)
            if kind == "Dvar_GetBool":
                return c["vsync"]
            # a float comes back in XMM0
            from unicorn.x86_const import UC_X86_REG_XMM0
            mu.reg_write(UC_X86_REG_XMM0, f32(c["rate"] if name == "r_refreshRate" else c["convergence"]))
            return None
        return fn

    def sli(mu):
        device, state = regs(mu)[:2]
        record(mu, "NvAPI_D3D_GetCurrentSLIState", device, bytes(mu.mem_read(state, 4)))
        mu.mem_write(state + 4, struct.pack("<IIIIII", 4, c["gpus"], c["afr"], 0, 0, 0))
        return c["sli_status"]

    def com_error(mu):
        m = _MACHINES[id(mu)]
        a = regs(mu)
        record(mu, "Com_Error_", m.read_cstr(a[0]), a[1] & 0xFFFFFFFF, a[2] & 0xFFFFFFFF, m.read_cstr(a[3]),
               m.read_cstr(stack(mu, 4)), stack(mu, 5) & 0xFFFFFFFF)

    def is_activated(mu):
        handle, out = regs(mu)[:2]
        record(mu, "NvAPI_Stereo_IsActivated", handle)
        mu.mem_write(out, bytes([c["stereo_on"]]))
        return c["stereo_status"]

    return {
        "Dvar_GetBool": dvar("Dvar_GetBool"),
        "Dvar_GetFloat": dvar("Dvar_GetFloat"),
        "Sys_EnterCriticalSection": lambda mu: record(mu, "enter", regs(mu)[0] & 0xFFFFFFFF),
        "Sys_LeaveCriticalSection": lambda mu: record(mu, "leave", regs(mu)[0] & 0xFFFFFFFF),
        "__dyn_tls_on_demand_init": lambda mu: record(mu, "tls init"),
        "NvAPI_D3D_GetCurrentSLIState": sli,
        "KERNEL32.dll!Sleep": lambda mu: record(mu, "Sleep", regs(mu)[0] & 0xFFFFFFFF),
        "USER32.dll!SendMessageA": lambda mu: (record(mu, "SendMessageA", *regs(mu)), c["hr"])[1],
        "Com_Error_": com_error,
        "NvAPI_Stereo_IsActivated": is_activated,
        "NvAPI_Stereo_SetConvergence": lambda mu: record(mu, "SetConvergence", regs(mu)[0],
                                                         mu.reg_read(UC_X86_REG_XMM1) & 0xFFFFFFFF),
    }


def setup(c):
    def apply(w):
        model = ComModel({(DEV, GET_REMOVED_REASON): ""}, {(DEV, GET_REMOVED_REASON): lambda call: c["reason"]})
        model.install(w.m)
        w.u64(syms.va("dx_device"), model.new(DEV))
        for name, p in DVARS.items():
            w.u64(syms.va(name), p)
        w.write(syms.va("dx_nvapiInitialized"), bytes([c["nvapi"]]))
        w.u32(syms.va("dx_gpuCount"), c["gpus"])
        w.u32(syms.va("s_lastAfrIndex"), c["last_afr"])
        w.write(syms.va("dx_afrIndexRepeated"), bytes([c["repeated"]]))
        w.u32(syms.va("dx_remoteScreenUpdateNesting"), c["nesting"])
        w.u32(syms.va("dx_vendor"), c["vendor"])
        w.u64(syms.va("g_hWnd"), HWND)
        w.u64(syms.va("dx_stereoHandle"), STEREO if c["stereo"] else 0)
        w.write(syms.va("dx_stereoActivated"), bytes([c["was_active"]]))
        w.write(TLS_BLOCK + 0x10, b"\x01")  # the thread's thread_locals are initialized
        w.u64(TLS_BLOCK + 0x20, 0x5C0BE000)  # some lock already held by the thread
    return apply


def inputs():
    r = random.Random(46720)
    out = []
    for _ in range(300):
        hr = r.choice(HRESULTS)
        c = {
            "nvapi": r.choice([0, 1, 1]), "gpus": r.choice([1, 2, 4, 0]), "afr": r.randrange(4), "last_afr": r.randrange(4),
            "repeated": r.choice([0, 0, 1]), "sli_status": r.choice([0, 0, -1, -6]),
            "vsync": r.choice([0, 1]), "nesting": r.choice([0, 0, 1, 3]), "vendor": r.choice([1, 2, 2, 3, 0]),
            "rate": r.choice([60.0, 144.0, 240.0, 499.999, 1.0, 333.4, 2000.0, 0.5, -5.0]),
            "hr": hr | (r.choice([0, 0xFFFFFFFF_00000000]) if hr else 0), "reason": r.choice(REASONS),
            "stereo": r.choice([0, 1]), "stereo_status": r.choice([0, 0, -1]), "stereo_on": r.choice([0, 1, 2]),
            "was_active": r.choice([0, 1]), "convergence": r.choice([6.0, 0.1, 42.5]),
        }
        out.append({"args": [], "setup": setup(c), "fakes": fakes(c), "case": c})
    return out


CASES = [{"symbol": SYM, "ret": "void", "inputs": inputs()}]
