#!/usr/bin/env python3
"""Extract structured tables from an original PDB (+ linker MAP) into analysis/<build>/.

Generated output only. Re-running on the same PDB/MAP reproduces identical files.

    python3 tools/pdb/extract.py <build-id> <exe> <pdb|-> <map|->

Pass `-` for a file the build doesn't have (e.g. a server build with an EXE and MAP but no PDB).

Needs llvm-pdbutil (apt install llvm) and resymc
(cargo install --locked --git https://github.com/ergrelet/resym --rev 5be09381 resymc).

Writes:
  analysis/<build>/pdb/sections.tsv    section index, name, virtual address, virtual size
  analysis/<build>/pdb/modules.tsv     one row per compiland: index, obj, primary source file
  analysis/<build>/pdb/functions.tsv   every function the PDB knows: va, size, name, scope, module, source, line, type
  analysis/<build>/pdb/lines.tsv       function start -> (source file, first line) from line tables
  analysis/<build>/pdb/locals.tsv      parameter/local names and types per function, as Ghidra stack offsets
  analysis/<build>/pdb/statics.tsv     file- and function-static data: source file, scope, name, va, type
  analysis/<build>/pdb/types.h         every PDB type as C++ with offsets and sizes (resymc), independent of Ghidra;
                                       negative enumerators corrected from llvm-pdbutil (resymc prints -1 as 0xff)
  analysis/<build>/pdb/types-errors.txt  types resymc could not rebuild
  analysis/<build>/pdb/raw/*.txt       llvm-pdbutil dumps the tables were parsed from
  analysis/<build>/map/publics.tsv     linker MAP publics: va, name, flags, lib, obj
"""
import hashlib
import re
import struct
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Original source roots (lower case, trailing backslash), from target.toml `source_roots`. Original paths are
# not known yet: fill them in from the first PDB/MAP/assert strings that show the source tree.
SRC_PREFIXES = [r.lower().rstrip("\\") + "\\" for r in tomllib.loads((ROOT / "target.toml").read_text()).get("source_roots", [])]


def image_base(exe: Path) -> int:
    """ImageBase from the PE optional header (0x140000000 for x64 MSVC exes, 0x400000 for x86)."""
    d = exe.read_bytes()[:0x400]
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    magic = struct.unpack_from("<H", d, pe + 24)[0]
    return struct.unpack_from("<Q", d, pe + 24 + 24)[0] if magic == 0x20B else struct.unpack_from("<I", d, pe + 24 + 28)[0]


def rel_source(path: str) -> str:
    """Original absolute Windows path -> repo-style relative path ('game_mp/pregame.cpp')."""
    if not path:
        return ""
    low = path.lower()
    for pre in SRC_PREFIXES:
        if low.startswith(pre):
            return path[len(pre):].replace("\\", "/")
    # outside the game tree (CRT, SDKs): keep it recognisable but drive-less
    p = re.sub(r"^[a-zA-Z]:\\", "", path)
    return "<external>/" + p.replace("\\", "/")


def make_canon(paths):
    """One spelling per path, case-insensitively. The original tree mixes 'DW/', 'Dw/', 'dw/' (Windows
    didn't care); a case-sensitive checkout would split them and a Windows checkout would collide.
    Per path component, prefer a spelling with capitals, then the ASCII-first one: deterministic."""
    spellings = {}
    for path in paths:
        parts = path.split("/")
        for i in range(len(parts)):
            spellings.setdefault("/".join(parts[:i + 1]).casefold(), set()).add(parts[i])
    best = {k: min(v, key=lambda c: (c == c.lower(), c)) for k, v in spellings.items()}

    def canon(path):
        if not path:
            return path
        parts = path.split("/")
        return "/".join(best["/".join(parts[:i + 1]).casefold()] for i in range(len(parts)))
    return canon


def pdbutil(*args) -> str:
    return subprocess.run(["llvm-pdbutil", *args], check=True, capture_output=True, text=True,
                          errors="replace").stdout


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tsv(path: Path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join("" if v is None else str(v).replace("\t", " ").replace("\n", " ") for v in r) + "\n")


