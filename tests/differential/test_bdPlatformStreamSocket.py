"""Hand-written cases for libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket-xboxone.cpp.

As for the UDP layer (test_bdPlatformSocket.py): Winsock is the model in winsock.py, every call it gets is compared
with its arguments (the fd_sets select is given and the sockaddr connect is given included), bdLogMessage is faked
and observed whole, and the byte statistics are compared as global writes. Half of each function's failures use an
error code the function maps, the rest any code.

Mutation check: see the commit adding this file.
"""
import random
import struct

from test_bdPlatformSocket import COMMON, ERRORS, FAMILIES, HANDLES, flag, sockaddr, winsock

CHECK = "?checkSocketException@bdPlatformStreamSocket@@SA_NH@Z"
CLOSE = "?close@bdPlatformStreamSocket@@SA_NH@Z"
CONNECT = "?connect@bdPlatformStreamSocket@@SA?AW4bdSocketStatusCode@@HVbdSockAddr@@G@Z"
CREATE2 = "?create@bdPlatformStreamSocket@@SAHI_N@Z"
CREATE1 = "?create@bdPlatformStreamSocket@@SAH_N@Z"
WRITABLE1 = "?isWritable@bdPlatformStreamSocket@@SA_NH@Z"
WRITABLE2 = "?isWritable@bdPlatformStreamSocket@@SA_NHAEAW4bdSocketStatusCode@@@Z"
RECEIVE = "?receive@bdPlatformStreamSocket@@SAHHQEAXI@Z"
SEND = "?send@bdPlatformStreamSocket@@SAHHQEBXI@Z"

MAPPED = [6, 10004, 10022, 10035, 10039, 10040, 10047, 10049, 10050, 10051, 10053, 10054, 10057, 10060, 10061, 10065]
SELECTS = [(0, ""), (1, "w"), (1, "e"), (2, "we"), (-1, "we"), (-1, ""), (0, "we"), (3, "rwe")]


def error(r, i):
    return r.choice(MAPPED) if i % 2 else r.choice(ERRORS)


def select_state(r, i):
    return winsock(select=[r.choice(SELECTS)], errors=[error(r, i), error(r, i)])


def check_inputs():
    r = random.Random(201)
    return [{"args": [r.choice(HANDLES)], "setup": select_state(r, i)} for i in range(80)]


def close_inputs():
    r = random.Random(202)
    return [{"args": [r.choice(HANDLES)], "setup": winsock(close=[r.choice([0, -1, 1, 7])], errors=[error(r, i)])}
            for i in range(80)]


def connect_inputs():
    r = random.Random(203)
    return [{"args": [r.choice(HANDLES), sockaddr(r, r.choice(FAMILIES)), r.randint(0, 0xFFFF)],
             "setup": winsock(connect=[r.choice([0, -1, -1, 2])], errors=[error(r, i)])} for i in range(240)]


def socket_state(r):
    return winsock(sockets=[r.choice([0x1F0, 0x204, (1 << 64) - 1, 0xFFFF_FFFF])], ioctl=[r.choice([0, 0, -1])])


def create2_inputs():
    r = random.Random(204)
    return [{"args": [r.choice(FAMILIES + [2, 23]), flag(r)], "setup": socket_state(r)} for _ in range(160)]


def create1_inputs():
    r = random.Random(205)
    return [{"args": [flag(r)], "setup": socket_state(r)} for _ in range(60)]


def writable1_inputs():
    r = random.Random(206)
    return [{"args": [r.choice(HANDLES)], "setup": select_state(r, i)} for i in range(120)]


def writable2_inputs():
    r = random.Random(207)
    return [{"args": [r.choice(HANDLES), b"\xcc" * 4], "setup": select_state(r, i)} for i in range(240)]


def receive_inputs():
    r = random.Random(208)
    out = []
    for i in range(300):
        size = r.choice([0, 1, 16, 512])
        reply = r.choice([r.randbytes(r.randint(0, 40)), -1, -1, 0, -3])
        out.append({"args": [r.choice(HANDLES + [0x1F0]), b"\xcc" * max(size, 1), size],
                    "setup": winsock(recv=[reply], select=[r.choice(SELECTS)], errors=[error(r, i), error(r, i)])})
    return out


def send_inputs():
    r = random.Random(209)
    out = []
    for i in range(300):
        data = r.randbytes(r.randint(1, 40))
        out.append({"args": [r.choice(HANDLES + [0x1F0]), data, r.choice([len(data), 0, 1])],
                    "setup": winsock(send=[r.choice([None, -1, -1, 0, 2, -7])], select=[r.choice(SELECTS)],
                                     errors=[error(r, i), error(r, i)])})
    return out


CASES = [
    {"symbol": CHECK, "ret": "char", "inputs": check_inputs(), **COMMON},
    {"symbol": CLOSE, "ret": "char", "inputs": close_inputs(), **COMMON},
    {"symbol": CONNECT, "ret": "int", "inputs": connect_inputs(), **COMMON},
    {"symbol": CREATE2, "ret": "int", "inputs": create2_inputs(), **COMMON},
    {"symbol": CREATE1, "ret": "int", "inputs": create1_inputs(), **COMMON},
    {"symbol": WRITABLE1, "ret": "char", "inputs": writable1_inputs(), **COMMON},
    {"symbol": WRITABLE2, "ret": "char", "inputs": writable2_inputs(), **COMMON},
    {"symbol": RECEIVE, "ret": "int", "inputs": receive_inputs(), **COMMON},
    {"symbol": SEND, "ret": "int", "inputs": send_inputs(), **COMMON},
]
