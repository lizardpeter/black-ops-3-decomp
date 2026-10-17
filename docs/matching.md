# Matching the Store build to the Steam build

`tools/match/match.py BlackOps3_Steam BlackOps3_MSStore` gives Store functions the identity of Steam functions,
with method, confidence and evidence per pair, in `analysis/BlackOps3_MSStore/match/functions.tsv`. Content only,
never position: the two builds use different compilers (VS2012 vs VS2019 with LTCG) and different layouts. The
matcher and its stages come from ghosts-decomp (its docs/matching.md has the method and its ground-truth
validation); the Steam build is the reference here because it has names (records/names.tsv, from the BOIII
client), not because it has symbols.

Run with the unpacked Steam image in `.work/originals/` (docs/arxan.md).

## Fix for BO3

The Steam exe has two `.text` sections (the game's and Arxan's). The matcher picked sections by name and so
disassembled Arxan's: no string or constant match on the Steam side. It now reads function bytes from the mapped
image and scans every `.rdata`/`.data` section.

## Result

12,224 of the Store build's 36,929 non-thunk functions matched (33.1%), each to a different Steam function.

| method | pairs |
|---|---:|
| string | 2,911 |
| constant | 201 |
| named (registrations, data tables) | 1,804 |
| callee propagation | 3,466 |
| caller propagation | 3,842 |

1,623 of the pairs give a Store function a BOIII name (1,267 of them through `named`, mostly Lua `LuaCall`
functions registered under their script name).

## How good it is

There is no ground truth for this pair (neither build has symbols), so precision is unmeasured. Two checks:

- **Call-graph consistency.** For a matched pair, a matched callee on the Store side should map to a callee of
  the Steam function. It does for 77.3% of 39,709 such edges (caller 87.6%, callee 83.6%, constant 74.7%,
  string 67.9%, named 62.4%). This is a lower bound on agreement, not an error rate: LTCG inlines many callees in
  the Store build, so a correct pair can still have edges that don't line up.
- **Spot checks** of named pairs read right: Lua functions match on their registered names, `DB_LoadXFile` on its
  "Error loading fastfile" string, `ClientCommand` on its command strings.

On Ghosts, the same matcher was validated on two symbol builds (docs/matching.md there). Before relying on a
match here, check its evidence; names carried to the Store build go into records/names.tsv with that evidence.
