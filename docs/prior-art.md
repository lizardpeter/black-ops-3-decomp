# Prior art and symbol sources

What exists for BO3 (T7) outside this repo, and what it is worth to us. Surveyed 2026-10 (see git history);
re-check before relying on availability.

## No decomp exists

No reimplementation of the T7 engine is known. The community work is runtime clients and patches that hook the
retail Steam exe, plus decompiled game *scripts* (GSC/CSC), which are game data, not engine code.

## Hook clients

| Project | License | Targets | Contents |
|---|---|---|---|
| **Ezz BOIII** (github.com/Ezz-lol/boiii-free, surveyed at 5aa7fac, 2026-09-27) | GPL-3.0 | Three Steam builds, told apart by the PE checksum: the current client (0x6531394, the 2026 updates), the **legacy client (0x888C368)** and the unranked dedicated server (0x14C28B4) | `src/client/game/symbols/`: 3,542 symbols by subsystem, 1,258 of them functions, each with up to three addresses (current, legacy, server); `structs/`: ~555 struct/enum/union definitions. Hooks and helpers, not decompiled engine code. |
| **CBServers boiii** (github.com/CBServers/boiii, surveyed at a8009ee, 2026-08-09) | GPL-3.0 | Legacy client and dedicated server | `symbols.hpp`: 158 symbols, 119 functions, client + server addresses. The older layout of the same data. |
| momo5502 **boiii** (original, taken down; archive.org "boiii-original-momo5502") | GPL-3.0 | Legacy client | Origin of both forks above. |

**Our Steam build is the legacy client.** `BlackOps3_Steam` has PE checksum 0x888C368, and against our
unpacked image: of the 835 functions Ezz BOIII gives a legacy address, 649 are exactly a `.pdata` function start,
and the other 186 decode as small functions without unwind entries (leaf functions such as
`Com_SessionMode_GetMode`). Their current-client column does not fit (83 of 1,167 on a function start), as
expected for a different build. So the legacy addresses apply to our analysis without any matching step.

How we use it: names and addresses are facts, and enter `records/names.tsv` as identifications for
`BlackOps3_Steam` with method `boiii-free symbols` and the commit as evidence, checked against our own analysis
(function start, strings, call graph). From there the matcher carries them to the Store build. Their *code* and
struct definitions are not imported: that would make this repo GPL-3.0, which is the user's decision.

Arxan: these clients let the stub decrypt the game at runtime (Ezz BOIII can dump the decrypted exe with `-dump`).
We decrypt by emulation instead (docs/arxan.md).

## Newer Steam builds

The Steam exe was updated in February 2026 and again on 2026-09-10 (Steam build 24784313); Ezz BOIII's
current-client addresses are for one of those (checksum 0x6531394). Our Steam exe is the 2023 build those
updates replaced. A copy of the current Steam exe would add Ezz BOIII's 1,258 current-client function names
(~420 more than the legacy column) and the last changes Activision made, which the Store build may or may not
share.

## Community patches

- **t7patch** (shiversoftdev, github.com/shiversoftdev/t7patch; updated fork Scroptss/T7Patch for the 2026
  updates): fixes the known RCE vulnerabilities and an FPS issue. Source in a separate repo (Black-Ops-3-Projects).
  A source for docs/security.md and the bug ledger once those subsystems are decompiled.
- **T7x** (AlterWare) and **BO3Enhanced**: other clients/patches named by t7patch; not surveyed yet.

## Scripts

- **t7-source** (shiversoftdev): decompiled GSC/CSC scripts. Not engine code, but the script function names
  and the builtins they call name engine functions (the script builtin tables).

## Symbol builds

None known publicly for PC. The Store and Steam exes name their PDBs (`d:\workspace\outrun\t7\game\pc\BlackOps3.pdb`,
`Q:\t7\pc\game\pc\cod_Ship.pdb`) but neither PDB is available. Worth looking for: console or prototype builds
with MAPs or PDBs, as Ghosts' servers and Xbox 360 prototypes had.
