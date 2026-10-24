"""Hand-written cases for libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket-xboxone.cpp.

Every Winsock call is answered by the model in winsock.py and logged with its arguments, so the original and the
reconstruction must make the same calls (the sockaddr they build included) and react the same way to every result
and WSAGetLastError code each function distinguishes. bdLogMessage is faked for both and observed with all its
arguments (type, channel, category, file, function, line, format, the value logged: its low 32 bits, since an int vararg leaves the upper half of its stack slot
undefined), so every log line is compared.
The socket statistics are globals and are compared as writes.

The inputs cover, per function: a closed handle (-1); AF_INET, AF_INET6 and other families; each error code the
function maps and some it does not; success with partial and odd byte counts; and bool arguments whose upper bits
are set (only the low byte counts).

Mutation check: see the commit adding this file.
"""
import random
import struct

from winsock import Winsock

LOG = "?bdLogMessage@@YAXW4bdLogMessageType@@QEBD111I1ZZ"
BIND = "?bind@bdPlatformSocket@@SA?AW4bdSocketStatusCode@@AEAHVbdSockAddr@@G@Z"
CLOSE = "?close@bdPlatformSocket@@SA_NAEAH@Z"
CREATE3 = "?create@bdPlatformSocket@@SAHI_N0@Z"
CREATE2 = "?create@bdPlatformSocket@@SAH_N0@Z"
HOST = "?getHostByName@bdPlatformSocket@@SAIQEBDPEAVbdSockAddr@@IH@Z"
RECV = "?receiveFrom@bdPlatformSocket@@SAHHAEAVbdSockAddr@@AEAGPEAXI@Z"
SEND = "?sendTo@bdPlatformSocket@@SAHHVbdSockAddr@@GPEBXI@Z"

# every WinSock error the functions distinguish, plus neighbours they do not
ERRORS = [6, 7, 10004, 10013, 10014, 10015, 10022, 10035, 10039, 10040, 10047, 10048, 10049, 10050, 10051, 10052,
          10053, 10054, 10055, 10060, 10065, 10066, 10101, 11001, 0, -1]
FAMILIES = [2, 23, 0, 1, 0x217, 0xFFFF]
HANDLES = [-1, 0x1F0, 0, 0x7FFFFFFF, -2]

COMMON = {"fakes": {LOG: lambda mu: None}, "observe": {LOG: "issssisi"}}


def sockaddr(r, family):
    return r.randbytes(0x80) + struct.pack("<H", family) + r.randbytes(2)


def u32(v):
    return v & 0xFFFFFFFF


def winsock(**kw):
    """A setup that installs a fresh copy of this Winsock state for each of the two runs."""
    state = Winsock(**kw)

    def setup(w):
        state.copy().install(w.m)
    return setup


BIND_ERRORS = [6, 10013, 10014, 10048, 10049]


def bind_inputs():
    r = random.Random(101)
    out = []
    for i in range(360):
        handle = r.choice(HANDLES[1:]) if i % 4 else -1
        family = r.choice([2, 23]) if i % 3 else r.choice(FAMILIES)
        error = r.choice(BIND_ERRORS) if i % 2 else r.choice(ERRORS)
        out.append({"args": [struct.pack("<i", handle), sockaddr(r, family), r.randint(0, 0xFFFF)],
                    "setup": winsock(bind=[r.choice([0, -1, -1, 5])], errors=[error])})
    return out


def close_inputs():
    r = random.Random(102)
    return [{"args": [struct.pack("<i", r.choice(HANDLES))], "setup": winsock(close=[r.choice([0, -1, 1])])}
            for _ in range(60)]


def flag(r):
    return r.choice([0, 1, 0x100, 0x101, 0xFF00, 0xFFFF_FF01])


def socket_state(r):
    return winsock(sockets=[r.choice([0x1F0, 0x204, (1 << 64) - 1, 0xFFFF_FFFF])],
                   setsockopt=[r.choice([0, 0, -1, 1])], ioctl=[r.choice([0, 0, -1])],
                   errors=[r.choice(ERRORS), r.choice(ERRORS)])


