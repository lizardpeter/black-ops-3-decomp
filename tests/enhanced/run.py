#!/usr/bin/env python3
"""Tests of the enhanced build (enhanced/), in the same emulator as the differential tests.

The enhanced build changes behaviour on purpose, so it isn't compared with the original: each test states what
the enhanced function must do and checks it. The retail exe and build/<build>/enhanced/recon.dll are mapped
together as in tests/differential, so enhanced code still runs on the original's data and engine.

    python3 tools/build_recon.py --build BlackOps3_MSStore --enhanced
    python3 tests/enhanced/run.py [-k name]

Each tests/enhanced/test_*.py defines functions test_<name>(env); env.call(symbol, args, ...) runs an export of
the enhanced DLL (or an original function by name) and returns the harness's (value, buffers, globals written,
observed calls). Fakes and observations take symbols, plain names, or imports ("dll!function").
Ported from ghosts-decomp.
"""
import importlib.util
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "differential"))
sys.path.insert(0, str(HERE.parents[1] / "tools"))
sys.path.insert(0, str(HERE.parent / "differential"))  # test modules reuse the differential cases

from harness import ROOT, Image, Machine, original_exe  # noqa: E402
import symbols  # noqa: E402
import syms  # noqa: E402

BUILD = "BlackOps3_MSStore"


class Env:
    def __init__(self):
        out = ROOT / "build" if BUILD == symbols.reference_build() else ROOT / "build" / BUILD
        self.dll = Image(out / "enhanced" / "recon.dll")
        self.machine = Machine(Image(original_exe(BUILD)), self.dll)
        syms.BUILD = BUILD

    def original(self, symbol):
        """An original function or global: by symbol, else by plain name (a build without decorated names)."""
        hit = symbols.resolve(BUILD, symbol)
        return hit[0] if hit else None

    def at(self, symbol):
        """Every address a hook on `symbol` needs: the enhanced DLL's copy, the original's, or an import stub."""
        if isinstance(symbol, int):
            return [symbol]
        if "!" in symbol:
            return [self.machine.import_stub(symbol)]
        return [va for va in (self.dll.exports.get(symbol), self.original(symbol)) if va]

    def call(self, symbol, args, ret="void", setup=None, fakes=None, observe=None, ret_site=None, at=None,
             original=False):
        """original=True runs the original function even when the enhanced DLL defines one of that name."""
        hooks = {va: fn for s, fn in (fakes or {}).items() for va in self.at(s)}
        obs = {va: spec for s, spec in (observe or {}).items() for va in self.at(s)}
        mid = {va: fn for s, fn in (at or {}).items() for va in self.at(s)}
        target = self.original(symbol) if original else self.dll.exports.get(symbol) or self.original(symbol)
        return self.machine.call(target, args, ret, setup, hooks, obs, ret_site, mid)


def main():
    only = sys.argv[sys.argv.index("-k") + 1] if "-k" in sys.argv else None
    env = Env()
    passed = failed = 0
    for path in sorted(HERE.glob("test_*.py")):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name in sorted(n for n in dir(mod) if n.startswith("test_")):
            if only and only not in name:
                continue
            try:
                getattr(mod, name)(env)
                print(f"ok   {path.stem}.{name}")
                passed += 1
            except Exception:
                print(f"FAIL {path.stem}.{name}")
                traceback.print_exc(limit=3)
                failed += 1
    print(f"{passed}/{passed + failed} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
