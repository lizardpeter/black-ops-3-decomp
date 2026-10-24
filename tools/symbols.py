"""The symbol table of a build: decorated name -> (address, kind), for linking and testing the reconstruction.

- A reference build (MAP + PDB) has its own: MAP publics (kind function/data from the MAP flags) and PDB statics
  (as `t7s@<source>@<scope>@<name>`, see tools/recon/include/t7_static.h).
- Any other build (the Store build, the Steam builds) gets one from identifications:
  1. records/names.tsv: authored identifications for that build (functions and data), each with its method,
     evidence and confidence;
  2. analysis/<build>/match/functions.tsv: the matcher's reference -> target pairs, taking the reference
     function's decorated name from the reference MAP. A reference address that carries several names (identical
     code folding: an empty function folded with another empty function) is skipped, since the target build need
     not have folded the same functions.
  records/names.tsv wins over the matcher when both name the same symbol.
"""
import csv
import tomllib
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
csv.field_size_limit(1 << 30)


def read_tsv(path):
    if not Path(path).exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def config():
    return tomllib.loads((ROOT / "target.toml").read_text())


def reference_build() -> str:
    """The build tests and the default hybrid link use: the first reference build with a MAP, or, for a game with no
    symbol build (BO3), the first retail build."""
    builds = config().get("build", [])
    ref = next((b["id"] for b in builds if b.get("kind") == "reference" and "map" in b), None)
    return ref or next(b["id"] for b in builds if b.get("kind") == "retail")


def base_name(sym: str) -> str:
    """A decorated name's leading identifier (`?I_stricmp@@YAHPEBD0@Z` -> `I_stricmp`); a plain name unchanged."""
    return sym[1:].split("@", 1)[0] if sym.startswith("?") else sym


def resolve(build: str, sym: str):
    """(va, kind) of a symbol in a build, or None. Exact first; in a build without a MAP, whose identifications
    carry plain names only (BO3), a decorated name the reconstruction emits resolves through its plain name when
    exactly one address has that name. The prototype is then the reconstruction's, unchecked against the
    original: there is no original decorated name to check it with."""
    t = table(build)
    if sym in t:
        return t[sym]
    if has_map(build):
        return None
    hits = {v for k, v in t.items() if base_name(k) == base_name(sym)}
    return hits.pop() if len(hits) == 1 else None


def build_spec(build: str) -> dict:
    return next(b for b in config()["build"] if b["id"] == build)


def has_map(build: str) -> bool:
    return (ROOT / "analysis" / build / "map" / "publics.tsv").exists()


@lru_cache(maxsize=None)
def table(build: str) -> dict:
    """{symbol: (va, kind)} with kind 'function' or 'data'."""
    out = {}
    if has_map(build):
        for r in read_tsv(ROOT / "analysis" / build / "map" / "publics.tsv"):
            out.setdefault(r["name"], (int(r["va"], 16), "function" if "f" in r["flags"] else "data"))
        for r in read_tsv(ROOT / "analysis" / build / "pdb" / "statics.tsv"):
            if r["va"]:
                out.setdefault(f"t7s@{r['source']}@{r['scope']}@{r['name']}", (int(r["va"], 16), "data"))
        return out

    matched = read_tsv(ROOT / "analysis" / build / "match" / "functions.tsv")
    for ref in sorted({r["ref_build"] for r in matched}):
        names_at = {}
        for r in read_tsv(ROOT / "analysis" / ref / "map" / "publics.tsv"):
            if "f" in r["flags"]:
                names_at.setdefault(r["va"], []).append(r["name"])
        targets = {}
        for r in matched:
            if r["ref_build"] != ref or len(names_at.get(r["ref_va"], [])) != 1:
                continue
            targets.setdefault(names_at[r["ref_va"]][0], set()).add(int(r["target_va"], 16))
        for name, vas in targets.items():
            if len(vas) == 1:
                out[name] = (vas.pop(), "function")
    for r in read_tsv(ROOT / "records" / "names.tsv"):
        if r["build"] == build:
            # a row without a decorated name (identified by name only) is keyed by its plain name
            out[r["symbol"] or r["name"]] = (int(r["va"], 16), r["kind"])
    return out


def by_plain_name(build: str) -> dict:
    """{plain name: va}: a decorated name's leading identifier, a static's name, or records/names.tsv's name."""
    out = {}
    for sym, (va, _) in table(build).items():
        if sym.startswith("t7s@"):
            out.setdefault(sym.rsplit("@", 1)[1], va)
        elif sym.startswith("?"):
            out.setdefault(sym[1:].split("@", 1)[0], va)
        else:
            out.setdefault(sym, va)
        out.setdefault(sym, va)
    for r in read_tsv(ROOT / "records" / "names.tsv"):
        if r["build"] == build:
            out[r["name"]] = int(r["va"], 16)
    return out
