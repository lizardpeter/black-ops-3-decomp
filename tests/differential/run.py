#!/usr/bin/env python3
"""Run the differential tests and check records/functions.tsv against the results.

    python3 tests/differential/run.py [--build <id>] [--check-records] [-k substring]

Without --build, tests run against the reference build (MAP + PDB) with build/recon.dll; with --build, against
that build (the Store build) with build/<id>/recon.dll, addresses from tools/symbols.py. A hand-written case
applies to every build that has the function unless it says "build": "<id>".

Every function the reconstruction exports is tested. Hand-written CASES in test_*.py are used when a
function has them; otherwise inputs are generated from the original prototype (auto.py).

For each input, the original and the reconstruction are called on identical arguments. Results must
match exactly: return value (floats bit-exact, NaN == NaN), every pointer buffer, and every byte the
call wrote into the original image's globals. Inputs on which the ORIGINAL itself crashes are skipped;
a function with too few usable inputs is reported as untestable, not passed.

Writes build/test-results.tsv. With --check-records, fails if records/ claims `matches` (or better)
for a function without a passing test.
"""
import csv
import importlib.util
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from auto import auto_case  # noqa: E402
import syms  # noqa: E402
from harness import ROOT, Image, Machine, original_exe, reference_build  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
import symbols  # noqa: E402

BUILD = sys.argv[sys.argv.index("--build") + 1] if "--build" in sys.argv else reference_build()
OUT = ROOT / "build" if BUILD == reference_build() else ROOT / "build" / BUILD
MATCHED = {"matches", "integrated"}
MIN_USABLE = 20
csv.field_size_limit(1 << 30)


def same(a, b):
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
        return struct.pack("<d", a) == struct.pack("<d", b)
    return a == b


def canonical_code(v, m, recon, recon_to_orig):
    """An address in the reconstruction's code as the original address it stands for: one of its functions ->
    the original function, a hybrid-link thunk (`jmp [rip+0]; .quad target`) -> its target."""
    if not recon.base <= v < recon.base + recon.size:
        return v
    if v in recon_to_orig:
        return recon_to_orig[v]
    code = bytes(m.mu.mem_read(v, 14))
    if code[:6] == b"\xff\x25\x00\x00\x00\x00":
        return struct.unpack("<Q", code[6:14])[0]
    return v


def normalize_writes(writes, m, recon, recon_to_orig):
    """Make global writes comparable across the two images. A pointer the reconstruction stores to one of its
    own functions is replaced by the original function's address, and a pointer into either image's .rdata
    (a string literal) by the string it points to: literals have different addresses in the two builds."""
    out = dict(writes)
    for a in sorted(writes):
        if a % 8 or any(a + i not in out for i in range(8)) or not isinstance(out[a], bytes):
            continue
        v = struct.unpack("<Q", b"".join(out[a + i] for i in range(8)))[0]
        if recon.base <= v < recon.base + recon.size and canonical_code(v, m, recon, recon_to_orig) != v:
            v = canonical_code(v, m, recon, recon_to_orig)
            for i, byte in enumerate(struct.pack("<Q", v)):
                out[a + i] = bytes([byte])
        elif any(lo <= v < hi for img in m.images for lo, hi in img.rdata):
            for i in range(1, 8):
                del out[a + i]
            out[a] = ("str", m.read_cstr(v))
    return out


def first_call_difference(want, got):
    for i, (a, b) in enumerate(zip(want, got)):
        if a != b:
            return f"\n       call {i}: original {fmt_call(a)} recon {fmt_call(b)}"
    return f"\n       {len(want)} calls in the original, {len(got)} in the reconstruction"


def fmt_call(c):
    return "(" + ", ".join(f"{x:#x}" if isinstance(x, int) and x > 0xFFFF else repr(x) for x in c) + ")"


def export_name(symbol):
    # x64: no leading underscore on extern "C" names, so MAP and export names agree
    return symbol


