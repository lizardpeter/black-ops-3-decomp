#!/usr/bin/env python3
"""Compile the reconstruction into one x64 Windows DLL, hybrid-linked against the original exe.

    python3 tools/build_recon.py                 # -> build/recon.dll, build/recon.symbols.tsv, build/hybrid.tsv
    python3 tools/build_recon.py --build <id>    # the same against another build -> build/<id>/
    python3 tools/build_recon.py --build <id> --enhanced   # the enhanced build -> build/<id>/enhanced/

  The default links against the reference build (MAP + PDB). Another build (the Store build) resolves names
  through tools/symbols.py: records/names.tsv and the matcher's identifications.

- Every file under src/ is compiled with clang targeting x86_64-pc-windows-msvc, so the Win64 calling convention
  and MSVC x64 C++ name mangling apply. tools/recon/include holds build-environment headers.
- Every defined function is exported under its decorated name, so tests find it by the ORIGINAL
  decorated name from the MAP: a wrong prototype simply isn't found.
- Hybrid link: any symbol the reconstruction uses but does not define yet is resolved to the original
  binary's address from the MAP (and original statics, declared with T7_STATIC, from the PDB). So a function can
  be reconstructed and tested before anything it calls is. build/hybrid.tsv lists every such dependency.
  Every such address lives in one slot table in the DLL, rebased at load by the DLL's entry point to wherever the
  exe actually is (the Store exe is ASLR-enabled): functions become a thunk that jumps through their slot, and the
  units' references to exe data (compiled with -mcmodel=large) are rewritten into loads from the data's slot.
  No code may hold an exe address directly; the link checks that. See docs/hybrid-link.md.
- Thread-local variables (`__declspec(thread)`, e.g. dvar_modifiedFlags) are reached through `_tls_index` and an
  offset into the TLS block, not an address. The original's `_tls_index` is linked like any data; each original
  TLS variable is placed in the DLL's own .tls section at the same offset it has in the original's, so the
  offsets the compiler emits are the original's. Nothing else in the reconstruction may use TLS.

The enhanced build (--enhanced) compiles src/ and enhanced/ together (docs/variants.md). A function defined in
enhanced/ replaces the src/ function of the same decorated name everywhere, calls from src/ included: enhanced
objects link first and lld-link keeps the first definition (/force:multiple). enhanced/ functions are exported
whether or not the original has them, for tests/enhanced/. enhanced/offline/ is not part of it: that is the
standalone offline DLL (tools/offline/build_dll.py). Ported from ghosts-decomp.

This is the `compiles` gate. It is not byte matching: that needs the original VC11 (VS2012) x64 compiler.

Ported from black-ops-1-decomp (x86). `-fms-compatibility-version=17.00` makes clang follow VS2012, the original
compiler: no thread-safe statics or TLS guards, which VS2012 didn't have and the original binary doesn't link.
"""
import csv
import os
import re
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
          f"-isystem{ROOT / 'tools' / 'recon' / 'include'}",
          # Every global is reached as `movabsq $sym, %reg`: the one form exe_relative_asm rewrites into a load from
          # the DLL's own slot table, which reaches the exe wherever either image is loaded (docs/hybrid-link.md).
          "-mcmodel=large",
          # Under the large model a switch's jump table holds 64-bit `case - table` differences across sections,
          # which COFF can only store as 32 bits: a negative one comes back 4 GB off. Compare chains instead
          # (same behaviour); compile_unit rejects any table that slips through.
          "-fno-jump-tables"]
csv.field_size_limit(1 << 30)


def out_dir(build: str) -> Path:
    """build/ for the reference build (the default), build/<build>/ for any other."""
    return ROOT / "build" if build == symbols.reference_build() else ROOT / "build" / build


def recon_output_dir(build: str, enhanced: bool = False) -> Path:
    """Canonical enhanced output always includes build ID; faithful remains as before."""
    return ROOT / "build" / build / "enhanced" if enhanced else out_dir(build)


def run(*cmd, quiet_duplicates=False):
    if not quiet_duplicates:
        subprocess.run([str(c) for c in cmd], check=True)
        return
    # the enhanced link: its intended duplicates (enhanced/ replacing src/) are not news
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    noise = ("duplicate symbol", ">>> defined at")
    out = [l for l in (r.stdout + r.stderr).splitlines() if l.strip() and not any(n in l for n in noise)]
    if out:
        print("\n".join(out))
    if r.returncode:
        raise subprocess.CalledProcessError(r.returncode, cmd)


