"""P0004: Demonware's UDP socket layer never reaches Winsock in the enhanced build.

Each method is called on the same inputs as its faithful differential test, with every ws2_32 import, the log and the
socket statistics forbidden or watched. The result must be the "no network" answer the override documents, with no
Winsock call, no log line, no global written (the statistics stay as they are) and no argument buffer changed.
"""
import test_bdPlatformSocket as faithful

WS2 = ["ws2_32.dll!" + n for n in ("socket", "WSASocketA", "bind", "sendto", "WSASendTo", "WSARecvFrom", "recvfrom",
                                   "getaddrinfo", "gethostbyname", "setsockopt", "ioctlsocket", "closesocket",
                                   "WSAGetLastError", "htons", "ntohs")]


def forbid(mu):
    raise AssertionError("the offline socket layer reached Winsock or the Demonware log")


def handle_of(args):
    h = args[0]
    return int.from_bytes(h, "little", signed=True) if isinstance(h, bytes) else (h - (1 << 64) if h >= 1 << 63 else h)


def check(env, symbol, inputs, expect, ret="int"):
    hooks = {name: forbid for name in WS2 + [faithful.LOG]}
    for inp in inputs:
        value, buffers, writes, observed = env.call(symbol, inp["args"], ret=ret, fakes=hooks)
        assert value == expect(inp["args"]), (symbol, inp["args"][:1], value)
        assert not writes and not observed, (symbol, writes, observed)
        assert buffers == [a for a in inp["args"] if isinstance(a, bytes)], symbol


def test_create_always_fails(env):
    check(env, faithful.CREATE3, faithful.create3_inputs(), lambda a: -1)
    check(env, faithful.CREATE2, faithful.create2_inputs(), lambda a: -1)


def test_bind_send_receive_report_no_network(env):
    by_handle = lambda other: lambda a: -10 if handle_of(a) == -1 else other  # noqa: E731
    check(env, faithful.BIND, faithful.bind_inputs(), by_handle(-1))
    check(env, faithful.SEND, faithful.send_inputs(), by_handle(-1))
    check(env, faithful.RECV, faithful.recv_inputs(), by_handle(-2))


def test_host_lookup_finds_nothing(env):
    check(env, faithful.HOST, faithful.host_inputs(), lambda a: 0)
