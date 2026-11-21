"""The DLL reaches the exe wherever Windows loads it (tools/build_recon.py, docs/hybrid-link.md).

The Store exe is ASLR-enabled, so its real base differs from 0x140000000 at run time. Every exe address the DLL uses
sits in one slot table, and the DLL's entry point (t7_hybrid_entry) adds the exe's actual base, read from the PEB,
minus its preferred base to each slot. The emulator always maps the exe at its preferred base, so the other tests
never see a rebase: this one moves the PEB's ImageBaseAddress and checks the entry point itself.
"""
import struct

from harness import TEB

PEB_IMAGE_BASE = TEB + 0x2000 + 0x10
DLL_PROCESS_DETACH, DLL_PROCESS_ATTACH = 0, 1
DELTA = 0x7FF5_0000_0000 - 0x1_4000_0000  # a high-entropy ASLR base, far beyond 2 GB from both images


def _slots(env):
    lo, hi = env.data("t7_exe_slots_start"), env.data("t7_exe_slots_end")
    assert lo < hi and (hi - lo) % 8 == 0, (hex(lo), hex(hi))
    return lo, hi


def _read(mu, lo, hi):
    return list(struct.unpack(f"<{(hi - lo) // 8}Q", bytes(mu.mem_read(lo, hi - lo))))


def _entry(env):
    pe = env.dll.pe
    return env.dll.base + pe.OPTIONAL_HEADER.AddressOfEntryPoint


def _written_qwords(writes, lo, hi):
    """The harness rolls a call's writes back and reports them per byte: the slot table as the call left it."""
    return {a: struct.unpack("<Q", b"".join(writes[a + i] for i in range(8)))[0]
            for a in range(lo, hi, 8) if all(a + i in writes for i in range(8))}


def test_entry_rebases_every_exe_slot(env):
    mu = env.machine.mu
    lo, hi = _slots(env)
    preferred = struct.unpack("<Q", bytes(mu.mem_read(PEB_IMAGE_BASE, 8)))[0]
    before = _read(mu, lo, hi)
    assert all(preferred <= v < preferred + 0x2000_0000 for v in before), [hex(v) for v in before[:8]]
    try:
        mu.mem_write(PEB_IMAGE_BASE, struct.pack("<Q", preferred + DELTA))
        ret, _, writes, _ = env.machine.call(_entry(env), [env.dll.base, DLL_PROCESS_ATTACH, 0], "int")
        assert ret == 1, ret
        after = _written_qwords(writes, lo, hi)
        want = {lo + 8 * i: v + DELTA for i, v in enumerate(before)}
        assert after == want, next((hex(a), hex(after.get(a, 0)), hex(w)) for a, w in want.items() if after.get(a) != w)
        # nothing else is written: trap slots (unidentified exe data, after the table) keep faulting at address 0
        assert {a & ~7 for a in writes} <= set(want), sorted(hex(a) for a in {a & ~7 for a in writes} - set(want))[:8]
        # any other reason changes nothing
        ret, _, writes, _ = env.machine.call(_entry(env), [env.dll.base, DLL_PROCESS_DETACH, 0], "int")
        assert ret == 1 and not writes, (ret, len(writes))
    finally:
        mu.mem_write(PEB_IMAGE_BASE, struct.pack("<Q", preferred))


def test_entry_at_preferred_base_changes_nothing(env):
    ret, _, writes, _ = env.machine.call(_entry(env), [env.dll.base, DLL_PROCESS_ATTACH, 0], "int")
    assert ret == 1 and not writes, (ret, len(writes))
