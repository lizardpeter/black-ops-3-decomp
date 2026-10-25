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
  below the exe image, above 0x160000000, and whether the bytes before it look like a `call` (no `0xFF`/`0xE8` where a
  breakpoint or a hook would be). For a real call site (`call rel32` or `call [rip+x]`, from the exe or from a DLL above
  or below it) every start converges on the same result. When the bytes before the return address are not a call (a
  jump into the code, a return address forged by a hook), the encoder and decoders never finish. So reconstructed code
  in a DLL can call the exe's decoders; only a caller that isn't a real call instruction hangs. (Measured in the
  emulator: tests/differential/obfuscation.py and test_cl_input.py.)

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
