#!/usr/bin/env python3
"""Map a build's online surface: every place its code can reach a network, and the functions around it.

    python3 tools/net/surface.py [<build-id>]      (default: the Store build)

Reads only generated analysis (analysis/<build>/disasm, ghidra/symbols.tsv, ghidra/callgraph.tsv, functions.tsv),
records/names.tsv, and the original exe's import table (fetched by tools/fetch_originals.py, sha256-checked). Writes
analysis/<build>/net/:

  imports.tsv    every import from a network DLL: its IAT slot and how many functions reference the slot
  hosts.tsv      every string naming a server (URL, *.demonware.net, xboxlive.com, ...) and the functions using it
  functions.tsv  every function with a direct network reference, plus every function in the Demonware library
                 (attributed by the library's own __FILE__ strings and bdClass:: log strings), with what it touches
                 and how many callers it has
  callers.tsv    the direct callers of each function in functions.tsv (one row per edge), so the layer above the
                 sockets/HTTP calls can be read without the whole call graph

"Network DLL" is the NET_DLLS list below. Direct references only: a reference is any instruction operand equal to
the IAT slot or the string's address (calls through the slot, and loads of it into a register). Calls through the
GDK runtime's API table (QueryApiImpl) and through vtables are not visible here; docs/network.md says what that
leaves out.

Generated output only: never hand-edit what this writes.
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import pefile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "differential"))
from harness import original_exe  # noqa: E402  (locates and sha256-checks the original)

csv.field_size_limit(1 << 30)

# DLL (lower case) -> what it is for
NET_DLLS = {
    "ws2_32.dll": "sockets",
    "winhttp.dll": "http",
    "xcurl.dll": "http",
    "gamechat2.dll": "voice",
    "wlanapi.dll": "netinfo",
    "iphlpapi.dll": "netinfo",
}
# Strings that name a server
HOST_RE = re.compile(r"(https?://|wss?://|[a-z0-9.-]+\.(demonware\.net|xboxlive\.com|activision\.com|"
                     r"callofduty\.com|microsoft\.com|live\.com|xbox\.com|steampowered\.com)\b)", re.I)
# The Demonware library's __FILE__ strings, and its log strings of the form "bdSomething::method"
DW_PATH_RE = re.compile(r"\\libs\\DemonWare[^\\]*\\(.+\.(?:cpp|c|h|inl))$", re.I)
DW_CLASS_RE = re.compile(r"^(bd[A-Z][A-Za-z0-9_]*)::")
HEADER_RE = re.compile(r"^; ([0-9A-F]{9})  (\S+)")
INSN_RE = re.compile(r"^  ([0-9A-F]{9})  [0-9A-F]+\s+(.*)$")
ADDR_RE = re.compile(r"0x(14[0-9a-f]{7})\b")


def read_tsv(path):
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def write_tsv(path, header, rows):
    path.write_text("\t".join(header) + "\n" + "".join("\t".join(str(x) for x in r) + "\n" for r in rows))


def import_slots(exe: Path):
    pe = pefile.PE(str(exe), fast_load=True)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
                                           pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT"]])
    out = {}
    for attr in ("DIRECTORY_ENTRY_IMPORT", "DIRECTORY_ENTRY_DELAY_IMPORT"):
        for d in getattr(pe, attr, []):
            dll = d.dll.decode().lower()
            if dll not in NET_DLLS:
                continue
            for i in d.imports:
                name = i.name.decode() if i.name else f"#{i.ordinal}"
                out[i.address] = (dll, name)
    return out


def main():
    build = sys.argv[1] if len(sys.argv) > 1 else "BlackOps3_MSStore"
    an = ROOT / "analysis" / build
    exe = original_exe(build)
    slots = import_slots(exe)

    # strings by address (ghidra's string symbols carry the text in strings.tsv)
    strings = {int(r["va"], 16): r["value"] for r in read_tsv(an / "ghidra" / "strings.tsv")}
    hosts = {va: s for va, s in strings.items() if HOST_RE.search(s)}
    dw_paths = {va: m.group(1).replace("\\\\", "/").replace("\\", "/")
                for va, s in strings.items() if (m := DW_PATH_RE.search(s.replace("\\\\", "\\")))}
    dw_classes = {va: m.group(1) for va, s in strings.items() if (m := DW_CLASS_RE.match(s))}

    names = {}
    for r in read_tsv(an / "functions.tsv"):
        names[int(r["va"], 16)] = (r["ghidra_name"], int(r["size"]))
    for r in read_tsv(ROOT / "records" / "names.tsv"):
        if r["build"] == build and r["kind"] == "function":
            va = int(r["va"], 16)
            names[va] = (r["name"], names.get(va, ("", 0))[1])

    # one pass over the disassembly: which function references which slot / string
    refs = defaultdict(lambda: defaultdict(set))  # fn -> kind -> {target}
    slot_fns = defaultdict(set)
    host_fns = defaultdict(set)
    for f in sorted((an / "disasm").rglob("*.asm")):
        fn = None
        for line in f.open():
            h = HEADER_RE.match(line)
            if h:
                fn = int(h.group(1), 16)
                continue
            if fn is None or "0x14" not in line:
                continue
            m = INSN_RE.match(line)
            if not m:
                continue
            for a in ADDR_RE.findall(m.group(2)):
                a = int(a, 16)
                if a in slots:
                    dll, imp = slots[a]
                    refs[fn][NET_DLLS[dll]].add(imp)
                    slot_fns[a].add(fn)
                elif a in hosts:
                    refs[fn]["host"].add(hosts[a])
                    host_fns[a].add(fn)
                elif a in dw_paths:
                    refs[fn]["dw_file"].add(dw_paths[a])
                elif a in dw_classes:
                    refs[fn]["dw_class"].add(dw_classes[a])

    callers = defaultdict(set)
    for r in read_tsv(an / "ghidra" / "callgraph.tsv"):
        callers[int(r["callee"], 16)].add(int(r["caller"], 16))

    out = an / "net"
    out.mkdir(exist_ok=True)
    write_tsv(out / "imports.tsv", ["dll", "import", "purpose", "slot", "functions"],
              sorted(([dll, imp, NET_DLLS[dll], f"{a:09X}", len(slot_fns[a])] for a, (dll, imp) in slots.items()),
                     key=lambda r: (r[0], r[1])))
    write_tsv(out / "hosts.tsv", ["va", "string", "functions"],
              [[f"{a:09X}", s, ",".join(f"{x:09X}" for x in sorted(host_fns[a]))] for a, s in sorted(hosts.items())])

    kinds = ["sockets", "http", "voice", "netinfo", "host", "dw_file", "dw_class"]
    rows = []
    for fn in sorted(refs):
        name, size = names.get(fn, (f"FUN_{fn:09X}", 0))
        rows.append([f"{fn:09X}", size, name, len(callers[fn])] +
                    [",".join(sorted(refs[fn].get(k, ()))) for k in kinds])
    write_tsv(out / "functions.tsv", ["va", "size", "name", "callers"] + kinds, rows)
    edges = []
    for fn in sorted(refs):
        for c in sorted(callers[fn]):
            edges.append([f"{fn:09X}", names.get(fn, ("",))[0], f"{c:09X}", names.get(c, (f"FUN_{c:09X}",))[0],
                          "yes" if c in refs else ""])
    write_tsv(out / "callers.tsv", ["callee", "callee_name", "caller", "caller_name", "caller_listed"], edges)
    print(f"{build}: {len(slots)} network imports, {len(hosts)} host strings, {len(rows)} functions, "
          f"{len(edges)} caller edges -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
