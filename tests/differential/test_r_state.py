"""Hand-written cases for gfx_d3d/r_state.cpp (the render thread's code matrices).

The source state is a 0x8200-byte buffer passed by pointer and compared after the call. MatrixMultiply44,
MatrixInverse44 and 141DECF80 (the projection) run for real in both: they only read and write the state. Each input
fills the view parms copy (+0x1DF0), the matrix behind group 12 (+0x2080), the code matrices and the eye offset with
random floats (a few zeros and negative zeros), the versions and stamps so that some matrices are current and some
are behind, the view-model mode (+0x22B8: 0, 1, 2, 0x40000000) and the camera-relative mode (+0x8100: 0, 1, 2).

R_DeriveCodeMatrix: every group base (0, 4, 8, 12) and some indexes that are not one. R_GetCodeMatrix: every one of
the 16 code matrices, rows 0-3; the returned row pointer is compared too.

Mutation check: see the commit adding this file.
"""
import random
import struct

DERIVE = "?R_DeriveCodeMatrix@@YAXPEADII@Z"
GET = "?R_GetCodeMatrix@@YAPEBMPEADII@Z"
SIZE = 0x8200


def _float(r):
    roll = r.random()
    if roll < 0.04:
        return 0.0
    if roll < 0.08:
        return -0.0
    return r.uniform(-4.0, 4.0) * (10 ** r.randrange(-2, 3))


def _state(r):
    data = bytearray(SIZE)

    def floats(offset, count):
        for i in range(count):
            struct.pack_into("<f", data, offset + 4 * i, _float(r))

    floats(0x0, 16 * 16)            # code matrices
    floats(0x100 + 0x2C, 1)         # projection's +0x2C (141DECF80's scale)
    floats(0x1DF0, 0x290 // 4)      # view parms
    floats(0x2030, 4)
    floats(0x2064, 1)
    floats(0x2080, 16)              # group 12's matrix
    floats(0x22A0, 4)               # eye offset
    versions = [r.randrange(0, 0x10000) for _ in range(4)]
    for g, v in enumerate(versions):
        struct.pack_into("<H", data, 0x228A + 2 * g, v)
    for u in range(16):
        current = versions[u >> 2]
        stamp = current if r.random() < 0.45 else r.choice([current - 1, current + 1, 0, r.randrange(0, 0x10000)])
        struct.pack_into("<H", data, 0x20C0 + 2 * (0xD5 + u), stamp & 0xFFFF)
    struct.pack_into("<I", data, 0x22B8, r.choice([0, 0, 1, 2, 0x40000000]))
    struct.pack_into("<I", data, 0x8100, r.choice([0, 0, 1, 2]))
    return bytes(data)


def derive_inputs():
    r = random.Random(0x141DED140)
    out = []
    for _ in range(160):
        base = r.choice([0, 4, 8, 12, 0, 4, 8, 12, 1, 3, 13, 16])
        out.append({"args": [_state(r), 0xD5 + r.randrange(0, 16), base]})
    return out


def get_inputs():
    r = random.Random(0x141DED4D0)
    out = []
    for _ in range(240):
        out.append({"args": [_state(r), 0xD5 + r.randrange(0, 16), r.randrange(0, 4)]})
    return out


CASES = [
    {"symbol": DERIVE, "ret": "void", "inputs": derive_inputs()},
    {"symbol": GET, "ret": "int64", "inputs": get_inputs()},
]