def create3_inputs():
    r = random.Random(103)
    return [{"args": [r.choice(FAMILIES + [2, 23, 2, 23]), flag(r), flag(r)], "setup": socket_state(r)}
            for _ in range(260)]


def create2_inputs():
    r = random.Random(104)
    return [{"args": [flag(r), flag(r)], "setup": socket_state(r)} for _ in range(120)]


def host_inputs():
    r = random.Random(105)
    names = [b"ops3-pc-qbl.prod.demonware.net", b"10.0.0.1", b"localhost", b"", b"9host", b"\xc1bc"]
    out = []
    for _ in range(220):
        name = r.choice(names)
        k = r.randrange(4)
        if k == 0:
            entry = r.choice([11001, 11002, 10050, -1])
        elif k == 1:
            entry = []
        else:
            entry = [(r.choice([16, 16, 8, 4, 0]), struct.pack("<HH", 2, r.randint(0, 0xFFFF)) + r.randbytes(12))
                     for _ in range(r.randint(1, 5))]
        maximum = r.choice([0, 1, 2, 4, 8])
        addrs = b"\xcc" * (0x84 * 8)
        out.append({"args": [name + b"\0", addrs, maximum, r.choice(HANDLES)],
                    "setup": winsock(addrinfo={name: entry}, errors=[r.choice(ERRORS)])})
    return out


RESETS = [10050, 10051, 10053, 10054, 10060, 10065]


def recv_inputs():
    r = random.Random(106)
    out = []
    for i in range(480):
        size = r.choice([0, 1, 16, 64, 1400])
        v4 = struct.pack("<HH", 2, r.randint(0, 0xFFFF)) + r.randbytes(12)
        v6 = struct.pack("<HH", 23, r.randint(0, 0xFFFF)) + r.randbytes(24)
        k = r.randrange(5)
        if k == 0:
            item = -1
        elif k == 1:
            item = (-1, r.choice([v4, v6]))  # a failure reporting the sender
        elif k == 2:
            item = (r.randbytes(r.randint(0, 80)), v4)
        elif k == 3:
            item = (r.randbytes(r.randint(0, 80)), v6)
        else:
            item = (r.randbytes(8), struct.pack("<HH", r.choice([0, 1, 17]), 5) + r.randbytes(12))
        # half the failures get a reset code, so each one meets both families
        error = r.choice(RESETS) if i % 2 else r.choice(ERRORS)
        family = r.choice([2, 23]) if i % 3 else r.choice(FAMILIES)
        out.append({"args": [r.choice(HANDLES + [0x1F0, 0x1F0]), sockaddr(r, family), b"\xcc\xcc",
                             b"\xcc" * max(size, 1), size],
                    "setup": winsock(wsarecvfrom=[item], errors=[error])})
    return out


def send_inputs():
    r = random.Random(107)
    out = []
    for i in range(420):
        data = r.randbytes(r.randint(1, 64))
        length = r.choice([len(data), 0, 1])
        out.append({"args": [r.choice(HANDLES + [0x1F0, 0x1F0]), sockaddr(r, r.choice(FAMILIES)),
                             r.randint(0, 0xFFFF), data, length],
                    "setup": winsock(sendto=[r.choice([None, -1, -1, 0, 3, -5, 0x7FFFFFF0])],
                                     wsasendto=[r.choice([None, (-1, 0), (-1, 7), (0, 3), (5, 2)])],
                                     errors=[r.choice(RESETS) if i % 3 == 0 else r.choice(ERRORS)])})
    return out


CASES = [
    {"symbol": BIND, "ret": "int", "inputs": bind_inputs(), **COMMON},
    {"symbol": CLOSE, "ret": "char", "inputs": close_inputs(), **COMMON},
    {"symbol": CREATE3, "ret": "int", "inputs": create3_inputs(), **COMMON},
    {"symbol": CREATE2, "ret": "int", "inputs": create2_inputs(), **COMMON},
    {"symbol": HOST, "ret": "int", "inputs": host_inputs(), **COMMON},
    {"symbol": RECV, "ret": "int", "inputs": recv_inputs(), **COMMON},
    {"symbol": SEND, "ret": "int", "inputs": send_inputs(), **COMMON},
]
