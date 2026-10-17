# Working in black-ops-3-decomp

Decompilation of Call of Duty: Black Ops III (T7, PC, x64). Read this before changing anything.

The structure, method and tools come from `lizardpeter/ghosts-decomp` (Ghosts, x64), which took them from
`lizardpeter/black-ops-1-decomp` (BO1). This repo owns its own copy of the tools and adapts them; there is no
shared toolkit. Comments in the copied tools still use Ghosts examples (the Store build, the PS4 server) where
they describe what a mechanism was built for.

## The one rule: generated vs authored

Every file is exactly one of these. They never share a folder.

| Kind | Where | Who writes it |
|---|---|---|
| **Generated** | `analysis/<build>/`, `analysis/graph/`, `STATUS.md` | Only the scripts in `tools/`. Never hand-edit. Re-running the pipeline on the same input reproduces it. |
| **Authored** | `src/`, `include/`, `tests/`, `docs/`, `records/` | People and agents. |

If a generated file is wrong, fix the script that wrote it and re-run. Don't patch the output.

## Layout

```
target.toml          builds (sha256 + R2 key of each original file), project id, protection
analysis/<build>/    GENERATED per build
  functions.tsv        every function: address, size, name, signature, bytes hash, decompile status
  unpack/              how a protected build was unpacked (log, sections changed, OEP, image hash)
  ghidra/              Ghidra exports (functions, callgraph, symbols, strings, types.h) + saved project (split tar)
  pseudocode/<group>.c Ghidra decompiler output, grouped by original source file once known
  disasm/<group>.asm   disassembly, same grouping
  pdb/ map/            symbol tables from a reference build's PDB / linker MAP
  match/               reference -> target identifications with evidence and confidence
  logs/                pipeline logs
records/             AUTHORED small facts; the only input to the graph besides analysis/
  functions.tsv        status of each reconstructed function, per build
  names.tsv            identifications in builds without symbols: name, method, evidence, confidence
  bugs.tsv             everything worth fixing, for the enhanced build
src/ include/        AUTHORED faithful reconstruction, mirroring the original source tree
enhanced/            AUTHORED (once needed) overrides for the enhanced build, same layout as src/
tests/differential/  differential tests (x64 Unicorn harness)
docs/<topic>.md      method notes and per-build findings. Topic names, never dates.
tools/               pipeline scripts (unpack/, ghidra/, pdb/, match/, graph/, recon/, prior/ for community names)
```

Folder and file names describe *what*, never *when*. Dates belong in commit messages.

## Faithful and enhanced

`src/` is the **faithful** decomp: original behaviour, bugs included, verified function by function. The
**enhanced** build is the faithful code plus overrides from `enhanced/` (security, bugfix, modernize, feature),
each recorded in `records/patches.tsv`; both are created with the first enhancement. Never fix a bug in `src/`.
See docs/variants.md.

**Everything worth fixing goes in `records/bugs.tsv`**, the enhanced build's fix queue: not only outright bugs,
but anything in the original that should be fixed or improved. Columns: id (`B` + 4 digits), build, va, function,
source, kind, priority (`high` for security, crashes and gameplay-visible problems, else `medium` or `low`),
description, evidence (the reproducing test, or the code/disassembly; say whether a current caller can trigger
it), enhanced (`planned`, `fixed <patch id>`, or `keep` when the original behaviour is wanted). Kinds: `security`,
`crash`, `hang`, `logic`, `ub`, `robustness`, `limit`, `precision`, `performance`, `quality`. The faithful code
keeps it all; security issues are also written up in docs/security.md. Plain float rounding that changes nothing
visible isn't a finding.

## Addresses

x64 virtual addresses at the image base 0x140000000, written as 9 upper-case hex digits without `0x`
(`14073DCA4`). Every tool uses that form.

## Protected builds

A build with `protection = "arxan"` in target.toml has encrypted code on disk. It is unpacked by a tool in
`tools/unpack/`, and Ghidra analyses the unpacked image, never the raw file. The unpacked image is generated,
never stored: its sha256 is pinned in target.toml (`unpacked_sha256`) so anyone can reproduce it.

## Function status ladder

Every function in `records/functions.tsv` has exactly one status:

`located -> named -> typed -> decompiled -> compiles -> matches -> integrated`

- `located`: entry and size known (Ghidra; `.pdata` gives every non-leaf function's bounds on x64)
- `named`: original name known (PDB/MAP, or a recorded cross-build match)
- `typed`: original prototype known
- `decompiled`: authored source exists in `src/`
- `compiles`: that source builds in CI
- `matches`: passes the differential test against the original
- `integrated`: linked into the runnable reconstruction

`matches` needs a passing automated test; CI fails if a record claims more than the tests show. A
function kept below `matches` on purpose carries a note saying why. `STATUS.md` and the graph are both
computed from this file. Don't track progress anywhere else.

Every cross-build identification records its method, evidence and confidence. Never match on address
position across differently linked builds.

## Graph

Graph `re_t7` on the Graph DB is **derived**. `tools/graph/sync.py` turns `records/` plus
`analysis/<build>/functions.tsv` into a MERGE-by-key import set under `analysis/graph/`, loaded with the
Graph DB `bulk_import_file` tool (import folder `t7/` on the Graph DB machine). Never write ad-hoc Cypher to
the graph; change records and re-sync. The graph holds identity, relationships and status only, with no code text.

## Originals

The game files (exe, pdb, map) are never committed. They live in R2 under the keys in `target.toml`,
and the pipeline verifies their sha256 before use. Helpers for reading the bucket are not part of this
repo.