def parse_sections(text):
    secs, cur = [], None
    for line in text.splitlines():
        m = re.match(r"\s*SECTION HEADER #(\d+)", line)
        if m:
            cur = {"index": int(m.group(1))}
            secs.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"\s*(\S+) name$", line)
        if m:
            cur["name"] = m.group(1)
        m = re.match(r"\s*([0-9A-Fa-f]+) virtual size$", line)
        if m:
            cur["vsize"] = int(m.group(1), 16)
        m = re.match(r"\s*([0-9A-Fa-f]+) virtual address$", line)
        if m:
            cur["rva"] = int(m.group(1), 16)
    return secs


def parse_modules(text):
    mods, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"\s*Mod (\d{4}) \| `(.*)`:", line)
        if m:
            cur = {"index": int(m.group(1)), "obj": m.group(2), "lib": "", "source": ""}
            mods[cur["index"]] = cur
            continue
        if cur is None:
            continue
        m = re.match(r"\s*Obj: `(.*)`:", line)
        if m:
            cur["lib"] = m.group(1) if m.group(1) != cur["obj"] else ""
        m = re.search(r"src file ni: \d+ `(.*)`", line)
        if m:
            cur["source"] = m.group(1)
    return mods


def derive_module_sources(mods, procs, first_line):
    """VS2012 x64 PDBs leave the module's 'src file' empty. Use the module's own functions' line-table sources:
    the source whose file stem equals the object's stem, else the most common one. Fills procs' module_source
    and the module records, so pseudocode groups by original compiland as on BO1."""
    from collections import Counter
    by_mod = {}
    for p in procs:
        src = first_line.get(p[0], ("", 0))[0]
        if src and not str(p[4]) == "":
            by_mod.setdefault(p[4], Counter())[src] += 1
    for idx, cnt in by_mod.items():
        m = mods.get(idx)
        if m is None or m["source"]:
            continue
        stem = Path(m["obj"].replace("\\", "/")).stem.lower()
        same = [s for s in cnt if Path(s).stem.lower() == stem]
        m["derived"] = max(same, key=lambda s: cnt[s]) if same else cnt.most_common(1)[0][0]
    for p in procs:
        m = mods.get(p[4])
        if not p[5] and m is not None and m.get("derived"):
            p[5] = m["derived"]


def parse_procs(text, mods, va_of):
    out, mod = [], None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"\s*Mod (\d{4}) \|", line)
        if m:
            mod = int(m.group(1))
        m = re.match(r"\s*\d+ \| (S_GPROC32|S_LPROC32|S_THUNK32) \[size = \d+\] `(.*)`\s*$", line)
        if m:
            kind, name = m.group(1), m.group(2)
            body = " ".join(lines[i + 1:i + 3])
            a = re.search(r"addr = (\d{4}):(\d+)", body)
            sz = re.search(r"(?:code size|len) = (\d+)", body)
            ty = re.search(r"type = `0x[0-9A-F]+ \((.*)\)`", body)
            if a:
                va = va_of(int(a.group(1)), int(a.group(2)))
                scope = {"S_GPROC32": "global", "S_LPROC32": "local", "S_THUNK32": "thunk"}[kind]
                src = mods.get(mod, {}).get("source", "")
                out.append([va, int(sz.group(1)) if sz else "", name, scope, mod, rel_source(src),
                            ty.group(1) if ty else ""])
        i += 1
    return out


