#!/usr/bin/env python3
"""Compile the reconstruction into one x64 Windows DLL, hybrid-linked against the original exe.

    python3 tools/build_recon.py                 # -> build/recon.dll, build/recon.symbols.tsv, build/hybrid.tsv
    python3 tools/build_recon.py --build <id>    # the same against another build -> build/<id>/

  The default links against the reference build (MAP + PDB). Another build (the Store build) resolves names
  through tools/symbols.py: records/names.tsv and the matcher's identifications.

- Every file under src/ is compiled with clang targeting x86_64-pc-windows-msvc, so the Win64 calling convention
  and MSVC x64 C++ name mangling apply. tools/recon/include holds build-environment headers.
- Every defined function is exported under its decorated name, so tests find it by the ORIGINAL
  decorated name from the MAP: a wrong prototype simply isn't found.
- Hybrid link: any symbol the reconstruction uses but does not define yet is resolved to the original
  binary's address from the MAP (and original statics, declared with T7_STATIC, from the PDB). Functions become a `jmp [rip+0]; .quad <va>` thunk into the original code,
  data becomes an absolute symbol at the original address. So a function can be reconstructed and tested
  before anything it calls is. build/hybrid.tsv lists every such dependency.
- Thread-local variables (`__declspec(thread)`, e.g. dvar_modifiedFlags) are reached through `_tls_index` and an
  offset into the TLS block, not an address. The original's `_tls_index` is linked like any data; each original
  TLS variable is placed in the DLL's own .tls section at the same offset it has in the original's, so the
  offsets the compiler emits are the original's. Nothing else in the reconstruction may use TLS.

This is the `compiles` gate. It is not byte matching: that needs the original VC11 (VS2012) x64 compiler.

Ported from black-ops-1-decomp (x86). `-fms-compatibility-version=17.00` makes clang follow VS2012, the original
compiler: no thread-safe statics or TLS guards, which VS2012 didn't have and the original binary doesn't link.
"""
import csv
import os
import subprocess
import tomllib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import symbols  # noqa: E402

TRIPLE = "--target=x86_64-pc-windows-msvc"
CFLAGS = [TRIPLE, "-fms-compatibility-version=17.00", "-O0", "-ffp-contract=off", "-fno-exceptions",
          "-fms-extensions", "-fno-stack-protector", "-ffreestanding", "-fno-builtin", "-Wall", "-Werror",
          "-Wno-unused-function", "-Wno-unused-variable", f"-I{ROOT / 'include'}",
          f"-isystem{ROOT / 'tools' / 'recon' / 'include'}"]
csv.field_size_limit(1 << 30)


def out_dir(build: str) -> Path:
    """build/ for the reference build (the default), build/<build>/ for any other."""
    return ROOT / "build" if build == symbols.reference_build() else ROOT / "build" / build


def run(*cmd):
    subprocess.run([str(c) for c in cmd], check=True)


def nm(obj, *flags):
    out = subprocess.run(["llvm-nm", *flags, str(obj)], check=True, capture_output=True, text=True).stdout
    return [line.split() for line in out.splitlines() if line.strip()]


def original_tls_section(build):
    """[start, end) of a symbol build's .tls section (analysis/<build>/pdb/sections.tsv)."""
    path = ROOT / "analysis" / build / "pdb" / "sections.tsv"
    if not path.exists():
        return 0, 0
    with open(path, newline="") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r["name"] == ".tls":
                lo = int(r["va"], 16)
                return lo, lo + int(r["vsize"], 16)
    return 0, 0


def import_slots(build):
    """{import name: IAT slot va} of the build's exe (for CRT calls a build without a MAP makes through its
    import table: the Store build links the CRT dynamically)."""
    import pefile
    path = Path(os.environ.get("T7_ORIGINALS", ROOT / ".work" / "originals")) / f"{build}.exe"
    if not path.exists():
        return {}
    pe = pefile.PE(str(path), fast_load=True)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
    return {imp.name.decode(): imp.address for d in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])
            for imp in d.imports if imp.name}


