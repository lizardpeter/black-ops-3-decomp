"""A model of COM objects (Direct3D 11 / DXGI) for differential tests of renderer code.

A test creates fake objects in its input setup. Each object is a vtable pointer followed by an id; every vtable
slot points at its own stub, so a call through `obj->lpVtbl[n]` lands in Python. Every call is logged into the
machine's observed calls as ("com", kind, slot offset, object id, argument values...), so the original and the
reconstruction must make the same calls, on the same objects, with the same arguments, in the same order.

Arguments are logged by a signature per method (`sigs`): one letter per argument after `this`, as in the
harness's `observe` (b 8-bit, i 32-bit, q 64-bit, f float), plus p for a pointer: one of the model's objects is
logged as ("obj", id), anything else as its value, or by content when the method has a dump size for it
(`dumps`), so descriptions passed by pointer are compared by content, not address. A call to a method without a
signature fails the test, so every method a function uses is described. Behaviour per method (`results`): a function fn(call) returning the value for RAX; it can write out
parameters, for example a newly created object (call.out_object). Without one, a method returns 0 (S_OK).

Slots are named by their byte offset in the vtable; tests give the offsets of the methods they use names.
"""
import struct
from dataclasses import dataclass, field

from unicorn import UC_HOOK_CODE, UcError
from unicorn.x86_const import (UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_RDX,
                               UC_X86_REG_RIP, UC_X86_REG_RSP, UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3)

REGION, REGION_SIZE = 0x00800000, 0x00200000
STUBS = REGION                      # 16 bytes per (kind, slot): kinds * SLOTS * 16
SLOTS = 128                         # enough for every interface the game uses (ID3D11DeviceContext has 115)
VTABLES = REGION + 0x80000          # SLOTS * 8 per kind
OBJECTS = REGION + 0xA0000          # 0x40 bytes per object
MEMORY = REGION + 0x100000          # buffers handed out by methods (Map's pData, ...)
OBJ_SIZE = 0x40
KINDS = ("ID3D11Device", "ID3D11DeviceContext", "IDXGIFactory", "IDXGIAdapter", "IDXGIOutput", "IDXGISwapChain",
         "ID3D11Resource", "ID3D11View", "ID3D11State", "ID3D11Shader", "ID3D11InputLayout", "ID3D11Query",
         "ID3D11CommandList", "IUnknown")


@dataclass
class Call:
    model: "ComModel"
    mu: object
    kind: str
    offset: int
    obj: int
    args: list = field(default_factory=list)  # integer argument values (registers, then stack)

    def arg(self, i):
        return self.args[i]

    def out_object(self, i, kind):
        """Create an object of `kind` and store its pointer through pointer argument i."""
        va = self.model.new(kind, self.mu)
        if self.args[i]:
            self.mu.mem_write(self.args[i], struct.pack("<Q", va))
        return va

    def write(self, va, data):
        self.mu.mem_write(va, data)


class ComModel:
    def __init__(self, sigs, results=None, dumps=None):
        self.sigs = dict(sigs)                     # (kind, offset) -> argument letters after `this`
        self.results = dict(results or {})         # (kind, offset) -> fn(Call) -> RAX value or None
        self.dumps = dict(dumps or {})             # (kind, offset) -> {arg index: byte count}
        self.objects = {}                          # va -> (kind, id)
        self.next_obj = OBJECTS
        self.next_mem = MEMORY
        self.machine = None

    # ---- set-up -------------------------------------------------------------------------------------------
    def install(self, m):
        """Map the region (once per machine) and make this model the one calls go to."""
        if not getattr(m, "_com_ready", False):
            try:
                m.mu.mem_map(REGION, REGION_SIZE)
            except UcError:
                pass
            for k in range(len(KINDS)):
                for s in range(SLOTS):
                    m.mu.mem_write(STUBS + (k * SLOTS + s) * 16, b"\x31\xc0\xc3")  # xor eax, eax; ret
                    m.mu.mem_write(VTABLES + (k * SLOTS + s) * 8, struct.pack("<Q", STUBS + (k * SLOTS + s) * 16))
            m.mu.hook_add(UC_HOOK_CODE, _on_stub, user_data=m, begin=STUBS, end=VTABLES - 1)
            m._com_ready = True
        m.mu.mem_write(OBJECTS, bytes(MEMORY - OBJECTS))
        m._com = self
        self.machine = m

    def new(self, kind, mu=None):
        """A new object of `kind`; ids count up from 1 in creation order."""
        mu = mu or self.machine.mu
        va = self.next_obj
        self.next_obj += OBJ_SIZE
        oid = len(self.objects) + 1
        self.objects[va] = (kind, oid)
        mu.mem_write(va, struct.pack("<QI", VTABLES + KINDS.index(kind) * SLOTS * 8, oid))
        return va

    def alloc(self, data: bytes, mu=None):
        mu = mu or self.machine.mu
        va = self.next_mem
        self.next_mem += (len(data) + 0xF) & ~0xF
        mu.mem_write(va, data)
        return va


def _on_stub(mu, address, size, m):
    model = getattr(m, "_com", None)
    if model is None or address & 0xF:
        return
    index = (address - STUBS) // 16
    kind, offset = KINDS[index // SLOTS], (index % SLOTS) * 8
    rcx = mu.reg_read(UC_X86_REG_RCX)
    obj = model.objects.get(rcx, (None, f"<not an object {rcx:#x}>"))[1]
    rsp = mu.reg_read(UC_X86_REG_RSP)
    sig = model.sigs.get((kind, offset))
    if sig is None:
        m.observed.append(("com", kind, offset, obj, "<no signature: add one to the test>"))
        sig = ""
    args, logged = [], []
    regs = (UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)
    xmms = (UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3)
    for i, letter in enumerate(sig):
        if i < 3:
            raw = mu.reg_read(xmms[i] if letter == "f" else regs[i])
        else:
            raw = struct.unpack("<Q", bytes(mu.mem_read(rsp + 0x28 + 8 * (i - 3), 8)))[0]
        value = raw & {"b": 0xFF, "i": 0xFFFFFFFF, "f": 0xFFFFFFFF}.get(letter, 0xFFFFFFFFFFFFFFFF)
        args.append(value)
        if letter == "p":
            n = model.dumps.get((kind, offset), {}).get(i)
            if value in model.objects:
                logged.append(("obj", model.objects[value][1]))
            elif n and value:
                try:
                    logged.append(("bytes", bytes(mu.mem_read(value, n))))
                except UcError:
                    logged.append(("unreadable", value))
            else:
                logged.append(("ptr",) if value else 0)  # stack and heap addresses differ between the two builds
        else:
            logged.append(value)
    m.observed.append(("com", kind, offset, obj, *logged))
    call = Call(model, mu, kind, offset, rcx, args)
    fn = model.results.get((kind, offset))
    value = fn(call) if fn else 0
    # return to the caller here, so the stub's own `xor eax, eax` doesn't overwrite the result
    mu.reg_write(UC_X86_REG_RAX, (value or 0) & 0xFFFFFFFFFFFFFFFF)
    mu.reg_write(UC_X86_REG_RIP, struct.unpack("<Q", bytes(mu.mem_read(rsp, 8)))[0])
    mu.reg_write(UC_X86_REG_RSP, rsp + 8)