def parse_locals(text, va_of):
    """Named stack variables per procedure, converted to Ghidra stack offsets (relative to ESP at entry).

    S_BPREL32 is relative to EBP after `push ebp; mov ebp, esp`, so Ghidra offset = offset - 4.
    S_REGREL32 on EBP is the same. On EBX it is MSVC's aligned-stack frame (`mov ebx, esp` after
    `push ebx`): EBX-relative parameters also map with -4, but EBP then points into a realigned
    frame, so EBP-relative locals of those functions are skipped. ESP-relative records are skipped.
    """
    procs, cur = [], None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"\s*\d+ \| (S_GPROC32|S_LPROC32) \[size = \d+\] `(.*)`\s*$", line)
        if m:
            a = re.search(r"addr = (\d{4}):(\d+)", lines[i + 1])
            cur = {"va": va_of(int(a.group(1)), int(a.group(2))), "vars": [], "aligned": False} if a else None
            if cur:
                procs.append(cur)
            continue
        m = re.match(r"\s*\d+ \| (S_BPREL32|S_REGREL32) \[size = \d+\] `(.*)`\s*$", line)
        if not (m and cur):
            continue
        detail = lines[i + 1]
        off = re.search(r"offset = (-?\d+)", detail)
        ty = re.search(r"type = 0x[0-9A-F]+ \((.*)\), (?:register|offset)", detail)
        reg = re.search(r"register = (\w+)", detail)
        reg = reg.group(1) if reg else "EBP"
        if reg == "EBX":
            cur["aligned"] = True
        if reg in ("EBP", "EBX") and off:
            o = int(off.group(1))
            if o >= 1 << 31:  # llvm-pdbutil prints some REGREL32 offsets as unsigned 32-bit
                o -= 1 << 32
            cur["vars"].append((reg, o - 4, m.group(2), ty.group(1) if ty else ""))
    rows = []
    for p in procs:
        seen = set()
        for reg, off, name, ty in p["vars"]:
            kind = "param" if off > 0 else "local"
            if p["aligned"] and reg == "EBP":
                continue
            if (kind, off) in seen:  # same slot reused by a nested scope: keep the outermost name
                continue
            seen.add((kind, off))
            rows.append([p["va"], kind, off, name, ty])
    return rows


def parse_statics(text, mods, va_of):
    """S_LDATA32 records per compiland. Scope is '' for file statics, else the enclosing function.
    Source is the module's repo-relative source: its PDB 'src file', or (VS2012 x64 leaves that empty) the one
    derive_module_sources() found from its functions' line tables, so T7_AT can name the compiland."""
    rows, mod, proc_end, proc = [], None, -1, ""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"\s*Mod (\d{4}) \|", line)
        if m:
            mod, proc_end, proc = int(m.group(1)), -1, ""
            continue
        m = re.match(r"\s*(\d+) \| (S_GPROC32|S_LPROC32|S_LDATA32|S_LTHREAD32) \[size = \d+\] `(.*)`\s*$", line)
        if not m:
            continue
        rec, kind, name = int(m.group(1)), m.group(2), m.group(3)
        if kind in ("S_GPROC32", "S_LPROC32"):
            e = re.search(r"end = (\d+)", lines[i + 1])
            proc, proc_end = name, int(e.group(1)) if e else -1
            continue
        if rec > proc_end:
            proc = ""
        a = re.search(r"addr = (\d{4}):(\d+)", lines[i + 1])
        ty = re.search(r"type = 0x[0-9A-F]+ \((.*)\), addr", lines[i + 1])
        if a and mod is not None and int(a.group(1)) != 0:  # segment 0: absolute/optimised away
            m = mods.get(mod, {})
            src = rel_source(m["source"]) if m.get("source") else m.get("derived", "")
            rows.append([src, proc, name, va_of(int(a.group(1)), int(a.group(2))),
                         ty.group(1) if ty else "", "tls" if kind == "S_LTHREAD32" else ""])
    return rows


def parse_lines(text, va_of):
    """First line of each line-table block, keyed by its start address."""
    out, src = {}, ""
    pending = None
    for line in text.splitlines():
        m = re.match(r"^([a-zA-Z]:\\.*) \(MD5:", line)
        if m:
            src = m.group(1)
            continue
        m = re.match(r"\s*(\d{4}):([0-9A-F]{8})-[0-9A-F]{8}, line/addr entries", line)
        if m:
            pending = va_of(int(m.group(1)), int(m.group(2), 16))
            continue
        if pending is not None:
            m = re.match(r"\s*(\d+) [0-9A-F]{8}", line)
            if m:
                out.setdefault(pending, (rel_source(src), int(m.group(1))))
                pending = None
    return out


