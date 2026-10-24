"""Hand-written cases for universal/q_shared.cpp (string utilities).

The generated cases (auto.py) only use printable ASCII without the characters these functions treat specially,
never pass null pointers and never use sizes near the string length. These cases cover what they miss:

- null pointers for every pointer argument;
- bytes >= 0x80 (signed vs unsigned char comparisons, tolower on high bytes);
- the case-folding boundaries '@' 'A' 'Z' '[' '`' 'a' 'z' '{';
- sizes 0, 1, exactly the string length, one more and one less (truncation and termination);
- '*' and '?' in wildcard patterns, including a trailing '*' and runs of '*';
- '^' colour codes at the end of the string, before non-digits, nested ('^^11'), and control characters.

Destination buffers are filled with 0xCC so a write past the terminator shows up in the compared buffer.

Mutation check: 26 single changes across the eight functions (bounds, constants, comparison directions, signedness,
a dropped case fold, a dropped terminator, a single CleanStr pass) each make these cases fail.
"""
import random

SYM = {
    "strcpy": "?I_strcpy@@YAXPEAD_KPEBD@Z",
    "strnicmp": "?I_strnicmp@@YAHPEBD0_K@Z",
    "strncmp": "?I_strncmp@@YAHPEBD0_K@Z",
    "stristr": "?I_stristr@@YAPEBDPEBD0@Z",
    "stricmp": "?I_stricmp@@YAHPEBD0@Z",
    "stricmpwild": "?I_stricmpwild@@YAHPEBD0@Z",
    "strcat": "?I_strcat@@YAXPEAD_KPEBD@Z",
    "CleanStr": "?I_CleanStr@@YAPEADPEAD@Z",
}

FOLD = b"@AZ[`az{"
HIGH = bytes([0x80, 0x9F, 0xC0, 0xC1, 0xDF, 0xE1, 0xFF])
ALPHA = b"aAbBzZ" + FOLD + b"019" + HIGH


def cs(s: bytes) -> bytes:
    """A C string argument: terminated, with slack so an over-read past the terminator stays in the buffer."""
    return s + b"\0" * 8


def rand_str(r, alphabet, lo=0, hi=12):
    return bytes(r.choice(alphabet) for _ in range(r.randint(lo, hi)))


def case_variant(r, s: bytes) -> bytes:
    """s with random letters flipped between cases (equal under a case-insensitive compare)."""
    return bytes((c ^ 0x20) if (0x41 <= c <= 0x5A or 0x61 <= c <= 0x7A) and r.random() < 0.5 else c for c in s)


def pair(r, alphabet):
    """Two strings that are equal, case-variants, prefixes of each other, or differ at one position."""
    a = rand_str(r, alphabet)
    k = r.randrange(5)
    if k == 0:
        return a, a
    if k == 1:
        return a, case_variant(r, a)
    if k == 2:
        return a, a[: r.randint(0, len(a))]
    if k == 3 and a:
        i = r.randrange(len(a))
        return a, a[:i] + bytes([r.choice(alphabet)]) + a[i + 1:]
    return a, rand_str(r, alphabet)


# --- copy and concatenate ------------------------------------------------------------------------------------

def strcpy_inputs():
    r = random.Random(1)
    ins = [[0, 0, cs(b"abc")], [0, 4, cs(b"abc")], [b"\xcc" * 8, 0, cs(b"abc")], [b"\xcc" * 8, 8, 0],
           [b"\xcc" * 8, 0, 0], [b"\xcc" * 8, 1, 0]]
    for _ in range(200):
        src = rand_str(r, ALPHA, 0, 16)
        n = r.choice([1, 2, len(src), len(src) + 1, max(1, len(src) - 1), r.randint(1, 20)])
        ins.append([b"\xcc" * max(n, 1) + b"\xcc" * 8, n, cs(src)])
    return ins


def strcat_inputs():
    r = random.Random(2)
    ins = [[cs(b"ab") + b"\xcc" * 8, 8, 0], [cs(b"") + b"\xcc" * 8, 1, cs(b"x")]]
    for _ in range(200):
        head = rand_str(r, ALPHA, 0, 10)
        src = rand_str(r, ALPHA, 0, 10)
        # destsize at least strlen(dest): below that the original computes a negative size (records/bugs.tsv)
        n = r.choice([len(head), len(head) + 1, len(head) + len(src), len(head) + len(src) + 1,
                      len(head) + r.randint(0, 20)])
        buf = head + b"\0" + b"\xcc" * (max(n, len(head) + 1) + 8 - len(head) - 1)
        ins.append([buf, n, cs(src)])
    return ins


