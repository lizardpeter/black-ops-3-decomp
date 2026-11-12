#!/usr/bin/env python3
"""Validates actual bootstrap command-line parsing using compiled C++ functions."""
import ctypes as C
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOCK = r'''
static char commandLine[10000] = {};
extern "C" char *GetCommandLineA() { return commandLine; }
extern "C" void OutputDebugStringA(const char *) {}
extern "C" void SetMockCommandLine(const char *text)
{
    unsigned int n = 0;
    while (text && text[n] && n < sizeof(commandLine) - 1) { commandLine[n] = text[n]; ++n; }
    commandLine[n] = 0;
}
'''
def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        mock = root / "mock.cpp"
        mock.write_text(MOCK)
        output = root / "bootstrap.so"
        subprocess.run(["g++", "-std=c++17", "-shared", "-fPIC", "-Wall", "-Wextra",
                        "-Werror", str(mock), str(ROOT / "enhanced/direct/startup.cpp"),
                        str(ROOT / "enhanced/direct/profile.cpp"), "-o", str(output)], check=True)
        lib = C.CDLL(str(output))
        lib.SetMockCommandLine.argtypes = [C.c_char_p]
        lib.T7DirectPlayerId.restype = C.c_ulonglong
        lib.T7DirectPlayerName.argtypes = [C.c_int]
        lib.T7DirectPlayerName.restype = C.c_char_p
        for cmd, expected in [
            (b'bo3.exe +direct_player ABCDEF0000000012 "Local One"', True),
            (b'bo3.exe +direct_player 0000000000000000 Player', False),
            (b'bo3.exe +direct_player bad Player', False),
            (b'bo3.exe +direct_player 0000000000000001', False),
            (b'bo3.exe +direct_player 0000000000000001 Player +direct_player 0000000000000002 Other', False),
            (b'bo3.exe "+direct_player 0000000000000001 Player"', False),
            (b'bo3.exe +direct_player 0000000000000001 "unfinished', False),
            (b'bo3.exe +direct_player 0000000000000001 "bad;command"', False),
            (b'bo3.exe +direct_player 0000000000000001 Player ' + b'x' * 8200, False),
        ]:
            lib.SetMockCommandLine(cmd)
            ok = bool(lib.T7DirectLoadStartupProfile())
            assert ok == expected, (cmd[:50], ok, expected)
            assert bool(lib.T7DirectPlayerId(0)) == expected
            if expected: assert lib.T7DirectPlayerName(0) == b"Local One"
    print("PASS: bounded command-line startup profile, duplicate rejection and no stale ID")
if __name__ == "__main__":
    main()
