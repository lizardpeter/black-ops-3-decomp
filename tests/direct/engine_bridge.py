#!/usr/bin/env python3
"""Native portable smoke test of source-linked enhanced recon GDK dispatch bridge.

A g++ shared object executes the SAME bridge code without original game files,
Xbox services, or network access. This is not proof of in-game execution.
"""
import ctypes as C
import subprocess
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def main():
    with tempfile.TemporaryDirectory() as directory:
        library = Path(directory) / "t7-bridge.so"
        subprocess.run([
            "g++", "-std=c++17", "-shared", "-fPIC",
            "-Wall", "-Wextra", "-Werror", "-D__declspec(x)=",
            str(ROOT / "enhanced/direct/engine_bridge.cpp"), "-o", str(library),
        ], check=True)
        dll = C.CDLL(str(library))
        dll.T7EnhancedReconProbe.restype = C.c_uint
        dll.T7EnhancedObservedGdkCalls.restype = C.c_uint
        dll.T7EnhancedLastGdkArgument.restype = C.c_uint64
        dll.T7EnhancedLastGdkCallerRva.restype = C.c_uint
        dll.T7EnhancedObserveGdkDispatch.argtypes = [C.c_uint64, C.c_uint]
        assert dll.T7EnhancedReconProbe() == 0x54374531
        assert dll.T7EnhancedObservedGdkCalls() == 0
        for idx in range(10):
            dll.T7EnhancedObserveGdkDispatch(0x100000000 + idx, 0x920300 + idx)
        assert dll.T7EnhancedObservedGdkCalls() == 10
        assert dll.T7EnhancedLastGdkArgument() == 0x100000009
        assert dll.T7EnhancedLastGdkCallerRva() == 0x920309
        print("PASS: enhanced recon probe and GDK dispatch callback run in native code")
if __name__ == "__main__":
    main()
