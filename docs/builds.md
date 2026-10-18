# Builds

Inventory of every BO3 build available, with provenance. target.toml holds the machine-readable part (R2 key,
sha256, kind); this page holds the reasoning: where each file came from, its signature, timestamps,
debug-directory PDB path and GUID, Rich header (compiler), protection, and why it was chosen as reference, target
or helper. More files are still being uploaded to R2; each is added here when it arrives.

## BlackOps3_MSStore (retail): Microsoft Store build

R2 `bo3/DUMP/`, a dump of the installed Store package.

| | |
|---|---|
| Package | `38985CA0.CallofDutyBlackOps3PCMS` 0.2.4.0, Store id 9P2Z4LP10ZMC, title id 74D934C1 (MicrosoftGame.config) |
| Exe | `BlackOps3.exe`, 57,512,424 bytes, sha256 `72c8a217…0f827c17` (target.toml) |
| Link time | 2024-11-14 18:19:22 UTC |
| PDB record | `d:\workspace\outrun\t7\game\pc\BlackOps3.pdb`, GUID BFD3A67B-5182-473D-B955-12F61FDB5F43, age 5 (PDB not available) |
| Compiler | VS2019 16.11: Rich header dominated by cl 19.29.30154, linker 14.29; POGO debug record, so LTCG |
| Library paths | `C:\trees\outrun\outrun\t7\code\libs\...` (DemonWareGDK and others) |
| Signature | Authenticode certificate present (10,728 bytes); not yet verified |
| Protection | none found: `.text` has entropy 6.7 (plain code), the entry point (142CFE874) is in `.text`, no Arxan strings. A small `.interpr` section (0x83B8) exists, as in the Ghosts exes; what it holds is to be checked |
| Platform | GDK: GameChat2, PartyXboxLive, PlayFabMultiplayerGDK, XCurl beside the exe; `libScePad.dll` for DualShock/DualSense input; D3D11 |

Sections: `.text` 0x2DA0F93, `.interpr` 0x83B8, `.rdata` 0x33D456, `.data` 0x1731E9B0 virtual (0x4BA200 on disk),
`.pdata` 0xACC20, `.xbld` 0x1C5, `.rsrc`, `.reloc`.

Same port as Ghosts' Store build (`d:\workspace\outrun\iw6-depot`, also VS2019 16.11, built four days later), so
ghosts-decomp's docs/store-build.md and docs/gdk.md are the closest prior work for the platform layer.

The MicrosoftGame.config comment says it was generated for `DedicatedDebug|x64`; that reads as a template
leftover, since the exe is an optimized LTCG build.

Not committed or analysed: the zone/ fastfiles, sound banks and video (game data, not code), and the GDK DLLs
beside the exe.

### Ghidra analysis

First pipeline run (Ghidra 12.1.4): analysis 34 min, decompile 6 shards of 5 to 11 min.

- 37,154 functions (37,151 in `.text`, 3 in `.interpr`), covering 46.3 MB of the 47.8 MB `.text`.
- Decompiled: 36,925 ok, 225 thunks, 4 failed (141D253D0, 1422649C0, 1422D6110, 1423C0110; all 36 KB or larger,
  1422649C0 is 208 KB).
- Checked against `.pdata` (58,968 entries): 26,968 entries that are not Ghidra functions are chained unwind
  records, i.e. fragments of a parent function split out by LTCG/POGO, which Ghidra correctly folds into the
  parent. Only 3 plain entries are missed (142AE41D0, 142D96E80, 142D98CA0).
- 238 functions have names from Ghidra (imports, CRT signatures); everything else is `FUN_` until matched.
- Largest functions: 1414168F0 (363 KB), 141F45730 (221 KB), 1422649C0 (208 KB).

Second run, with tools/ghidra/CreateTableFunctions.java: 5,064 pointers in `.rdata`/`.data` led into code where no
function existed (11 more pointed inside a function and were left alone); 5,063 became functions, 1 was not code.
Now **42,221 functions**, 41,928 decompiled, 289 thunks, the same 4 failures. These are functions reached only
through tables: vtables, Lua and command registration, callbacks.

## BlackOps3_Steam (related): final Steam build

R2 `bo3/t7_tor_exe/BlackOps3.exe`, from a torrent copy of the Steam release.

| | |
|---|---|
| Exe | 143,134,192 bytes, sha256 `66b95eb4…be24ff44` (target.toml) |
| Link time | 2023-02-25 01:02:52 UTC |
| PDB record | `Q:\t7\pc\game\pc\cod_Ship.pdb`, GUID 97E5A5DF-999E-4983-B5DD-03ECE1D43B07, age 215 (PDB not available) |
| Compiler | VS2012 (linker 11.0; Rich header mostly build 50727 and 61030) |
| Signature | Activision Authenticode; the signed sha256 image digest matches the file, so it is an unmodified original |
| Protection | Arxan, see docs/arxan.md |
| Platform | Steam (`steam_api64.dll`), D3D11, DirectSound, HID |

Use: a helper, not the target. The community BO3 clients name addresses in the Steam build, and those names can be
carried to the Store build by matching. The two builds use different compilers (VS2012 vs VS2019 with LTCG), so
matching relies on strings, constants and the call graph, never on code bytes or position.

### Ghidra analysis (Steam)

First pipeline run (Ghidra 12.1.4) on the unpacked image: unpack 12 min in CI (hash matched the pinned
`unpacked_sha256`), analysis 2 h, decompile 6 shards of 7 to 14 min. The pipeline's own commit failed on GitHub's
100 MB file limit (the graph's function table was 123 MB), so this run was published from its artifacts with the
fixed tools/graph/sync.py, which now splits big tables into parts.

- Ghidra found 426,463 functions, 332,822 of them tiny fragments in Arxan's own `.text` section (15AAEA000).
  Those are excluded from the published tables (`exclude` in target.toml, tools/ghidra/publish.py).
- Game code: 93,641 functions (93,638 in `.text`, 3 in `.interpr`), covering 46.9 MB. Decompiled: 79,771 ok,
  13,869 thunks, 1 failed.
- Checked against `.pdata` in the game `.text`: 40,147 of 40,177 plain entries are Ghidra functions (30 missed);
  the 28,535 chained entries are fragments of parent functions.
- 2.5 times the Store build's function count: VS2012 without LTCG inlines far less than VS2019 with LTCG, and the
  13,869 thunks include jumps Arxan inserted into game code.

Second run, with tools/ghidra/CreateTableFunctions.java: 5,033 data pointers led into game code with no function
(3 more pointed inside a function); all 5,033 became functions. Now **98,792 game functions**, 84,748 decompiled,
14,043 thunks, 1 failure.
