"""Addresses of the original's globals for hand-written test setups: the reference build's MAP and PDB, or for
another build its identifications (tools/symbols.py). tests/differential/run.py sets BUILD."""
import sys
from functools import lru_cache

from harness import ROOT, reference_build

sys.path.insert(0, str(ROOT / "tools"))
import symbols  # noqa: E402

BUILD = None


@lru_cache(maxsize=None)
def _names(build):
    return symbols.by_plain_name(build)


@lru_cache(maxsize=None)
def _statics(build):
    out = {}
    for sym, (va, _) in symbols.table(build).items():
        if sym.startswith("t7s@"):
            _, source, scope, name = sym.split("@", 3)
            out[(source, scope, name)] = va
    return out


def va(name: str) -> int:
    """A global or function by decorated or plain name (`playerKeys`, `?cmd_args@@3UCmdArgs@@A`)."""
    return _names(BUILD or reference_build())[name]


def static(source: str, name: str, scope: str = "") -> int:
    """A static by original source path, name and enclosing function ("" for file scope)."""
    return _statics(BUILD or reference_build())[(source, scope, name)]
