"""Hand-written cases for universal/dvar.cpp (Dvar_Init).

Dvar_Init sets two globals, registers seven dvars and calls Dvar_AddCommands. The registration functions are faked as
in test_r_dvars.py (every argument recorded, strings compared as strings, a pointer from the hash and the input's salt
returned, so each stored global is checked); Dvar_GenerateHash runs for real; Dvar_AddCommands is faked and recorded,
so its place after the registrations is checked. The salts only vary the returned pointers; the function reads no input.
The two globals it sets start from other values (the image holds 0 in both), so both stores show.

Mutation check: see the commit adding this file.
"""
from harness import _MACHINES

import syms
import test_r_dvars as regs

SYM = "?Dvar_Init@@YAXXZ"


def add_commands(mu):
    _MACHINES[id(mu)].observed.append(("Dvar_AddCommands",))


def setup(byte, dword):
    def apply(w):
        w.write(syms.va("byte_158835226"), bytes([byte]))
        w.u32(syms.va("dword_1599E7624"), dword)
    return apply


def inputs():
    return [{"args": [], "setup": setup(salt & 1, salt * 0x1001),
             "fakes": {**{name: regs.fake(name, salt) for name in regs.SPECS}, "Dvar_AddCommands": add_commands}}
            for salt in (0x11, 0x22, 0x33, 0xA5)]


CASES = [{"symbol": SYM, "ret": "void", "inputs": inputs()}]
