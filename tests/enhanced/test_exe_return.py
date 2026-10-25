"""The hybrid link's calls into the exe return through the exe (tools/build_recon.py function_thunk, target.toml
exe_return; docs/obfuscation.md).

The game's decoders hang when their caller lies outside the exe, depending on the PEB address. CL_MouseMove (the
enhanced build's) calls the original CL_GetLocalClientGlobals first, which decodes the encrypted clientActive array
pointer; with no frame time it returns right after. It must return for every one of the 16 PEB variants and every
encrypted value tried (with thunks that jump straight to the original, half the variants hang).
"""
import struct

from harness import TEB

MOUSE_MOVE = "?CL_MouseMove@@YAXHPEAUusercmd_s@@@Z"
PEBS = 0x7FF7_0000_0000


def test_calls_into_the_exe_return_for_every_peb(env):
    mu = env.machine.mu
    if not any(lo <= PEBS <= hi for lo, hi, _ in mu.mem_regions()):
        mu.mem_map(PEBS, 0x10000)
    try:
        for variant in range(16):
            for encrypted in (0x0000_7FF6_1234_5678, 0xCF7E_6011_C906_18CB, 1):
                def setup(w, variant=variant, encrypted=encrypted):
                    w.m.mu.mem_write(TEB + 0x60, struct.pack("<Q", PEBS + (variant << 12)))
                    w.u64(0x149BB45D0, encrypted)  # cl_arrayEncoded
                    w.u32(0x1440A99A4, 2)          # local clients
                    w.u32(0x1440A9874, 0)          # cls_frametime: CL_MouseMove returns after the lookup
                value = env.call(MOUSE_MOVE, [0, bytes(0x48)], "void", setup)[0]
                assert not (isinstance(value, str) and value.startswith("fault")), (variant, hex(encrypted), value)
    finally:
        mu.mem_write(TEB + 0x60, struct.pack("<Q", TEB + 0x2000))
