"""The game's encrypted pointers, for test setups (docs/obfuscation.md).

The cg array pointer (cg_arrayEncoded, 149B25A20) is stored encrypted with a PEB-keyed transform and decoded inline
wherever it is used. A test that needs a cgame sets the pointer to the encryption of a buffer it controls; the
encryption is the game's own: CG_AllocateClientMemory (1408D8D80), which allocates the array and encrypts it, is run up to its store with its
allocation returning the chosen address. The key comes from the PEB, so results hold for the harness's PEB only.
"""
import struct

from harness import STACK, STACK_SIZE
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

ALLOC_CG = 0x1408D8D80        # allocates the cg array and stores it encrypted
STORE_AT = 0x1408DA639        # mov [cg_arrayEncoded], rax
ALLOCATORS = 0x14310FE88      # allocator function table, entry 0
CALL_SITE = 0x14140C829 + 5   # a real call of ALLOC_CG: its caller-byte checks need a genuine return site
CG_SIZE = 0x342720
STUBS = 0x0F00_0000           # a stub per encryption: the emulator caches translated code, so stubs aren't rewritten
_cache = {}


def encrypt_cg_array(machine, pointer: int) -> int:
    """The value cg_arrayEncoded holds when the cg array is at `pointer`."""
    if pointer in _cache:
        return _cache[pointer]
    mu = machine.mu
    if not any(lo <= STUBS < hi for lo, hi, _ in mu.mem_regions()):
        mu.mem_map(STUBS, 0x100000)
    stub = STUBS + 0x20 * len(_cache)
    mu.mem_write(stub, b"\x48\xb8" + struct.pack("<Q", pointer) + b"\xc3")  # mov rax, pointer; ret
    saved = bytes(mu.mem_read(ALLOCATORS, 8))
    mu.mem_write(ALLOCATORS, struct.pack("<Q", stub))
    kind = STUBS + 0xFF000                                                      # *param_1: allocator 0
    mu.mem_write(kind, struct.pack("<i", 0))
    got = {}

    def at_store(uc, address, size, user):
        got["value"] = uc.reg_read(UC_X86_REG_RAX)
        uc.emu_stop()

    hook = mu.hook_add(UC_HOOK_CODE, at_store, begin=STORE_AT, end=STORE_AT)
    sp = STACK + STACK_SIZE - 0x800
    mu.mem_write(sp, struct.pack("<Q", CALL_SITE))
    mu.reg_write(UC_X86_REG_RSP, sp)
    mu.reg_write(UC_X86_REG_RCX, kind)
    mu.reg_write(UC_X86_REG_RDX, 0)
    try:
        mu.emu_start(ALLOC_CG, CALL_SITE, count=1_000_000)
    finally:
        mu.hook_del(hook)
        mu.mem_write(ALLOCATORS, saved)
    _cache[pointer] = got["value"]
    return got["value"]


def map_region(machine, base: int, size: int):
    """Maps [base, base + size) once (a cgame for tests); the region isn't compared, setups fill it each call."""
    mu = machine.mu
    if not any(lo <= base <= hi for lo, hi, _ in mu.mem_regions()):
        mu.mem_map(base, size)
