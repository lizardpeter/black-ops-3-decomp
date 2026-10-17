"""Generate differential test inputs from a function's original prototype.

The prototype comes from the original decorated name (demangled with llvm-undname), so no hand-written
test is needed for ordinary functions. Hand-written CASES in test_*.py take precedence when the inputs
need structure (valid matrices, strings, game state).
"""
import random
import re
import struct
import subprocess
import zlib

SPECIAL_F = [0.0, -0.0, 1.0, -1.0, 0.5, -0.5, 2.0, 1e-30, -1e-30, 1e30, -1e30, 360.0, -180.0, 180.0,
             float("inf"), float("-inf"), float("nan")]
SPECIAL_I = [0, 1, -1, 2, 127, 128, -128, 255, 256, 32767, -32768, 65535, 2**31 - 1, -2**31]
INT_TYPES = {"int", "unsigned int", "long", "unsigned long", "short", "unsigned short", "char", "signed char",
             "unsigned char", "bool", "unsigned", "__int64", "unsigned __int64", "long long", "unsigned long long"}


def demangle(symbol: str) -> str | None:
    if not symbol.startswith("?"):
        return None
    out = subprocess.run(["llvm-undname"], input=symbol + "\n", capture_output=True, text=True).stdout
    lines = [l for l in out.splitlines() if l.strip() and l.strip() != symbol]
    return lines[0].strip() if lines else None


def split_params(sig: str):
    """'float __cdecl f(float const *const, int)' -> ('float', ['float const *const', 'int'])."""
    m = re.match(r"^(.*?)\s*__cdecl\s+[^(]+\((.*)\)\s*$", sig)
    if not m:
        return None
    ret, params = m.group(1).strip(), m.group(2).strip()
    out, depth, cur = [], 0, ""
    for ch in params:
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
            continue
        depth += ch in "(<[" and 1 or (ch in ")>]" and -1 or 0)
        cur += ch
    if cur.strip() and cur.strip() != "void":
        out.append(cur.strip())
    return ret, out


def ret_kind(ret: str) -> str:
    r = ret.replace("const", "").strip()
    if r == "void":
        return "void"
    if r == "float":
        return "float"
    if r == "double":
        return "double"
    if "*" in r or "&" in r or r in ("__int64", "unsigned __int64", "long long", "unsigned long long"):
        return "int64"  # x64: pointers and 64-bit integers return in all of RAX
    if r in ("char", "signed char", "unsigned char", "bool"):
        return "char"
    if r in ("short", "unsigned short"):
        return "short"
    return "int"


class Gen:
    def __init__(self, seed):
        self.r = random.Random(seed)

    def f(self):
        r = self.r.random()
        if r < 0.25:
            return self.r.choice(SPECIAL_F)
        if r < 0.6:
            return self.r.uniform(-2.0, 2.0)
        return self.r.uniform(-1e4, 1e4)

    def i(self):
        return self.r.choice(SPECIAL_I) if self.r.random() < 0.3 else self.r.randint(-1000, 1000)

    def floats(self, n):
        return struct.pack(f"<{n}f", *(self.f() for _ in range(n)))

    def arg(self, t: str):
        base = t.replace("const", "").replace("volatile", "").strip()
        if "*" in base or "[" in base or "&" in base:
            if base.startswith("char") and base.count("*") == 1:
                n = self.r.randint(0, 24)
                return bytes(self.r.randint(32, 126) for _ in range(n)) + b"\0" * 8
            return self.floats(64)  # 256 bytes: covers vectors, matrices and small structs
        if base == "float":
            return ("f", self.f())
        if base == "double":
            return ("d", self.f())
        if base in INT_TYPES or base.startswith("enum"):
            return self.i() if not base.startswith("enum") else self.r.randint(0, 8)
        return None  # by-value struct or unknown: not auto-testable


def auto_case(symbol: str, va: int, n: int = 300):
    sig = demangle(symbol)
    parsed = split_params(sig) if sig else None
    if not parsed:
        return None, f"no prototype for {symbol}"
    ret, params = parsed
    g = Gen(zlib.crc32(symbol.encode()))
    inputs = []
    for _ in range(n):
        args = [g.arg(p) for p in params]
        if any(a is None for a in args):
            return None, f"cannot generate inputs for {sig}"
        inputs.append(args)
    return {"symbol": symbol, "va": va, "ret": ret_kind(ret), "inputs": inputs, "auto": True}, sig
