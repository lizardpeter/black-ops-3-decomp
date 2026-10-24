"""P0007: libHttpClient never begins an HTTP request or a WebSocket connection in the enhanced build.

HttpCallPerformAsync runs on the faithful test's inputs with the allocator, XAsyncBegin, XTaskQueueCloseHandle and the
free hook forbidden: it must return HRESULT_FROM_WIN32(ERROR_NETWORK_UNREACHABLE) and touch nothing. The same for
WebSocketConnectAsync, which must also leave the caller's strings and the shared_ptr's count as they were.
"""
import test_NetworkState as faithful
from test_bdPlatformSocket_offline import forbid


def test_http_call_is_refused(env):
    hooks = {name: forbid for name in (faithful.ALLOC, faithful.FREE, faithful.BEGIN, faithful.CLOSE)}
    for inp in faithful.inputs():
        value, buffers, writes, observed = env.call(faithful.PERFORM, inp["args"], ret="int", fakes=hooks)
        assert value == -0x7FF8FB31 and not writes and not observed, (hex(value), writes, observed)


def test_websocket_connect_is_refused(env):
    hooks = {name: forbid for name in (faithful.ALLOC, faithful.FREE, faithful.BEGIN, faithful.CLOSE)}
    for inp in faithful.connect_inputs():
        value, buffers, writes, observed = env.call(faithful.CONNECT, inp["args"], ret="int", setup=inp["setup"],
                                                    fakes=hooks)
        assert value == -0x7FF8FB31 and not writes and not observed, (hex(value), writes, observed)
        assert buffers == [a for a in inp["args"] if isinstance(a, bytes)]
