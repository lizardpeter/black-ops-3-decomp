#!/usr/bin/env python3
"""Carry a reference build's recorded names to a target build through the matcher's pairs.

    python3 tools/match/carry_names.py <target-build> [--write]

For every pair in analysis/<target>/match/functions.tsv whose reference function has a name in records/names.tsv
(e.g. the Steam build's BOIII names), writes a names.tsv row for the target function. The row keeps the trail:
method `<reference method>+match:<match method>`, confidence the lower of the two, and evidence naming the
reference function, how it was named and how it was matched.

Names a reference build has from its own PDB/MAP need no carrying (tools/symbols.py reads those directly); this is
for references named only by identification. A target function that already has a name in names.tsv from any
other method keeps it. Rows this tool wrote before for the target are replaced.

Without --write, prints the counts only.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLUMNS = ["build", "va", "kind", "symbol", "name", "source", "method", "confidence", "evidence"]
csv.field_size_limit(1 << 30)


def read_tsv(path):
    if not Path(path).exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def carried(row):
    return "+match:" in row["method"]


def main():
    target = sys.argv[1]
    write = "--write" in sys.argv
    path = ROOT / "records" / "names.tsv"
    names = read_tsv(path)
    pairs = read_tsv(ROOT / "analysis" / target / "match" / "functions.tsv")

    ref_name = {}
    for r in names:
        if r["kind"] == "function" and not r["name"].startswith("sub_"):
            ref_name[(r["build"], r["va"])] = r
    already = {r["va"] for r in names if r["build"] == target and not carried(r)}
    # a name an authored identification gives to another address in the target wins over a carried one: the
    # match behind the carried name is then wrong (e.g. callee propagation pairing a neighbour)
    authored_names = {r["name"] for r in names if r["build"] == target and not carried(r)}

    rows, stats = [], Counter()
    for p in pairs:
        n = ref_name.get((p["ref_build"], p["ref_va"]))
        if n is None:
            continue
        if p["target_va"] in already:
            stats["target already named"] += 1
            continue
        if n["name"] in authored_names:
            stats["name given elsewhere by an authored identification"] += 1
            continue
        stats[p["method"]] += 1
        conf = min(float(n["confidence"] or 0), float(p["confidence"] or 0))
        rows.append({"build": target, "va": p["target_va"], "kind": "function", "symbol": n["symbol"],
                     "name": n["name"], "source": n["source"],
                     "method": f"{n['method']}+match:{p['method']}", "confidence": f"{conf:.2f}",
                     "evidence": f"matched to {p['ref_build']} {p['ref_va']} ({n['name']}, named by {n['method']}) "
                                 f"by {p['method']}: {p['evidence']}"})

    print(f"{target}: {len(rows)} names carried by match method {dict(stats)}")
    if not write:
        return
    kept = [r for r in names if not (r["build"] == target and carried(r))]
    with open(path, "w", newline="\n") as f:
        f.write("\t".join(COLUMNS) + "\n")
        for r in sorted(kept + rows, key=lambda r: (r["build"], r["va"], r["kind"])):
            f.write("\t".join(r.get(c, "") for c in COLUMNS) + "\n")
    print(f"wrote {len(rows)} rows to records/names.tsv ({len(kept)} other rows kept)")


if __name__ == "__main__":
    main()
