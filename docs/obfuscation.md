# Obfuscation in the Store build

The Store build (`BlackOps3_MSStore`) has no Arxan: its code is plaintext on disk and nothing checks the image at
run time. But the game's own source carries obfuscation that every build compiled in, and the Store rebuild kept it.
This is what reconstructing and testing code around it needs to know.

## Encrypted pointers

Some global pointers are stored encrypted. The one met so far is the cg array (`cg_arrayEncoded`, 149B25A20: the
cgame's per-local-client globals, 0x342720 bytes each), stored by 1408D8D80 when it is allocated.

- **Decode.** Every use decodes it inline: a `switch` on `(PEB address >> 12) & 0xF` picks one of 16 small state
  machines (rotates, xors, multiply-adds on the two halves), about 6 KB of code per use. That is why functions such
  as `sub_1413ACDF0` (6.4 KB) or `CG_CalcFOVfromLens` (13 KB) are mostly decode. The exe also has many out-of-line
  copies of the same decode (e.g. `sub_141406ED0`, `CG_GetPredictedPlayerState` 140961D00), each a function of its
  own.
- **Key.** The result depends only on the encrypted value and the PEB address bits: the encoder (1408D8D80) uses
  the same key, so a process decodes what it stored.
- **Caller checks.** Each decoder and encoder starts its state machine differently depending on its return address:
  below the exe image, above 0x160000000, and whether the bytes before it look like a call (no `0xFF`/`0xE8` where a
  breakpoint or a hook would be). From the exe's own call sites every start reaches the end state. From outside the
  exe it depends on the PEB variant: measured over all 16, the standalone decoder 141406ED0 called from the recon.dll
  range (0x18...) hangs in 9 of them, and `Dvar_GetBool`, `Dvar_GetFloat` and `Dvar_GetInt` hang in every one; from
  some exe sites a few variants hang too. (An earlier note here, measured with the harness's single PEB variant, said
  calls from a DLL always decode the same; that was wrong.)

**So calls from recon.dll into the exe return through the exe.** Every hybrid-link thunk (tools/build_recon.py
`function_thunk`) calls its original function with an exe address as the return address: a call site followed by
`add rsp, 78h; ret` (target.toml `exe_return`, 14005D3F8, checked against the exe at build time). The thunk builds a
frame of its own (the gadget address, home space, copies of up to 11 stack arguments, and the address of a stub that
drops the frame and returns to the real caller), so arguments, return values and nonvolatile registers pass through
unchanged. With it, `sub_1413ACDF0`'s decode copy and `CL_GetLocalClientGlobals` return in all 16 PEB variants (8 of
16 hang with plain `jmp` thunks): tests/enhanced/test_exe_return.py. The exe is not CET-compatible (no extended
DLL characteristics), so a return address the shadow stack didn't push is not a problem.

A call through a function pointer that isn't a hybrid symbol (an address read from a table) bypasses the thunks;
`T7ExeCall(fn, args...)` (tools/recon/include/t7_exe_call.h, up to five arguments) does the same for those.

Reconstructed code calls an out-of-line decode copy instead of repeating the 16 state machines: the copies are the
same algorithm, and the differential tests check that the reconstruction (copy) and the original (inline) decode the
same encrypted pointers.

## Scrambled dvar values

`Dvar_SetFloat` (1423AA7A0), the `Dvar_Register*` wrappers and `Dvar_ValueToString` (142397330) scramble values of
some dvar types the same way, with the same caller checks.

## Testing

- The harness writes `call rel32` bytes before its sentinel return address (`harness.py`), so decoders called by a
  test return.
- `tests/differential/obfuscation.py` encrypts a pointer with the game's own encoder (1408D8D80 run to its store,
  with its allocation returning the chosen address), so a test can give the code a cgame in memory it controls.