def nm(obj, *flags):
    out = subprocess.run(["llvm-nm", *flags, str(obj)], check=True, capture_output=True, text=True).stdout
    return [line.split() for line in out.splitlines() if line.strip()]


def compile_unit(src, obj):
    """src -> obj through assembly: obj.s is kept, since exe_relative_asm may rewrite it and reassemble."""
    asm = obj.with_suffix(".s")
    run("clang++", "-std=c++17", *CFLAGS, "-S", src, "-o", asm)
    for line in asm.read_text().splitlines():
        if re.match(r"\s*\.(?:quad|long)\s+[.\w$@?\"]+\s*-\s*[.\w$@?\"]+\s*$", line):
            sys.exit(f"{asm}: a label-difference table ({line.strip()}): truncated to 32 bits across COFF sections")
    run("clang", TRIPLE, "-c", asm, "-o", obj)


SLOT_PREFIX = "t7x@"  # the slot holding the exe address of a symbol the reconstruction reads or writes as data
_TOKEN = re.compile(r'"([^"]+)"|([A-Za-z_.?$@][\w.?$@]*)')
_MOVABS = re.compile(r'^(\s*)movabsq\s+\$("[^"]+"|[A-Za-z_.?$@][\w.?$@]*)([+-](?:0x[0-9a-fA-F]+|\d+))?\s*,\s*(%r\w+)\s*(#.*)?$')


def exe_relative_asm(asm_path, exe_data):
    """Rewrite one unit's references to exe data into loads from the DLL's slot table. With -mcmodel=large clang
    reaches every global as `movabsq $sym[+off], %reg`; for a symbol of the exe that becomes
    `movq "t7x@sym"(%rip), %reg` (and `leaq off(%reg), %reg`, which leaves the flags alone). The slot is inside the
    DLL, so in reach wherever it is loaded, and it holds the exe's address, rebased at load (t7_hybrid_entry).
    Any other reference to an exe symbol stops the build: it would bake in an address that is wrong as soon as
    either image moves. Returns the number of references rewritten."""
    out, n = [], 0
    for line in asm_path.read_text().splitlines():
        names = {a or b for a, b in _TOKEN.findall(line.split("#", 1)[0])} & exe_data
        if not names:
            out.append(line)
            continue
        if line.strip().startswith(".addrsig_sym"):
            continue  # an address-significance hint for a symbol that no longer exists
        m = _MOVABS.match(line)
        if not m or m.group(2).strip('"') not in exe_data:
            sys.exit(f"{asm_path}: unsupported reference to exe data {sorted(names)}: {line.strip()}")
        indent, sym, off, reg = m.group(1), m.group(2).strip('"'), m.group(3), m.group(4)
        out.append(f'{indent}movq\t"{SLOT_PREFIX}{sym}"(%rip), {reg}')
        if off:
            out.append(f"{indent}leaq\t{int(off, 0)}({reg}), {reg}")
        n += 1
    asm_path.write_text("\n".join(out) + "\n")
    return n


def exe_preferred_base(build):
    """(ImageBase, SizeOfImage) from the build's exe header: what the slot table's addresses assume."""
    import pefile
    path = Path(os.environ.get("T7_ORIGINALS", ROOT / ".work" / "originals")) / f"{build}.exe"
    if not path.exists():
        sys.exit(f"{path}: the hybrid link needs the original exe (tools/fetch_originals.py {build} --only exe)")
    o = pefile.PE(str(path), fast_load=True).OPTIONAL_HEADER
    return o.ImageBase, o.SizeOfImage


def hybrid_entry(exe_base):
    """The DLL's entry point. On DLL_PROCESS_ATTACH it reads the exe's actual base from the PEB and adds the
    difference from its preferred base to every slot between t7_exe_slots_start and t7_exe_slots_end (exe data,
    original functions, the exe-return gadget, import table slots). Trap slots lie after the end and stay 0.
    Returns TRUE; does nothing on any other reason, or when the exe is at its preferred base."""
    return ["\t.text", "\t.globl t7_hybrid_entry", "t7_hybrid_entry:",
            "\tcmpl $1, %edx", "\tjne 2f",
            "\tmovq %gs:0x60, %rax", "\tmovq 0x10(%rax), %rax",
            f"\tmovabsq ${exe_base:#x}, %rcx", "\tsubq %rcx, %rax", "\tje 2f",
            "\tleaq t7_exe_slots_start(%rip), %rcx", "\tleaq t7_exe_slots_end(%rip), %rdx",
            "1:", "\tcmpq %rdx, %rcx", "\tjae 2f", "\taddq %rax, (%rcx)", "\taddq $8, %rcx", "\tjmp 1b",
            "2:", "\tmovl $1, %eax", "\tretq"]


