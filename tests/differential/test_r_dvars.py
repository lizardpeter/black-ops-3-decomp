"""Hand-written cases for gfx_d3d/r_dvars.cpp (renderer dvar registration).

sub_141D976E0 is a straight run of Dvar_Register* calls whose results go to globals. Each register function is faked
(the dvar system is not set up in the emulator) and records its type and every argument: hash, name and description
(compared as strings), value, domain, flags, the trailing bool, and for enums the value list's strings. A fake returns
a pointer derived from the hash and the input's salt, so every global the function stores is compared with the
pointer that registration returned. The salts only vary those pointers; the function reads no input.

Mutation check: see the commit adding this file.
"""
import struct

from harness import _MACHINES
from unicorn.x86_const import (UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP,
                               UC_X86_REG_XMM2, UC_X86_REG_XMM3)

SYM = "?sub_141D976E0@@YAXXZ"
INT = (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)
XMM = (None, None, UC_X86_REG_XMM2, UC_X86_REG_XMM3)
# argument kinds by position: i = 32-bit int, s = C string, b = bool, f = float, l = enum value list
SPECS = {
    "Dvar_RegisterBool": "isbisb",
    "Dvar_RegisterFloat": "isfffisb",
    "Dvar_RegisterInt": "isiiiisb",
    "Dvar_RegisterString": "issisb",
    "Dvar_RegisterVec3": "isfffffisb",
    "Dvar_RegisterEnum": "isliisb",
}


def args(mu, spec):
    m = _MACHINES[id(mu)]
    rsp = mu.reg_read(UC_X86_REG_RSP)
    out = []
    for i, kind in enumerate(spec):
        if i < 4:
            raw = mu.reg_read(XMM[i] if kind == "f" else INT[i])
        else:
            raw = struct.unpack("<Q", bytes(mu.mem_read(rsp + 8 + 8 * i, 8)))[0]
        if kind == "f":
            out.append(raw & 0xFFFFFFFF)
        elif kind == "s":
            out.append(m.read_cstr(raw))
        elif kind == "b":
            out.append(raw & 0xFF)
        elif kind == "l":
            names = []
            while True:
                p = struct.unpack("<Q", bytes(mu.mem_read(raw + 8 * len(names), 8)))[0]
                if not p:
                    break
                names.append(m.read_cstr(p))
            out.append(tuple(names))
        else:
            out.append(raw & 0xFFFFFFFF)
    return out


def fake(name, salt):
    def fn(mu):
        got = args(mu, SPECS[name])
        _MACHINES[id(mu)].observed.append((name, *got))
        return 0x7F00_0000_0000 | salt << 32 | got[0]
    return fn


def inputs():
    return [{"args": [], "fakes": {name: fake(name, salt) for name in SPECS}} for salt in (0x11, 0x22, 0x33, 0xA5)]


CASES = [{"symbol": SYM, "ret": "void", "inputs": inputs()}]
