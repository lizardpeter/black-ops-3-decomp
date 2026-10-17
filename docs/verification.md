# Verification

How a function earns `compiles` and `matches` in `records/functions.tsv`. The method is BO1's
(black-ops-1-decomp `docs/verification.md`); ghosts-decomp ported it to x64, and this repo uses that port. What changes for BO3 is recorded here as it is found.

## compiles

`tools/build_recon.py` builds everything under `src/` with clang `--target=x86_64-pc-windows-msvc`
(Win64 calling convention, MSVC x64 C++ mangling) into `build/recon.dll`, exporting every function under
its decorated name. Tests look functions up by the original decorated name, so a wrong prototype shows
up as a missing export.

That only works where an original decorated name is known, i.e. from a reference build's MAP or PDB.
For functions known only from the stripped retail exe there is no decorated name; they are tested by
address (the match records give the address and the prototype).

## Hybrid link (x64)

Anything the reconstruction uses but does not define resolves to the original binary: functions become
`jmp qword ptr [rip+0]` followed by the 8-byte original address (x64 has no `push imm64`), data becomes an
absolute symbol. The DLL is linked at 0x180000000, clear of the exe at 0x140000000.

## matches (differential)

Same contract as BO1: the original and the reconstruction run in one Unicorn address space on identical
inputs; return value, every pointer buffer and every global write must match exactly; inputs on which the
original faults are skipped; too few usable inputs means untestable, never passed.

The harness (`tests/differential/harness.py`) is ported to x64. What changed from BO1:

- `UC_MODE_64`, a GS-based TEB (`gs:[0x30]` self pointer, `gs:[0x60]` PEB) for code that reads it.
- Win64 calling convention: the first four arguments in rcx, rdx, r8, r9, or xmm0 to xmm3 for floating
  point (by position, not by count of each kind); 32 bytes of shadow space above the return address;
  rsp 16-byte aligned before the call; return in rax or xmm0.
- No x87 state to set up: x64 MSVC does all floating point in SSE. The CPU starts with MXCSR 0x1F80.
  The x87-specific workarounds from BO1 (unrounded ST0 returns, `X87_MATH`) don't apply.
- An Arxan-protected build runs from its **unpacked** image (tools/unpack); the harness checks `unpacked_sha256`.
- The original's CRT math (`sin`, `pow`, ...) is called as ordinary functions; the hybrid link routes the
  reconstruction's calls to the same original routines.

### State, the OS, and calls the test can't see

Most game functions read and write global state and call into the rest of the engine. The harness supports that
without giving up the bit-exact contract:

- **Setup.** An input can carry a `setup(writer)` that writes state into the original's globals (key bindings,
  key catchers, `cmd_args` with an argv in scratch memory, dvar pointers to scratch `dvar_t`s) before each of the
  two calls. Setup writes are undone afterwards like the call's own writes, so inputs never leak into each other.
- **Thread-local storage.** `gs:[0x58]` leads to a copy of the original's TLS template. Reconstructed code reaches
  the same block: `tools/build_recon.py` links the original's `_tls_index` and lays out the DLL's own `.tls` so
  each original TLS variable (`dvar_modifiedFlags`) has its original offset. TLS writes are compared too.
- **Imports.** Every import address table slot of the original points at a stub returning 0 (deterministic
  `timeGetTime`, `EnterCriticalSection` and so on). `Machine.on_import` gives a stub behaviour when a test needs
  one.
- **rdtsc** returns a counter that restarts with every call (`Sys_Milliseconds` seeds `sys_counterBase` from it).
- **Observed calls.** A case can list original functions whose calls are recorded with their arguments and
  compared. That covers callees whose effect is invisible in this build (`CL_ExecBinding` is empty in the
  server); a reconstructed callee is watched at both copies.
- **Fakes.** A case can replace an original function with Python for both runs (`Dvar_GetInt` for dvars that
  were never registered, `Com_ErrorEntering`), so the paths behind them are exercised.
- **Addresses that differ by construction** are normalised before comparing: a pointer the reconstruction stores
  to one of its own functions counts as the original function's address, a pointer into either image's
  `.rdata` counts as the string it points at, and a returned `const char *` is compared as a string (`ret:
  "cstr"`).

Each new case is mutation-checked: a deliberate change in the reconstruction (a constant, a comparison, a
dropped call) must make it fail. A function whose tests survive a mutation gets better inputs, not a pass.

### Testing against a build without symbols

The final target usually has no symbols. `tools/symbols.py` gives it a symbol table from `records/names.tsv` (hand
identifications with method, evidence and confidence) and the matcher's pairs; `tools/build_recon.py --build <id>`
links the reconstruction against it (unidentified symbols link to a trap, imports go through the exe's import
table, an import outranks a matcher pair), and `tests/differential/run.py --build <id>` tests every function that
has an address there. Only functions records/ claims for that build must pass; a failure elsewhere is reported but
doesn't fail the run. CI does this for every `kind = "retail"` build in target.toml.

Other harness rules carried over from Ghosts: every call starts with all registers zeroed; global writes are
compared as net changes (whole qwords, so stored pointers can be normalised); a fake or an observation on a
function applies to its reconstructed copy too; struct padding is left out of compared structs.

## Byte matching

Would need the original compiler on a Windows runner. Retail builds are optimized, so byte matching is not the
goal for them; behavioural equivalence is. The compiler is recorded in target.toml once the inventory confirms it.
