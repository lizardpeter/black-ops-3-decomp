# How the reconstruction reaches the original exe

`tools/build_recon.py` links the reconstruction into one DLL that runs inside the original process. Anything it uses
but doesn't define yet (an original function, global, static or import) is the original exe's. This page covers how
the DLL reaches those addresses, which has to work wherever Windows loads both images.

## Why addresses can't be baked in

- **The Store exe is ASLR-enabled.** `BlackOps3_MSStore.exe` is marked dynamic-base, high-entropy, and carries a
  relocation table. At run time Windows loads it at a random base, not 0x140000000. (Ghosts' Store exe isn't
  ASLR-enabled, so ghosts-decomp can use fixed addresses.) Wine usually honours the preferred base, so Wine runs
  don't show this.
- **The enhanced DLL is ASLR-relocatable too** (`/dynamicbase`), because it must not assume a free base inside the
  game's process (tools/enhanced/build.py).
- **COFF can't express a 64-bit absolute symbol.** A symbol's value field is 32 bits, so `.set sym, 0x1440A9874`
  stores `0x440A9874`. Code reaching such a symbol RIP-relatively only lands on the right address by modular
  arithmetic, and only when the DLL is within 2 GB of the exe. The faithful DLL at a fixed 0x180000000 happened to
  satisfy that. The enhanced DLL at 0x400000000 didn't: every exe global it touched was 0x300000000 off, which is
  why most of `tests/enhanced` failed.

## The slot table

Every exe address the DLL uses lives in one table of 8-byte slots in the DLL's `.data`, between
`t7_exe_slots_start` and `t7_exe_slots_end`. Each slot holds the address assuming the exe's preferred base.

| User | How it reaches the exe |
|---|---|
| Original function | thunk: `jmp [rip+slot]` |
| Original function, through the exe-return gadget (docs/obfuscation.md) | `mov r10, [rip+gadget_slot]` and `mov r10, [rip+slot]`; `jmp r10` |
| Import (Win32, CRT) | `mov rax, [rip+slot]` (the exe's IAT entry); `jmp [rax]` |
| Global or static (`t7x@<symbol>`) | the unit's `movabsq $sym, %reg` becomes `movq "t7x@sym"(%rip), %reg` |
| Unidentified data (trap) | a slot holding 0, after `t7_exe_slots_end`: never rebased, so it still faults at address 0 |

Code reaches a slot RIP-relatively, which always works because the slot is inside the same DLL.

### Rebasing at load

The DLL's entry point `t7_hybrid_entry` runs on `DLL_PROCESS_ATTACH`. It reads the exe's actual base from the PEB
(`gs:[0x60]` → `ImageBaseAddress`), subtracts the preferred base, and adds the difference to every slot in the table.
It does nothing at the preferred base or for any other reason, and returns TRUE. `tests/enhanced/test_hybrid_rebase.py`
calls it with the PEB reporting a high-entropy base and checks that every slot moves by exactly that much and nothing
else is written. The emulator always maps the exe at its preferred base, so this is the only test that exercises a
rebase.

### Exe data in compiled code

Units are compiled with `-mcmodel=large`, so clang reaches every global as `movabsq $sym, %reg`: one form, with a
full 64-bit address. After symbol resolution, `exe_relative_asm` rewrites that form, for each symbol of the exe, into
a load from the symbol's slot (`leaq off(%reg), %reg` follows for `sym+off`, leaving flags alone). The symbols
themselves are never defined, so a reference the rewrite missed fails the link. Any other instruction form that
mentions an exe symbol stops the build. Across src/ and enhanced/ there were 518 such references, all of that form.

`-fno-jump-tables` comes with the large model. A large-model jump table stores 64-bit `case - table` differences
across sections, which COFF keeps as 32 bits, so a negative one comes back 4 GB off. `compile_unit` rejects any
label-difference table that slips through.

### Checks

- After linking, `check_no_exe_addresses` disassembles the DLL's `.text` and fails if any instruction holds an
  address inside the exe's image, as an immediate or as a RIP-relative target. Only the slot table holds exe
  addresses.
- `tests/differential/run.py` maps a thunk back to its original function by reading the slot it jumps through, so it
  follows a rebase.

## Undefined behaviour in faithful source

The large model changes code generation, so faithful source that relied on undefined behaviour can compile
differently. `bdPlatformSocket::sendTo` added `sent + 28` as `int` and then widened it. The original wraps in 32 bits
(`lea eax, [rdi+1Ch]; movsxd rcx, eax` at 1429C4C87), but signed overflow is undefined in C++. Under the large model
clang did the add in 64 bits, and `m_totalBytesSent` came out different past INT_MAX. The source now does the add
unsigned, which is well-defined and gives the original's result. Write such wraps explicitly: don't rely on the
compiler to reproduce MSVC's.
