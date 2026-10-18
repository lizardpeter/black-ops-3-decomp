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

After both builds were re-analysed with tools/ghidra/CreateTableFunctions.java: **12,835 of the Store build's
41,932 non-thunk functions matched** (30.6%), each to a different Steam function.

| method | pairs | first run (before table functions) |
|---|---:|---:|
| string | 2,920 | 2,911 |
| constant | 204 | 201 |
| named (registrations, data tables) | 2,394 | 1,804 |
| callee propagation | 3,478 | 3,466 |
| caller propagation | 3,839 | 3,842 |
| total | 12,835 | 12,224 |

The percentage fell because the Store build gained 5,000 functions; most of the new ones are reached only through
tables, and the named stage pairs 590 more of them.

## How good it is

There is no ground truth for this pair (neither build has symbols), so precision is unmeasured. Two checks:

- **Call-graph consistency.** For a matched pair, a matched callee on the Store side should map to a callee of
  the Steam function. It does for 77.2% of 39,732 such edges (caller 87.6%, callee 83.5%, constant 74.7%,
  string 67.9%, named 61.6%). This is a lower bound on agreement, not an error rate: LTCG inlines many callees in
  the Store build, so a correct pair can still have edges that don't line up.
- **Spot checks** of named pairs read right: Lua functions match on their registered names, `DB_LoadXFile` on its
  "Error loading fastfile" string, `ClientCommand` on its command strings.

On Ghosts, the same matcher was validated on two symbol builds (docs/matching.md there). Before relying on a
match here, check its evidence.

## Names carried to the Store build

`tools/match/carry_names.py BlackOps3_MSStore --write` turns the pairs whose Steam function has a name in
records/names.tsv into names.tsv rows for the Store build: 1,956 functions (1,623 before the table functions), each with method
`boiii-free symbols+match:<method>`, the lower of the two confidences, and evidence naming the Steam function and
the match. A Store function named by any other method keeps that name. Re-run it after re-matching or after new
Steam names.
