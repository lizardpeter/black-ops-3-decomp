"""Single place that turns analysis/ + records/ into the function table everything else reads.

Status ladder (see AGENTS.md):
    located -> named -> typed -> decompiled -> compiles -> matches -> integrated

The first three come from analysis/ automatically, plus records/names.tsv for identifications made by hand in a build
without symbols (e.g. a stripped retail build). The rest come only from records/functions.tsv.
"""
import csv
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LADDER = ["located", "named", "typed", "decompiled", "compiles", "matches", "integrated"]
csv.field_size_limit(1 << 30)


def read_tsv(path: Path):
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


@dataclass
class Fn:
    build: str
    va: str
    size: int = 0
    name: str = ""          # PDB name (undecorated) when known
    symbol: str = ""        # MAP decorated name when known: the cross-build identity
    source: str = ""        # original source file, e.g. game_mp/pregame.cpp
    line: int = 0
    type: str = ""
    lib: str = ""           # library for CRT / SDK code that has no game source file
    status: str = "located"
    src: str = ""           # authored reconstruction file, once one exists
    note: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def key(self) -> str:
        """Build-independent identity of the function."""
        return self.symbol or (f"{self.source}::{self.name}" if self.source else self.name) or f"{self.build}:{self.va}"

    @property
    def subsystem(self) -> str:
        if self.source and not self.source.startswith("<external>"):
            return self.source.split("/")[0]
        return "_external" if self.source else ("_lib:" + self.lib if self.lib else "_unknown")


def config():
    return tomllib.loads((ROOT / "target.toml").read_text())


def load(build: str) -> dict[str, Fn]:
    a = ROOT / "analysis" / build
    fns: dict[str, Fn] = {}

    def get(va):
        return fns.setdefault(va, Fn(build=build, va=va))

    for r in read_tsv(a / "map" / "publics.tsv"):
        if "f" not in r["flags"]:
            continue
        f = get(r["va"])
        f.symbol = f.symbol or r["name"]
        f.lib = r["lib"]
        f.status = "named"
    for r in read_tsv(a / "pdb" / "functions.tsv"):
        f = get(r["va"])
        f.size = int(r["size"] or 0)
        f.name = r["name"]
        f.source = r["module_source"] or r["line_source"]
        f.line = int(r["line"] or 0)
        f.type = r["type"]
        f.status = "typed" if r["type"] else "named"
    for r in read_tsv(a / "functions.tsv"):  # joined Ghidra table, once the pipeline has run
        f = get(r["va"])
        f.size = f.size or int(r["size"] or 0)
        f.name = f.name or r["pdb_name"] or r["ghidra_name"]
        f.extra["bytes_sha256"] = r["bytes_sha256"]
        f.extra["decompile"] = r["decompile"]
    for r in read_tsv(ROOT / "records" / "names.tsv"):
        if r["build"] != build or r["kind"] != "function" or r["va"] not in fns:
            continue
        f = fns[r["va"]]
        if not r["name"].startswith("sub_"):  # sub_<va>: identified as a function, name unknown
            f.name = r["name"]
            f.symbol = f.symbol or (r["symbol"] if r["symbol"].startswith("?") else "")
            f.source = f.source or r["source"]
            if LADDER.index(f.status) < LADDER.index("named"):
                f.status = "named"
    for r in read_tsv(ROOT / "records" / "functions.tsv"):
        if r["build"] != build or r["va"] not in fns:
            continue
        f = fns[r["va"]]
        if LADDER.index(r["status"]) > LADDER.index(f.status):
            f.status = r["status"]
        f.src, f.note = r.get("src", ""), r.get("note", "")
    return fns


if __name__ == "__main__":
    import sys
    # python3 tools/model.py retail-ids   -> the ids of the kind = "retail" builds, one per line (used by CI)
    if sys.argv[1:] == ["retail-ids"]:
        for b in config().get("build", []):
            if b.get("kind") == "retail":
                print(b["id"])
    else:
        sys.exit("usage: tools/model.py retail-ids")