def parse_map(text):
    rows = []
    # x86 MAPs print Rva+Base in 8 digits, x64 MAPs in 16
    pat = re.compile(r"^ ([0-9a-f]{4}):([0-9a-f]{8})\s+(\S+)\s+([0-9a-f]{8}|[0-9a-f]{16})((?: [fi])*)\s+(\S.*)$")
    for line in text.splitlines():
        m = pat.match(line)
        if not m:
            continue
        va = int(m.group(4), 16)
        if va == 0:
            continue  # absolute / imported placeholder rows
        flags = m.group(5).split()
        where = m.group(6).strip()
        lib, _, obj = where.rpartition(":")
        rows.append([va, m.group(3), "".join(flags), lib, obj])
    return rows


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    build, exe, pdb, mapf = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
    out = ROOT / "analysis" / build
    base = image_base(exe)
    inputs = [("exe", exe)]
    if str(pdb) != "-":
        inputs.append(("pdb", pdb))
        extract_pdb(out, pdb, base)
    if str(mapf) != "-":
        inputs.append(("map", mapf))
        map_text = mapf.read_text(errors="replace")
        (out / "map").mkdir(parents=True, exist_ok=True)
        rows = parse_map(map_text)
        tsv(out / "map" / "publics.tsv", ["va", "name", "flags", "lib", "obj"],
            [[f"{r[0]:09X}", *r[1:]] for r in sorted(rows, key=lambda r: (r[0], r[1]))])
        print(f"{build}: {len(rows)} MAP publics")
    (out / "inputs.tsv").write_text(
        "role\tfile\tsha256\n" + "".join(f"{role}\t{p.name}\t{sha256(p)}\n" for role, p in inputs))


def enum_values(types_dump: str) -> dict:
    """{enum name: {enumerator: value}} from `llvm-pdbutil dump -types`."""
    fieldlists, enums, cur, kind, name = {}, {}, None, None, None
    for line in types_dump.splitlines():
        m = re.match(r"\s*(0x[0-9A-F]+) \| (LF_\w+) \[size = \d+\](?: `(.*)`)?", line)
        if m:
            cur, kind, name = int(m.group(1), 16), m.group(2), m.group(3)
            if kind == "LF_FIELDLIST":
                fieldlists[cur] = {}
            continue
        if kind == "LF_FIELDLIST":
            e = re.match(r"\s*- LF_ENUMERATE \[(\S+) = (-?\d+)\]", line)
            if e:
                fieldlists[cur][e.group(1)] = int(e.group(2))
        elif kind == "LF_ENUM":
            f = re.match(r"\s*field list: (0x[0-9A-F]+)", line)
            if f and name not in enums and int(f.group(1), 16) in fieldlists:
                enums[name] = fieldlists[int(f.group(1), 16)]
    return enums


def fix_enum_values(text: str, types_dump: str) -> str:
    """resymc prints a negative enumerator stored as a one- or two-byte leaf as its raw low byte(s)
    (`GPAD_PHYSAXIS_NONE = 0xff` where the PDB says -1). Put back the PDB's value wherever they differ."""
    enums = enum_values(types_dump)
    out, values = [], None
    for line in text.split("\n"):
        m = re.match(r"enum (\S+) : \w+ \{", line)
        if m:
            values = enums.get(m.group(1))
        elif line.startswith("};"):
            values = None
        elif values is not None:
            e = re.match(r"(\s*)(\w+) = (0x[0-9a-f]+|-?\d+),$", line)
            if e and e.group(2) in values and int(e.group(3), 0) != values[e.group(2)]:
                v = values[e.group(2)]
                line = f"{e.group(1)}{e.group(2)} = {v if v < 0 else hex(v)},"
        out.append(line)
    return "\n".join(out)


