#!/usr/bin/env python3
"""Sanitizer regression for enhanced BO3 I_strcat, no original game required."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    with tempfile.TemporaryDirectory() as directory:
        binary = Path(directory) / "strcat_bounds"
        subprocess.run([
            os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
            "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined",
            "-fno-omit-frame-pointer", "-I" + str(ROOT / "include"),
            str(ROOT / "enhanced/universal/q_shared.cpp"),
            str(ROOT / "tests/security/strcat_bounds.cpp"),
            "-o", str(binary),
        ], check=True)
        environment = os.environ.copy()
        environment.setdefault("ASAN_OPTIONS", "detect_leaks=0:halt_on_error=1")
        environment.setdefault("UBSAN_OPTIONS", "halt_on_error=1")
        subprocess.run([str(binary)], check=True, env=environment)
    print("PASS: enhanced I_strcat 22,750 guard cases; wildcard 6,000 oracle fuzz cases and DoS input under ASan/UBSan")


if __name__ == "__main__":
    main()
