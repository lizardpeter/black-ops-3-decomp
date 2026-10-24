"""bdLogMessage as a fake that records each log line whole, for tests of Demonware code.

The fake stands in for the original's bdLogMessage (1429C3A20) in both runs and appends to the observed calls:
("bdLogMessage", type, channel, category, file, function, line, format, *values), where the values are read from
the varargs as the format consumes them: %d %i %u %x %X %c as 32-bit integers (an int vararg leaves the upper half
of its stack slot undefined), %p and the 64-bit lengths (%I64, %ll) as 64-bit, %s as the string. So a log line is
compared exactly, including what it prints, and a vararg nobody prints (a stale stack slot) is not compared.
"""
import re
import struct

from harness import _MACHINES
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

SYMBOL = "?bdLogMessage@@YAXW4bdLogMessageType@@QEBD111I1ZZ"
SPEC = re.compile(rb"%([-+ #0]*)(\*|\d+)?(?:\.(\*|\d+))?(hh|h|ll|l|I64|I32|I|z)?([diouxXcspn%])")


def _arg(mu, i):
    if i < 4:
        return mu.reg_read((UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)[i])
    return struct.unpack("<Q", bytes(mu.mem_read(mu.reg_read(UC_X86_REG_RSP) + 8 + 8 * i, 8)))[0]


def fake(mu):
    m = _MACHINES[id(mu)]
    s = lambda a: m.read_cstr(a) if a else None  # noqa: E731
    fmt = s(_arg(mu, 6))
    record = ["bdLogMessage", _arg(mu, 0) & 0xFFFFFFFF, s(_arg(mu, 1)), s(_arg(mu, 2)), s(_arg(mu, 3)),
              s(_arg(mu, 4)), _arg(mu, 5) & 0xFFFFFFFF, fmt]
    i = 7
    for flags, width, prec, length, conv in SPEC.findall(fmt or b""):
        if conv == b"%":
            continue
        for star in (width, prec):
            if star == b"*":
                record.append(_arg(mu, i) & 0xFFFFFFFF)
                i += 1
        v = _arg(mu, i)
        i += 1
        if conv == b"s":
            record.append(s(v))
        elif conv == b"p" or length in (b"ll", b"I64", b"z", b"I"):
            record.append(v)
        else:
            record.append(v & 0xFFFFFFFF)
    m.observed.append(tuple(record))
    return None


FAKES = {SYMBOL: fake}