def main():
    build = sys.argv[sys.argv.index("--build") + 1] if "--build" in sys.argv else symbols.reference_build()
    reference = symbols.has_map(build)
    BUILD = out_dir(build)
    BUILD.mkdir(parents=True, exist_ok=True)
    objs, sources = [], []
    for src in sorted((ROOT / "src").rglob("*.cpp")):
        rel = src.relative_to(ROOT / "src")
        obj = BUILD / "obj" / rel.with_suffix(".obj")
        obj.parent.mkdir(parents=True, exist_ok=True)
        run("clang++", "-std=c++17", *CFLAGS, "-c", src, "-o", obj)
        objs.append(obj)
        sources.append(obj)
    if not objs:
        sys.exit("no sources")

    # build environment: the MSVC float marker
    (BUILD / "fltused.c").write_text("int _fltused = 0;\n")
    run("clang", *CFLAGS, "-c", BUILD / "fltused.c", "-o", BUILD / "fltused.obj")
    env_objs = [BUILD / "fltused.obj"]

    defined, exports, rows = set(), [], []
    for obj in sources:
        for parts in nm(obj, "--defined-only", "--extern-only"):
            if len(parts) == 3:
                defined.add(parts[2])
                if parts[1] in ("T", "t"):
                    exports.append(parts[2])
                    rows.append(f"{parts[2]}\t{obj.relative_to(BUILD / 'obj').with_suffix('.cpp')}")
    for obj in env_objs:
        defined |= {p[2] for p in nm(obj, "--defined-only", "--extern-only") if len(p) == 3}
    undefined = sorted({p[-1] for o in objs + env_objs for p in nm(o, "--undefined-only")} - defined)

    table = symbols.table(build)
    orig = {k: (va, kind == "function") for k, (va, kind) in table.items() if not k.startswith("t7s@")}
    statics = {k: va for k, (va, kind) in table.items() if k.startswith("t7s@")}
    # Only functions that exist in the original are exported (and tested). Anything else defined in src/
    # is an inline helper from a header; flag it so new names do not slip in unnoticed.
    stray = [e for e in exports if e not in orig and e not in ("_fltused",)]
    # A build whose PDB names each function's source file has the function only when it comes from the same file:
    # the PS4 server's ds/ds_net.cpp NET_Init is not the PC's win32/win_net.cpp NET_Init. Functions the PDB places
    # in a header (inline) are left alone.
    pdb_source = {}
    for r in symbols.read_tsv(ROOT / "analysis" / build / "pdb" / "functions.tsv"):
        pdb_source.setdefault(int(r["va"], 16), []).append((r["name"], r["module_source"], r["line_source"]))
    sources_of = {}
    for r in rows:
        sym, src = r.split("\t")
        sources_of.setdefault(sym, set()).add(src.replace("\\", "/"))
    other_file = set()
    for e in set(stray) | {e for e in exports if e in orig}:
        bn = e[1:].split("@", 1)[0] if e.startswith("?") else e
        vas = [orig[e][0]] if e in orig else [va for k, (va, _) in orig.items()
                                               if (k[1:].split("@", 1)[0] if k.startswith("?") else k) == bn]
        # by address and plain name: identical code folding puts several functions at one address
        known = [(ms, ls) for va in vas for name, ms, ls in pdb_source.get(va, []) if name == bn]
        if known and all(ls.endswith(".cpp") and not ({ms, ls} & sources_of.get(e, set())) for ms, ls in known):
            other_file.add(e)
    if other_file:
        print(f"note: {len(other_file)} function(s) in {build} come from another source file (not exported):",
              ", ".join(sorted(other_file)))
    stray = [e for e in stray if e not in other_file]
    exports = [e for e in exports if e in orig and e not in other_file]
    rows = [r for r in rows if r.split("\t")[0] in orig and r.split("\t")[0] not in other_file]
    # A stray symbol whose plain name matches an original function is a prototype mismatch (wrong parameter
    # or return type, constness, calling convention): the function would silently drop out of testing.
    def base_name(sym):
        return sym[1:].split("@", 1)[0] if sym.startswith("?") else sym
    orig_names = {}
    for o in orig:
        orig_names.setdefault(base_name(o), []).append(o)
    mismatched = [f"{e}  (original: {', '.join(orig_names[base_name(e)])})" for e in stray if base_name(e) in orig_names]
    if mismatched:
        sys.exit("prototype differs from the original's decorated name:\n  " + "\n  ".join(mismatched))
    if stray and reference:
        print("note: defined in src/ but not in the original MAP (not exported):", ", ".join(stray))
    elif stray:
        print(f"note: {len(stray)} function(s) in src/ are not identified in {build} yet (not exported)")
    # Anything the reconstruction uses that this build doesn't have (a build without a MAP knows only what is
    # identified: records/names.tsv and the matcher; code for another build, such as client code against the
    # server) links to a trap: a function to ud2, data to address 0. A test that reaches it fails instead of
    # running the wrong code. Imports (Win32, and the CRT for a build that links it dynamically) go through the
    # exe's import address table.
    slots = import_slots(build)
    asm = ["\t.text"]
    hybrid = ["symbol\tkind\tva"]
    ref_build = symbols.reference_build()
    tls_lo, tls_hi = original_tls_section(build if reference else ref_build)
    ref_table = symbols.table(ref_build)
    tls = []
    for u in undefined:
        q = '"' + u + '"'
        if u in slots and not reference:
            # an import of this build is authoritative: a matcher pair for a CRT name (statically linked in the
            # reference) can point at the wrong function in a build that imports it
            orig.pop(u, None)
        if u not in orig and u not in statics:
            if u in slots:
                asm += [f"\t.globl {q}", f"{q}:", f"\tmovabsq ${slots[u]:#x}, %rax", "\tjmpq *(%rax)"]
                hybrid.append(f"{u}\timport\t{slots[u]:09X}")
            elif u in ref_table and tls_lo <= ref_table[u][0] < tls_hi:
                tls.append((ref_table[u][0] - tls_lo, q))  # keeps the link valid; not this build's offset
                hybrid.append(f"{u}\tunresolved-tls\t")
            elif u in ref_table and ref_table[u][1] == "data" or u.startswith("t7s@"):
                asm += [f"\t.globl {q}", f"\t.set {q}, 0"]
                hybrid.append(f"{u}\tunresolved-data\t")
            else:
                asm += [f"\t.globl {q}", f"{q}:", "\tud2"]
                hybrid.append(f"{u}\tunresolved-function\t")
            continue
        va, is_func = orig[u] if u in orig else (statics[u], False)
        if reference and tls_lo <= va < tls_hi:
            tls.append((va - tls_lo, q))
            hybrid.append(f"{u}\ttls\t{va:09X}")
            continue
        if is_func:
            asm += [f"\t.globl {q}", f"{q}:", "\tjmpq *0(%rip)", f"\t.quad {va:#x}"]
        else:
            asm += [f"\t.globl {q}", f"\t.set {q}, {va:#x}"]
        hybrid.append(f"{u}\t{'function' if is_func else 'data'}\t{va:09X}")
    if tls:
        asm += ['\t.section .tls$, "dw"', "hybrid_tls_start:"]
        for off, q in sorted(tls):
            asm += [f"\t.skip {off} - (. - hybrid_tls_start)", f"\t.globl {q}", f"{q}:"]
        asm += [f"\t.skip {tls_hi - tls_lo} - (. - hybrid_tls_start)"]
    (BUILD / "hybrid.s").write_text("\n".join(asm) + "\n")
    run("clang", TRIPLE, "-c", BUILD / "hybrid.s", "-o", BUILD / "hybrid.obj")
    (BUILD / "hybrid.tsv").write_text("\n".join(hybrid) + "\n")

    dll = BUILD / "recon.dll"
    run("lld-link", "/dll", "/noentry", "/nodefaultlib", "/base:0x180000000", "/fixed", f"/out:{dll}",
        *[f"/export:{e}" for e in exports],  # x64: no leading underscore on C names
        *objs, *env_objs, BUILD / "hybrid.obj")
    (BUILD / "recon.symbols.tsv").write_text("symbol\tsource\n" + "\n".join(rows) + "\n")
    unresolved = sum(1 for h in hybrid if "\tunresolved" in h)
    if unresolved and reference:
        print(f"note: {unresolved} symbol(s) not in {build} (trap; build/hybrid.tsv):",
              ", ".join(h.split("\t")[0] for h in hybrid if "\tunresolved" in h))
    print(f"{dll}: {len(exports)} functions from {len(sources)} files; "
          f"{len(undefined) - unresolved} symbols resolved to {build}" +
          (f", {unresolved} not identified there yet (trap)" if unresolved else ""))


if __name__ == "__main__":
    main()