# --- comparisons ---------------------------------------------------------------------------------------------

def nullable_pairs():
    return [[0, 0], [0, cs(b"a")], [cs(b"a"), 0], [0, cs(b"")], [cs(b""), 0]]


def cmpn_inputs(seed):
    r = random.Random(seed)
    ins = [p + [r.choice([0, 1, 5])] for p in nullable_pairs()]
    for _ in range(250):
        a, b = pair(r, ALPHA)
        n = r.choice([0, 1, len(a), len(b), min(len(a), len(b)), r.randint(0, 16), 0x7FFFFFFF, 2**64 - 1])
        if r.random() < 0.5:
            a, b = b, a
        ins.append([cs(a), cs(b), n])
    return ins


def cmp_inputs(seed):
    r = random.Random(seed)
    ins = list(nullable_pairs())
    for _ in range(250):
        a, b = pair(r, ALPHA)
        ins.append([cs(a), cs(b)] if r.random() < 0.5 else [cs(b), cs(a)])
    return ins


def stristr_inputs():
    r = random.Random(4)
    ins = list(nullable_pairs()) + [[cs(b""), cs(b"")], [cs(b"abc"), cs(b"")], [cs(b""), cs(b"a")]]
    for _ in range(250):
        hay = rand_str(r, b"aAbB" + FOLD + HIGH, 0, 14)
        k = r.randrange(3)
        if k == 0 and hay:
            i = r.randrange(len(hay))
            needle = case_variant(r, hay[i: i + r.randint(1, 5)])
        elif k == 1:
            needle = rand_str(r, b"aAbB" + FOLD + HIGH, 1, 4)
        else:
            needle = case_variant(r, hay) + rand_str(r, b"ab", 0, 2)
        ins.append([cs(hay), cs(needle)])
    return ins


def wild_inputs():
    r = random.Random(5)
    ins = [[cs(b""), cs(b"")], [cs(b"*"), cs(b"")], [cs(b"*"), cs(b"anything")], [cs(b"?"), cs(b"")],
           [cs(b"a*"), cs(b"a")], [cs(b"*a"), cs(b"bba")], [cs(b"**"), cs(b"x")], [cs(b"a?c"), cs(b"ABC")],
           [cs(b"*b*"), cs(b"aBc")], [cs(b"mp_*"), cs(b"MP_NUKETOWN")], [cs(b"zm_*"), cs(b"mp_x")]]
    for _ in range(250):
        s = rand_str(r, b"abAB" + FOLD + HIGH + b"?*", 0, 8)
        k = r.randrange(3)
        if k == 0:  # a pattern made from s: some characters replaced by '?' or '*'
            pat = bytearray(case_variant(r, s))
            for i in range(len(pat)):
                if r.random() < 0.25:
                    pat[i] = r.choice(b"?*")
            pat = bytes(pat)
        elif k == 1:
            pat = rand_str(r, b"ab*?", 0, 6)
        else:
            pat = case_variant(r, s)
        ins.append([cs(pat), cs(s)])
    return ins


# --- colour codes ---------------------------------------------------------------------------------------------

def clean_inputs():
    r = random.Random(6)
    ins = [[cs(b"")], [cs(b"^")], [cs(b"^^")], [cs(b"^1")], [cs(b"a^")], [cs(b"^^11x")], [cs(b"^^^123")],
           [cs(b"^a^:^/")], [cs(b"\x1f\x7f~ ")], [cs(b"^\x80")], [cs(b"plain")]]
    alphabet = b"^^^0159:/aZ ~\x7f\x1f\t\x80\xff"
    for _ in range(250):
        ins.append([cs(rand_str(r, alphabet, 0, 16))])
    return ins


CASES = [
    {"symbol": SYM["strcpy"], "ret": "void", "inputs": strcpy_inputs()},
    {"symbol": SYM["strnicmp"], "ret": "int", "inputs": cmpn_inputs(10)},
    {"symbol": SYM["strncmp"], "ret": "int", "inputs": cmpn_inputs(11)},
    {"symbol": SYM["stristr"], "ret": "int64", "inputs": stristr_inputs()},
    {"symbol": SYM["stricmp"], "ret": "int", "inputs": cmp_inputs(12)},
    {"symbol": SYM["stricmpwild"], "ret": "int", "inputs": wild_inputs()},
    {"symbol": SYM["strcat"], "ret": "void", "inputs": strcat_inputs()},
    {"symbol": SYM["CleanStr"], "ret": "int64", "inputs": clean_inputs()},
]
