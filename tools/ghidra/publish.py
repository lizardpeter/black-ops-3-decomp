#!/usr/bin/env python3
"""Turn raw Ghidra exports into the committed analysis/<build>/ layout.

    python3 tools/ghidra/publish.py <build-id> <raw-dir>

<raw-dir> holds what ExportAll.java and Decompile.java wrote:
  functions.tsv callgraph.tsv symbols.tsv strings.tsv types.h disasm.jsonl decomp-*.jsonl

Pseudocode and disassembly are grouped by the ORIGINAL source file, taken from the PDB
(analysis/<build>/pdb/functions.tsv), falling back to the linker MAP's lib/obj. Inside a file,
functions are ordered by their original line number, then address.

A build's `exclude` list in target.toml ([{name, start, end}], hex VAs, end exclusive) keeps code that is not
the game's out of everything written here (functions, call graph, pseudocode, disassembly), e.g. the section
holding Arxan's own code. The saved Ghidra project still contains it.

Generated output only: never hand-edit what this writes.
"""
import csv
import json
import re
import shutil
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
csv.field_size_limit(1 << 30)


def read_tsv(path):
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def safe(part: str) -> str:
    part = part.replace("<external>", "_external").replace("<", "_").replace(">", "_")
    return re.sub(r"[^A-Za-z0-9._+\-/ ]", "_", part).strip("/ ") or "_unnamed"


def group_of(va, pdb, mapobj):
    p = pdb.get(va)
    if p and p["module_source"]:
        return safe(p["module_source"]), p
    m = mapobj.get(va)
    if m:
        lib = Path(m["lib"]).stem if m["lib"] else ""
        obj = Path(m["obj"]).stem
        return safe((f"_lib/{lib}/{obj}" if lib else f"_obj/{obj}").lower()), p
    # No PDB/MAP source for this function (retail builds): group by 64 KB address block until matching
    # against a reference build assigns it a source file.
    return f"_unattributed/{va[:4]}0000", p


def excluded_ranges(build):
    cfg = tomllib.loads((ROOT / "target.toml").read_text())
    b = next((b for b in cfg.get("build", []) if b["id"] == build), {})
    return [(e["name"], int(e["start"], 16), int(e["end"], 16)) for e in b.get("exclude", [])]


def main():
    build, raw = sys.argv[1], Path(sys.argv[2])
    out = ROOT / "analysis" / build
    ranges = excluded_ranges(build)
    dropped = defaultdict(int)

    def keep(va):
        v = int(va, 16)
        for name, lo, hi in ranges:
            if lo <= v < hi:
                dropped[name] += 1
                return False
        return True

    def copy_filtered(src, dst, cols):
        """Copy a Ghidra TSV, leaving out rows whose address columns fall in an excluded range."""
        with open(src, newline="") as f, open(dst, "w", newline="\n") as o:
            header = f.readline()
            o.write(header)
            idx = [header.rstrip("\n").split("\t").index(c) for c in cols if c in header.rstrip("\n").split("\t")]
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if all(not any(lo <= int(parts[i], 16) < hi for _, lo, hi in ranges) for i in idx if parts[i]):
                    o.write(line)
    pdb = {r["va"]: r for r in read_tsv(out / "pdb" / "functions.tsv")}
    mapobj = {r["va"]: r for r in read_tsv(out / "map" / "publics.tsv") if "f" in r["flags"]}

    gdir = out / "ghidra"
    gdir.mkdir(parents=True, exist_ok=True)
    for name in ("functions.tsv", "callgraph.tsv", "symbols.tsv", "strings.tsv", "types.h"):
        if not (raw / name).exists():
            continue
        if ranges and name == "functions.tsv":
            copy_filtered(raw / name, gdir / name, ["va"])
        elif ranges and name == "callgraph.tsv":
            copy_filtered(raw / name, gdir / name, ["caller", "callee"])
        else:
            shutil.copyfile(raw / name, gdir / name)
    for log in raw.glob("*.log"):
        (out / "logs").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(log, out / "logs" / log.name)

    ghidra = [g for g in read_tsv(raw / "functions.tsv") if keep(g["va"])]
    decomp = {}
    for shard in sorted(raw.glob("decomp-*.jsonl")):
        for line in open(shard):
            o = json.loads(line)
            decomp[o["va"]] = o
    disasm = {}
    if (raw / "disasm.jsonl").exists():
        for line in open(raw / "disasm.jsonl"):
            o = json.loads(line)
            disasm[o["va"]] = o["asm"]

    groups = defaultdict(list)
    joined = []
    for g in ghidra:
        va = g["va"]
        grp, p = group_of(va, pdb, mapobj)
        line = int(p["line"]) if p and p["line"] else 1 << 30
        groups[grp].append((line, va, g, p))
        d = decomp.get(va)
        joined.append([
            va, g["size"], g["name"], (p or {}).get("name", ""), (mapobj.get(va) or {}).get("name", ""),
            grp, (p or {}).get("line", ""), g["thunk"], g["instructions"], g["bytes_sha256"],
            "ok" if d and "c" in d else ("failed" if d else ("thunk" if g["thunk"] else "none")),
        ])

    # Only replace what this run actually produced: a missing stage must never wipe earlier results.
    if not decomp:
        print(f"{build}: no decompiler output in {raw}; keeping existing pseudocode/")
    for sub, have in (("pseudocode", bool(decomp)), ("disasm", bool(disasm))):
        if have:
            shutil.rmtree(out / sub, ignore_errors=True)
    for grp, items in groups.items():
        items.sort(key=lambda t: (t[0], t[1]))
        c_parts, a_parts = [], []
        for line, va, g, p in items:
            where = f"{p['line_source']}:{p['line']}" if p and p["line"] else "line unknown"
            head = f"// {va}  {g['name']}  ({where})\n"
            d = decomp.get(va)
            if d is not None:
                c_parts.append(head + (d.get("c") or f"// decompile failed: {d.get('error', '')}\n"))
            if va in disasm:
                a_parts.append(f"; {va}  {g['name']}  ({where})\n" + disasm[va])
        for sub, parts, ext in (("pseudocode", c_parts, ".c"), ("disasm", a_parts, ".asm")):
            if parts and (decomp if sub == "pseudocode" else disasm):
                path = out / sub / (grp + ext)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"// GENERATED by tools/ghidra/publish.py from build {build}. Do not edit.\n\n"
                                + "\n".join(parts))

    with open(out / "functions.tsv", "w", newline="\n") as f:
        f.write("va\tsize\tghidra_name\tpdb_name\tmap_name\tsource\tline\tthunk_of\tinstructions\tbytes_sha256\tdecompile\n")
        for r in sorted(joined):
            f.write("\t".join(str(x) for x in r) + "\n")

    ok = sum(1 for r in joined if r[-1] == "ok")
    print(f"{build}: {len(joined)} functions, {len(groups)} source groups, {ok} decompiled"
          + "".join(f"; {n} excluded ({name})" for name, n in dropped.items()))


if __name__ == "__main__":
    main()
