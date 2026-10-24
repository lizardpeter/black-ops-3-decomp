"""P0005: Demonware's TCP socket layer never reaches Winsock in the enhanced build.

Each overridden method runs on the same inputs as its faithful differential test, with every ws2_32 import and the
log forbidden. The result must be the "no connection" answer the override documents, with no Winsock call, no log
line, no global written (the byte statistics stay as they are), and no argument buffer changed except isWritable's
status, which must read BD_NET_NOT_CONNECTED (-11).
"""
import struct

import test_bdPlatformStreamSocket as faithful
from test_bdPlatformSocket_offline import WS2, forbid, handle_of

WS2_ALL = WS2 + ["ws2_32.dll!" + n for n in ("connect", "send", "recv", "select", "__WSAFDIsSet")]


def check(env, symbol, inputs, expect, ret="int", buffers=None):
    hooks = {name: forbid for name in WS2_ALL + ["?bdLogMessage@@YAXW4bdLogMessageType@@QEBD111I1ZZ"]}
    for inp in inputs:
        value, bufs, writes, observed = env.call(symbol, inp["args"], ret=ret, fakes=hooks)
        assert value == expect(inp["args"]), (symbol, inp["args"][:1], value)
        assert not writes and not observed, (symbol, writes, observed)
        want = [a for a in inp["args"] if isinstance(a, bytes)] if buffers is None else buffers
        assert bufs == want, (symbol, bufs)


def test_no_socket_no_connection(env):
    check(env, faithful.CREATE2, faithful.create2_inputs(), lambda a: -1)
    check(env, faithful.CREATE1, faithful.create1_inputs(), lambda a: -1)
    check(env, faithful.CONNECT, faithful.connect_inputs(), lambda a: -1)
    check(env, faithful.CHECK, faithful.check_inputs(), lambda a: 1, ret="char")
    check(env, faithful.WRITABLE1, faithful.writable1_inputs(), lambda a: 0, ret="char")
    check(env, faithful.WRITABLE2, faithful.writable2_inputs(), lambda a: 0, ret="char",
          buffers=[struct.pack("<i", -11)])


def test_send_receive_report_no_connection(env):
    by_handle = lambda a: -10 if handle_of(a) == -1 else -11  # noqa: E731
    check(env, faithful.RECEIVE, faithful.receive_inputs(), by_handle)
    check(env, faithful.SEND, faithful.send_inputs(), by_handle)
