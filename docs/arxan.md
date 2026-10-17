# Arxan (Steam build)

The Steam `BlackOps3.exe` is Arxan-protected: on disk, both `.text` sections (the game's, 0x2F7B600, and a second
one of 0x4FCD000 holding Arxan's own code) are encrypted, along with parts of `.interpr`, `.rdata`, `.data` and
`_RDATA`. Ghidra analyses the decrypted image, never the raw file.

`tools/unpack/arxan.py` (from ghosts-decomp) emulates the stub in Unicorn and writes the decrypted image. The image
is generated, not stored: its sha256 is pinned in target.toml (`unpacked_sha256`).

## What differs from Ghosts

- **The stub reads KUSER_SHARED_DATA** (0x7FFE0008, InterruptTime). Ghosts' stub didn't, so the unpacker now maps
  that page with a frozen clock (InterruptTime, SystemTime and TickCount never advance), which keeps the run
  deterministic.
- **The entry point is already the CRT entry.** Ghosts' PE entry pointed at a stub, and the unpacker found the
  original entry by pattern. In BO3 the entry (142C4D06C) is the VS2012 `mainCRTStartup`, with its tail patched:
  `sub rsp,28h; call 14133B835; nop; jmp 15D16978D` instead of `... add rsp,28h; jmp __tmainCRTStartup`. Arxan
  runs from those patched call and jump, so the entry point is left as it is.
- The run stops at the first ordinary runtime call, `GetSystemTimeAsFileTime` from 142C6541A
  (`__security_init_cookie`), as on Ghosts.

## Result

| section | changed bytes | entropy before | after |
|---|---:|---:|---:|
| .text (game) | 49,532,374 | 8.00 | 6.74 |
| .interpr | 38,790 | 7.99 | 6.42 |
| .rdata | 3,015,808 | 7.74 | 5.73 |
| .data | 3,328,005 | 5.19 | 1.22 |
| _RDATA | 12,969 | 7.93 | 6.71 |
| .text (Arxan) | 78,795,172 | 7.96 | 6.76 |

No 1/32 slice of the game `.text` is still high-entropy afterwards. The decrypted code still contains Arxan's
inserted calls and jumps (guards and the patched entry); they are not game code and are in neither build.