def check_no_exe_addresses(dll, exe_base, exe_size):
    """The linked DLL's code must hold no address inside the exe's image, as an immediate or as a RIP-relative
    target: those are the references that break when either image is loaded somewhere else. Only the slot table
    (data) holds exe addresses, and t7_hybrid_entry rebases it."""
    out = subprocess.run(["llvm-objdump", "-d", "--no-show-raw-insn", "--section=.text", str(dll)],
                         check=True, capture_output=True, text=True).stdout
    bad = []
    for line in out.splitlines():
        if ":" not in line or not line.startswith(" "):
            continue
        for h in re.findall(r"0x([0-9a-fA-F]+)", line.split(":", 1)[1]):
            if exe_base <= int(h, 16) < exe_base + exe_size:
                bad.append(line.strip())
                break
    if bad:
        sys.exit(f"{dll}: code refers to the exe's image directly ({len(bad)}):\n  " + "\n  ".join(bad[:20]))


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


def exe_return_gadget(build):
    """(va, n) of the build's exe-return gadget (target.toml `exe_return`), checked against the exe: a call
    instruction, then `add rsp, n; ret`. None without one (the thunks then jump straight to the original)."""
    spec = symbols.build_spec(build)
    if "exe_return" not in spec:
        return None
    import pefile
    va = int(spec["exe_return"], 16)
    path = Path(os.environ.get("T7_ORIGINALS", ROOT / ".work" / "originals")) / f"{build}.exe"
    pe = pefile.PE(str(path), fast_load=True)
    code = pe.get_data(va - 5 - pe.OPTIONAL_HEADER.ImageBase, 10)
    if code[0] != 0xE8 or code[5:8] != b"\x48\x83\xc4" or code[9] != 0xC3:
        sys.exit(f"{build}: exe_return {va:09X} is not `call; add rsp, n; ret`: {code.hex()}")
    return va, code[8]


def function_thunk(q, slot, gadget_slot, index, n=0):
    """The hybrid link's call into an original function, whose address is in `slot` (the slot table: rebased at
    load). With an exe-return gadget (docs/obfuscation.md; its address in `gadget_slot`): the call is made with the
    gadget, inside the exe, as its return address, because the game's decoders hang when their caller lies outside
    the exe. The thunk builds a frame of its own: [S] the gadget, the home space, copies of the caller's stack
    arguments, and at S + 8 + n the address of a stub that drops the frame and returns to the real caller; the
    gadget's `add rsp, n; ret` lands there. Registers are passed through untouched (R10 is scratch, as at any call);
    at most (n - 0x20) / 8 stack arguments are copied."""
    if not gadget_slot:
        return [f"\t.globl {q}", f"{q}:", f"\tjmpq *{slot}(%rip)"]
    frame = (n + 16 + 15) & ~15
    slots = (n - 0x20) // 8
    label = f"t7_exe_return_{index}"
    lines = [f"\t.globl {q}", f"{q}:", f"\tsubq ${frame:#x}, %rsp"]
    for i in range(slots):
        lines += [f"\tmovq {frame + 0x28 + 8 * i:#x}(%rsp), %r10", f"\tmovq %r10, {0x28 + 8 * i:#x}(%rsp)"]
    lines += [f"\tleaq {label}(%rip), %r10", f"\tmovq %r10, {8 + n:#x}(%rsp)",
              f"\tmovq {gadget_slot}(%rip), %r10", "\tmovq %r10, (%rsp)",
              f"\tmovq {slot}(%rip), %r10", "\tjmpq *%r10",
              f"{label}:", f"\taddq ${frame - n - 16:#x}, %rsp", "\tretq"]
    return lines


