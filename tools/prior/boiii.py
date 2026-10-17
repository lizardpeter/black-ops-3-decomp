#!/usr/bin/env python3
"""Carry the Ezz BOIII client's legacy-client names into records/names.tsv for BlackOps3_Steam.

    python3 tools/prior/boiii.py <boiii-free checkout> [--write]

Ezz BOIII (GPL-3.0, docs/prior-art.md) declares each game symbol as `symbol<type> Name{current, legacy, server}`
in src/client/game/symbols/. The legacy column is our Steam build (PE checksum 0x888C368). Only names and
addresses are taken, as facts with their evidence; none of the client's code or types.

The kind comes from where the address falls, not the declared type (functions are often declared through
typedefs such as `hks::lua_CFunction` or `cmd::xcommandFunc_t`), and is checked against our own analysis:
  function  in the game .text: must be a Ghidra function start in analysis/BlackOps3_Steam/functions.tsv
  data      in a data section (.rdata, .data, .tls, _RDATA)
Anything else is reported and skipped.
An address the client gives two different names is a conflict and recorded under neither. Rows this tool wrote
before (method `boiii-free symbols`) are replaced; every other row in names.tsv is kept as it is.

Without --write, prints the counts only.
"""
import csv
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = "BlackOps3_Steam"
METHOD = "boiii-free symbols"
COLUMNS = ["build", "va", "kind", "symbol", "name", "source", "method", "confidence", "evidence"]
TEXT = (0x140001000, 0x142F7C600)
DATA_SECTIONS = {".rdata": (0x142F87000, 0x1432D1000), ".data": (0x1432D1000, 0x15A8A7420),
                 ".tls": (0x15A972000, 0x15A972400), "_RDATA": (0x15A973000, 0x15A976400)}
SYM = re.compile(r"symbol<(?P<type>[^;{}]*?)>\s*(?P<name>[A-Za-z_]\w*)\s*\{\s*(?P<a>0x[0-9A-Fa-f]+|0)"
                 r"\s*(?:,\s*(?P<b>0x[0-9A-Fa-f]+|0))?\s*(?:,\s*(?P<c>0x[0-9A-Fa-f]+|0))?\s*\}", re.S)
csv.field_size_limit(1 << 30)


def read_tsv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def main():
    src = Path(sys.argv[1])
    write = "--write" in sys.argv
    commit = subprocess.run(["git", "-C", str(src), "rev-parse", "--short=7", "HEAD"],
                            capture_output=True, text=True).stdout.strip() or "unknown"
    starts = {int(r["va"], 16) for r in read_tsv(ROOT / "analysis" / BUILD / "functions.tsv")}

    found = defaultdict(set)   # va -> {(kind, name, file)}
    total = 0
    for hpp in sorted((src / "src/client/game/symbols").rglob("*.hpp")):
        for m in SYM.finditer(hpp.read_text(errors="ignore")):
            total += 1
            legacy = int(m["b"], 16) if m["b"] else 0
            if not legacy:
                continue
            kind = "function" if TEXT[0] <= legacy < TEXT[1] else "data"
            # `_Com_SessionMode_GetMode` style: the client's raw symbol behind an inline wrapper of the real name
            name = m["name"][1:] if re.match(r"_[A-Z][a-z]", m["name"]) and kind == "function" else m["name"]
            found[legacy].add((kind, name, hpp.relative_to(src).as_posix()))

    rows, stats = [], defaultdict(int)
    for va in sorted(found):
        entries = found[va]
        names = {(k, n) for k, n, _ in entries}
        if len(names) > 1:
            stats["conflict"] += 1
            continue
        kind, name = next(iter(names))
        files = sorted({f for _, _, f in entries})
        if kind == "function":
            if va not in starts:
                stats["function: not a Ghidra function start"] += 1
                continue
            check = "a Ghidra function start in our unpacked image"
        else:
            sec = next((s for s, (lo, hi) in DATA_SECTIONS.items() if lo <= va < hi), None)
            if not sec:
                stats["outside the game .text and the data sections"] += 1
                continue
            check = f"in {sec}"
        stats[f"{kind}: recorded"] += 1
        rows.append({"build": BUILD, "va": f"{va:X}", "kind": kind, "symbol": "", "name": name, "source": "",
                     "method": METHOD, "confidence": "0.9",
                     "evidence": f"Ezz BOIII {commit} {', '.join(files)} legacy-client address; {check}"})

    print(f"{total} symbol declarations, {len(found)} distinct legacy addresses")
    for k in sorted(stats):
        print(f"  {stats[k]:>6}  {k}")
    if not write:
        return
    path = ROOT / "records" / "names.tsv"
    kept = [r for r in read_tsv(path) if not (r["build"] == BUILD and r["method"] == METHOD)]
    with open(path, "w", newline="\n") as f:
        f.write("\t".join(COLUMNS) + "\n")
        for r in sorted(kept + rows, key=lambda r: (r["build"], r["va"], r["kind"])):
            f.write("\t".join(r.get(c, "") for c in COLUMNS) + "\n")
    print(f"wrote {len(rows)} rows to records/names.tsv ({len(kept)} other rows kept)")


if __name__ == "__main__":
    main()
