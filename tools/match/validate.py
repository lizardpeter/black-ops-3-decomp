#!/usr/bin/env python3
"""Score a match against ground truth when the target build has its own symbols.

    python3 tools/match/match.py <reference> <other symbol build> --same-compiler
    python3 tools/match/validate.py <reference> <other symbol build>

Both server builds have MAP/PDB names, so matching one to the other "blind" measures the matcher's
precision per method. A pair counts as correct when the two addresses share a MAP or PDB name.
"""
import collections
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
csv.field_size_limit(1 << 30)


def rd(p):
    with open(p, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def names(build):
    """Every name at each function address: identical code folding (/OPT:ICF) gives one body several names,
    and the two builds may fold differently, so a pair is correct when the name sets intersect."""
    out = collections.defaultdict(set)
    for r in rd(ROOT / "analysis" / build / "functions.tsv"):
        for n in (r["map_name"], r["pdb_name"]):
            if n:
                out[r["va"]].add(n)
    publics = ROOT / "analysis" / build / "map" / "publics.tsv"
    if publics.exists():
        for r in rd(publics):
            if "f" in r["flags"]:
                out[r["va"]].add(r["name"])
    pdb = ROOT / "analysis" / build / "pdb" / "functions.tsv"
    if pdb.exists():
        for r in rd(pdb):
            out[r["va"]].add(r["name"])
    return out


ref_id, tgt_id = sys.argv[1], sys.argv[2]
truth, refn = names(tgt_id), names(ref_id)
res = collections.defaultdict(lambda: [0, 0, 0])
for m in rd(ROOT / "analysis" / tgt_id / "match" / "functions.tsv"):
    t, r = truth.get(m["target_va"], set()), refn.get(m["ref_va"], set())
    res[m["method"]][2 if not (t and r) else (0 if t & r else 1)] += 1
tot = [sum(v[i] for v in res.values()) for i in range(3)]
for k, (ok, bad, unk) in sorted(res.items()) + [("all", tot)]:
    print(f"{k:8} correct {ok:6}  wrong {bad:5}  unverifiable {unk:4}  precision {100 * ok / max(ok + bad, 1):5.1f}%")