def main():
    build = sys.argv[sys.argv.index("--build") + 1] if "--build" in sys.argv else symbols.reference_build()
    reference = symbols.has_map(build)
    enhanced = "--enhanced" in sys.argv
    # Enhanced artifacts always use a build-id-qualified directory, even when
    # this retail build happens to be the reference build. The canonical
    # packager and CI consume build/<build-id>/enhanced/recon.dll.
    BUILD = recon_output_dir(build, enhanced)
    BUILD.mkdir(parents=True, exist_ok=True)
    objs, sources = [], []
    for src in sorted((ROOT / "src").rglob("*.cpp")):
        rel = src.relative_to(ROOT / "src")
        obj = BUILD / "obj" / rel.with_suffix(".obj")
        obj.parent.mkdir(parents=True, exist_ok=True)
        compile_unit(src, obj)
        objs.append(obj)
        sources.append(obj)
    if not objs:
        sys.exit("no sources")
    enhanced_defs = set()
    if enhanced:
        enhanced_objs = []
        for src in sorted((ROOT / "enhanced").rglob("*.cpp")):
            rel = src.relative_to(ROOT / "enhanced")
            if rel.parts[0] == "offline":
                continue  # the standalone offline DLL, built by tools/offline/build_dll.py
            obj = BUILD / "obj" / "enhanced" / rel.with_suffix(".obj")
            obj.parent.mkdir(parents=True, exist_ok=True)
            compile_unit(src, obj)
            enhanced_objs.append(obj)
            enhanced_defs |= {p[2] for p in nm(obj, "--defined-only", "--extern-only") if len(p) == 3 and p[1] in ("T", "t")}
        objs = enhanced_objs + objs  # first definition wins: enhanced/ replaces src/
        sources = enhanced_objs + sources

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
                    if parts[2] not in {r.split("\t")[0] for r in rows}:  # an enhanced/ override is listed once
                        rows.append(f"{parts[2]}\t{obj.relative_to(BUILD / 'obj').with_suffix('.cpp')}")
    for obj in env_objs:
        defined |= {p[2] for p in nm(obj, "--defined-only", "--extern-only") if len(p) == 3}
    undefined = sorted({p[-1] for o in objs + env_objs for p in nm(o, "--undefined-only")} - defined)

    table = symbols.table(build)
    orig = {k: (va, kind == "function") for k, (va, kind) in table.items() if not k.startswith("t7s@")}
    if not reference:
        # identifications without decorated names (BO3): a decorated name the reconstruction defines or uses
        # resolves through its plain name (tools/symbols.py resolve)
        for sym in set(exports) | set(undefined):
            if sym not in orig:
                hit = symbols.resolve(build, sym)
                if hit:
                    orig[sym] = (hit[0], hit[1] == "function")
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
    stray = [e for e in stray if e not in other_file and e not in enhanced_defs]
    exports = list(dict.fromkeys(e for e in exports if (e in orig or e in enhanced_defs) and e not in other_file))
    rows = [r + (f"\t{orig[r.split(chr(9))[0]][0]:09X}" if r.split("\t")[0] in orig else "\t") for r in rows
            if (r.split("\t")[0] in orig or r.split("\t")[0] in enhanced_defs) and r.split("\t")[0] not in other_file]
    # A stray symbol whose plain name matches an original function is a prototype mismatch (wrong parameter
    # or return type, constness, calling convention): the function would silently drop out of testing.
    def base_name(sym):
        # the name with its class scope (`?create@bdPlatformSocket@@...` -> `create@bdPlatformSocket`), so methods
        # of different classes don't look like one function with two prototypes
        return sym[1:].split("@@", 1)[0] if sym.startswith("?") else sym
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
    gadget = exe_return_gadget(build)
    # Every exe address the DLL uses lives in one table of slots, rebased at load by t7_hybrid_entry; code reaches
    # a slot RIP-relatively (it is inside the DLL). exe_slots: (label, va); exe_data: symbols the units read or write
    # as data, rewritten by exe_relative_asm; traps: data slots holding 0, outside the rebased range.
    exe_slots, exe_data, traps = [], set(), []

    def slot(va, label=None):
        label = label or f"t7_exe_slot_{len(exe_slots)}"
        exe_slots.append((label, va))
        return label
    gadget_slot = slot(gadget[0], "t7_exe_return_gadget") if gadget else None
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
                asm += [f"\t.globl {q}", f"{q}:", f"\tmovq {slot(slots[u])}(%rip), %rax", "\tjmpq *(%rax)"]
                hybrid.append(f"{u}\timport\t{slots[u]:09X}")
            elif u in ref_table and tls_lo <= ref_table[u][0] < tls_hi:
                tls.append((ref_table[u][0] - tls_lo, q))  # keeps the link valid; not this build's offset
                hybrid.append(f"{u}\tunresolved-tls\t")
            elif u in ref_table and ref_table[u][1] == "data" or u.startswith("t7s@"):
                exe_data.add(u)
                traps.append(f'"{SLOT_PREFIX}{u}"')
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
            asm += function_thunk(q, slot(va), gadget_slot, len(asm), gadget[1] if gadget else 0)
        else:
            exe_data.add(u)
            slot(va, f'"{SLOT_PREFIX}{u}"')
        hybrid.append(f"{u}\t{'function' if is_func else 'data'}\t{va:09X}")
    if tls:
        asm += ['\t.section .tls$, "dw"', "hybrid_tls_start:"]
        for off, q in sorted(tls):
            asm += [f"\t.skip {off} - (. - hybrid_tls_start)", f"\t.globl {q}", f"{q}:"]
        asm += [f"\t.skip {tls_hi - tls_lo} - (. - hybrid_tls_start)"]
    exe_base, exe_size = exe_preferred_base(build)
    asm += hybrid_entry(exe_base)
    asm += ["\t.data", "\t.p2align 3", "\t.globl t7_exe_slots_start", "t7_exe_slots_start:"]
    for label, va in exe_slots:
        asm += [f"\t.globl {label}", f"{label}:", f"\t.quad {va:#x}"]
    asm += ["\t.globl t7_exe_slots_end", "t7_exe_slots_end:"]
    for label in traps:
        asm += [f"\t.globl {label}", f"{label}:", "\t.quad 0"]
    (BUILD / "hybrid.s").write_text("\n".join(asm) + "\n")
    # the units' references to exe data become loads from their slots (the symbols themselves are never defined,
    # so anything left over fails the link instead of reaching a stale address)
    rewritten = 0
    for obj in objs:
        n = exe_relative_asm(obj.with_suffix(".s"), exe_data)
        if n:
            run("clang", TRIPLE, "-c", obj.with_suffix(".s"), "-o", obj)
            rewritten += n
    run("clang", TRIPLE, "-c", BUILD / "hybrid.s", "-o", BUILD / "hybrid.obj")
    (BUILD / "hybrid.tsv").write_text("\n".join(hybrid) + "\n")

    dll = BUILD / "recon.dll"
    # A DLL loaded *inside* the Store EXE must not assume its preferred image base is free: the enhanced image is
    # relocatable (tools/enhanced/build.py checks real PE interval overlap). That is sound only because no code
    # reaches the exe directly: the slot table and t7_hybrid_entry (docs/hybrid-link.md). The faithful
    # differential DLL keeps its fixed layout.
    image_link = ("/base:0x400000000", "/dynamicbase") if enhanced else (
        "/base:0x180000000", "/fixed")
    run("lld-link", "/dll", "/entry:t7_hybrid_entry", "/nodefaultlib", *image_link, f"/out:{dll}",
        *[f"/export:{e}" for e in exports],  # x64: no leading underscore on C names
        *(["/force:multiple", f"/map:{BUILD / 'recon.map'}"] if enhanced else []),
        *objs, *env_objs, BUILD / "hybrid.obj", quiet_duplicates=enhanced)
    check_no_exe_addresses(dll, exe_base, exe_size)
    (BUILD / "recon.symbols.tsv").write_text("symbol\tsource\tva\n" + "\n".join(rows) + "\n")
    unresolved = sum(1 for h in hybrid if "\tunresolved" in h)
    if unresolved and reference:
        print(f"note: {unresolved} symbol(s) not in {build} (trap; build/hybrid.tsv):",
              ", ".join(h.split("\t")[0] for h in hybrid if "\tunresolved" in h))
    print(f"{dll}: {len(exports)} functions from {len(sources)} files; "
          f"{len(undefined) - unresolved} symbols resolved to {build}, {rewritten} data references through "
          f"{len(exe_slots)} rebased slots" +
          (f", {unresolved} not identified there yet (trap)" if unresolved else ""))


if __name__ == "__main__":
    main()