def extract_types(out, pdb):
    """All types as C++ from resymc: complete even where Ghidra's PDB loader gives up on a deep struct."""
    res = subprocess.run(["resymc", "dump-all", "-s", "-x", "-f", "portable", str(pdb), str(out / "pdb" / "types.h")],
                         capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"resymc failed: {res.stderr[-2000:]}")
    # resymc emits types in hash order, different on every run: sort for a reproducible file. Forward
    # declarations first, then each definition (separated by blank lines) ordered by its first line.
    path = out / "pdb" / "types.h"
    chunks = [c.strip("\n") for c in path.read_text().split("\n\n") if c.strip()]
    fwd = sorted({l for c in chunks for l in c.splitlines()
                  if re.fullmatch(r"(struct|union|enum|class) [^{]+;", l)})
    defs = sorted({"\n".join(l for l in c.splitlines() if l not in fwd) for c in chunks} - {""})
    text = "\n".join(fwd) + "\n\n" + "\n\n".join(defs) + "\n"
    path.write_text(fix_enum_values(text, pdbutil("dump", "-types", str(pdb))))
    errors = sorted(line.split("] ", 1)[-1] for line in res.stderr.splitlines() if "ERROR" in line)
    (out / "pdb" / "types-errors.txt").write_text("".join(e + "\n" for e in errors))
    return len(errors)


def extract_pdb(out, pdb, base):
    raw = out / "pdb" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    print(f"{out.name}: types.h written, {extract_types(out, pdb)} type(s) resymc could not rebuild")

    dumps = {
        "summary": pdbutil("dump", "-summary", str(pdb)),
        "sections": pdbutil("dump", "-section-headers", str(pdb)),
        "modules": pdbutil("dump", "-modules", str(pdb)),
        "symbols": pdbutil("dump", "-symbols", str(pdb)),
        "publics": pdbutil("dump", "-publics", str(pdb)),
        "lines": pdbutil("dump", "-l", str(pdb)),
    }
    for k, v in dumps.items():
        (raw / f"{k}.txt").write_text(v)

    secs = parse_sections(dumps["sections"])
    rva = {s["index"]: s["rva"] for s in secs}

    def va_of(seg, off):
        return f"{base + rva[seg] + off:09X}"

    tsv(out / "pdb" / "sections.tsv", ["index", "name", "va", "vsize"],
        [[s["index"], s.get("name", ""), f"{base + s['rva']:09X}", f"{s.get('vsize', 0):X}"] for s in secs])

    mods = parse_modules(dumps["modules"])
    first_line = parse_lines(dumps["lines"], va_of)
    procs = parse_procs(dumps["symbols"], mods, va_of)
    procs.sort(key=lambda r: (r[0], r[2]))
    derive_module_sources(mods, procs, first_line)

    canon = make_canon([rel_source(m[k]) for m in mods.values() for k in ("obj", "lib", "source")]
                       + [p[5] for p in procs] + [s for s, _ in first_line.values()])
    for p in procs:
        p[5] = canon(p[5])
    first_line = {va: (canon(s), ln) for va, (s, ln) in first_line.items()}
    statics = parse_statics(dumps["symbols"], mods, va_of)
    tsv(out / "pdb" / "statics.tsv", ["source", "scope", "name", "va", "type", "kind"],
        sorted(([canon(r[0]), *r[1:]] for r in statics), key=lambda r: (r[0], r[1], r[2])))
    tsv(out / "pdb" / "modules.tsv", ["module", "obj", "lib", "source"],
        [[m["index"], canon(rel_source(m["obj"])), canon(rel_source(m["lib"])), canon(rel_source(m["source"])) if m["source"] else canon(m.get("derived", ""))]
         for m in sorted(mods.values(), key=lambda m: m["index"])])
    tsv(out / "pdb" / "functions.tsv", ["va", "size", "name", "scope", "module", "module_source", "line_source", "line", "type"],
        [[p[0], p[1], p[2], p[3], p[4], p[5], *first_line.get(p[0], ("", "")), p[6]] for p in procs])
    locals_ = parse_locals(dumps["symbols"], va_of)
    tsv(out / "pdb" / "locals.tsv", ["va", "kind", "offset", "name", "type"], sorted(locals_, key=lambda r: (r[0], r[1] != "param", abs(r[2]))))
    tsv(out / "pdb" / "lines.tsv", ["va", "source", "line"],
        [[va, s, ln] for va, (s, ln) in sorted(first_line.items())])

    print(f"{out.name}: {len(mods)} modules, {len(procs)} PDB procs, {len(first_line)} line blocks")


if __name__ == "__main__":
    main()