def read_tsv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def main():
    only = sys.argv[sys.argv.index("-k") + 1] if "-k" in sys.argv else None
    mapsyms = {name: va for name, (va, kind) in symbols.table(BUILD).items()}
    # a build without decorated names (BO3) resolves the reconstruction's decorated names by plain name; the
    # build wrote the address it resolved to
    for r in read_tsv(OUT / "recon.symbols.tsv"):
        if r["symbol"] not in mapsyms and r.get("va"):
            mapsyms[r["symbol"]] = int(r["va"], 16)
    recon = Image(OUT / "recon.dll")
    m = Machine(Image(original_exe(BUILD)), recon)

    syms.BUILD = BUILD  # test setups look up this build's globals
    recon_to_orig = {va: mapsyms[name] for name, va in recon.exports.items() if name in mapsyms}

    explicit = {}
    for test in sorted(Path(__file__).parent.glob("test_*.py")):
        spec = importlib.util.spec_from_file_location(test.stem, test)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for case in mod.CASES:
            if case.get("build", BUILD) == BUILD:
                explicit[case["symbol"]] = case

    exported = [r["symbol"] for r in read_tsv(OUT / "recon.symbols.tsv")]
    results, failed = [], 0
    for sym in sorted(exported, key=lambda s: mapsyms.get(s, 0)):
        if only and only not in sym:
            continue
        va = mapsyms[sym]
        case = explicit.get(sym)
        how = "explicit"
        if case is None:
            case, note = auto_case(sym, va)
            how = "auto"
            if case is None:
                results.append([BUILD, f"{va:09X}", sym, 0, f"untestable: {note}"])
                failed += 1
                print(f"UNTESTABLE {va:09X} {sym}: {note}")
                continue
        target = recon.exports.get(export_name(sym))
        if target is None:
            verdict, used = "missing: no export with the original decorated name", 0
        else:
            verdict, used = "pass", 0
            for inp in case["inputs"]:
                args, setup = (inp["args"], inp.get("setup")) if isinstance(inp, dict) else (inp, None)
                # a faked function that is also reconstructed is reached at the reconstruction's own copy when the
                # reconstruction calls it: fake both
                wanted = {**case.get("fakes", {}), **(inp.get("fakes", {}) if isinstance(inp, dict) else {})}
                # a name with "!" is an import ("dll!function"): hooked at its stub, reached by both copies
                at = lambda s: m.import_stub(s) if "!" in s else mapsyms[s] if s in mapsyms else symbols.resolve(BUILD, s)[0]  # noqa: E731
                fakes = {at(s): fn for s, fn in wanted.items()}
                fakes.update({recon.exports[s]: fn for s, fn in wanted.items() if s in recon.exports})
                # an observed function that is also reconstructed is reached at the reconstruction's own copy
                # when the reconstruction calls it: watch both, and report either as the original address
                observe = {at(s): spec for s, spec in case.get("observe", {}).items()}
                observe.update({recon.exports[s]: spec for s, spec in case.get("observe", {}).items()
                                if s in recon.exports})
                want = m.call(va, args, case["ret"], setup, fakes, observe)
                if isinstance(want[0], str) and want[0].startswith("fault"):
                    continue  # the original itself crashes on this input: not a usable case
                got = m.call(target, args, case["ret"], setup, fakes, observe)
                got = (*got[:3], [tuple(canonical_code(x, m, recon, recon_to_orig) if isinstance(x, int) else x
                                        for x in c) for c in got[3]])
                used += 1
                # recon globals live at the original's addresses (hybrid link), so writes compare 1:1
                want_w = normalize_writes(want[2], m, recon, recon_to_orig)
                got_w = normalize_writes(got[2], m, recon, recon_to_orig)
                if not (same(want[0], got[0]) and want[1] == got[1] and want_w == got_w and want[3] == got[3]):
                    verdict = (f"FAIL args={args!r}\n       original={want[0]!r} bufs_equal={want[1] == got[1]} "
                               f"globals_equal={want_w == got_w} calls_equal={want[3] == got[3]}"
                               + ("" if want[3] == got[3] else first_call_difference(want[3], got[3])) + f"\n       recon   ={got[0]!r}")
                    break
            if verdict == "pass" and used < min(MIN_USABLE, len(case["inputs"])):
                verdict = f"untestable: original faults on {len(case['inputs']) - used}/{len(case['inputs'])} inputs"
        failed += verdict != "pass"
        results.append([BUILD, f"{va:09X}", sym, used, verdict])
        tag = "ok  " if verdict == "pass" else ("UNTESTABLE" if verdict.startswith("untestable") else "FAIL")
        print(f"{tag} {va:09X} {sym}  ({used} cases, {how})" + ("" if verdict == "pass" else f"\n     {verdict[:600]}"))

    out = OUT / "test-results.tsv"
    out.write_text("build\tva\tsymbol\tcases\tresult\n" +
                   "".join("\t".join(str(x).replace("\n", " ") for x in r) + "\n" for r in results))
    known = 0
    if "--check-records" in sys.argv:
        passed = {(r[0], r[1]) for r in results if r[4] == "pass"}
        records = {(r["build"], r["va"]): r for r in read_tsv(ROOT / "records" / "functions.tsv")
                   if r["build"] == BUILD}
        for key, r in records.items():
            if r["status"] in MATCHED and key not in passed:
                print(f"FAIL records claim {r['status']} for {key[0]}:{key[1]} without a passing test")
                failed += 1
        # A failure is expected, not fatal, only for a function records/ deliberately keeps below
        # `matches` with a note saying why (e.g. it stores its own code addresses in a global).
        for r in results:
            rec = records.get((r[0], r[1]))
            if r[4] != "pass" and rec and rec["status"] not in MATCHED and rec["note"]:
                print(f"known  {r[1]} {r[2]}: records keep it at {rec['status']}: {rec['note']}")
                failed -= 1
                known += 1
    unclaimed = 0
    if BUILD != reference_build() or not symbols.has_map(BUILD):
        # A build without a MAP exports every function it has a name for, claimed or not. Only functions that
        # records/ claims for this build must pass; for the rest a failure is information (the function may
        # differ in this build, or need inputs and identifications nobody has written yet).
        claimed = {r["va"] for r in read_tsv(ROOT / "records" / "functions.tsv") if r["build"] == BUILD}
        for r in results:
            if r[4] != "pass" and r[1] not in claimed:
                unclaimed += 1
        failed -= unclaimed
    print(f"{len(results) - failed - known - unclaimed}/{len(results)} passed" +
          (f", {known} known failure(s)" if known else "") +
          (f", {unclaimed} failing but not claimed for {BUILD}" if unclaimed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
