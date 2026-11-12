#!/usr/bin/env python3
"""Compile the exact enhanced keyed-MAC and replay code against published vectors."""
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROGRAM = r"""
#include "wire_auth.h"
#include <assert.h>
int main() {
    unsigned char key[16];
    unsigned char message[64];
    for (unsigned i = 0; i < 16; ++i) key[i] = (unsigned char)i;
    for (unsigned i = 0; i < 64; ++i) message[i] = (unsigned char)i;
    const unsigned long long reference[] = {
        0x726fdb47dd0e0e31ULL, 0x74f839c593dc67fdULL,
        0x0d6c8009d9a94f5aULL, 0x85676696d7fb7e2dULL,
    };
    for (unsigned i = 0; i < 4; ++i)
        assert(T7WireAuth::Mac(key, message, i) == reference[i]);
    unsigned char tag[8] = {0x72,0x6f,0xdb,0x47,0xdd,0x0e,0x0e,0x31};
    assert(T7WireAuth::EqualTag(reference[0], tag));
    tag[7] ^= 1;
    assert(!T7WireAuth::EqualTag(reference[0], tag));
    unsigned char parsed[16] = {};
    assert(T7WireAuth::ParseHexKey("000102030405060708090a0b0c0d0e0f", parsed));
    for (unsigned i = 0; i < 16; ++i) assert(parsed[i] == key[i]);
    assert(!T7WireAuth::ParseHexKey("", parsed));
    assert(!T7WireAuth::ParseHexKey("00000000000000000000000000000000", parsed));
    assert(!T7WireAuth::ParseHexKey("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz", parsed));
    T7WireAuth::ReplayWindow state = {};
    assert(!T7WireAuth::Accept(state, 0));
    assert(T7WireAuth::Accept(state, 1));
    assert(!T7WireAuth::Accept(state, 1));
    assert(T7WireAuth::Accept(state, 3));
    assert(T7WireAuth::Accept(state, 2));
    assert(!T7WireAuth::Accept(state, 2));
    assert(T7WireAuth::Accept(state, 100));
    assert(!T7WireAuth::Accept(state, 1));
    return 0;
}
"""

def main():
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        (folder / "vectors.cpp").write_text(PROGRAM)
        subprocess.run([
            "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
            "-I" + str(ROOT / "enhanced" / "direct"),
            str(folder / "vectors.cpp"), "-o", str(folder / "vectors"),
        ], check=True)
        subprocess.run([str(folder / "vectors")], check=True)
    print("PASS: SipHash-2-4 reference vectors, constant-time tag check, key parser and replay window")

if __name__ == "__main__":
    main()
