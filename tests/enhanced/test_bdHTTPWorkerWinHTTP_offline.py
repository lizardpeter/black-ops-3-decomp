"""P0006: Demonware's HTTP worker never opens a WinHTTP session in the enhanced build.

initializeWinHTTP runs on the faithful test's inputs (initialized or not, network ready or not, every WinHTTP result)
with WinHTTP, GetLastError, the GDK feature query and the log forbidden: it must return false and change nothing.
"""
import test_bdHTTPWorkerWinHTTP as faithful
from test_bdPlatformSocket_offline import forbid

FORBIDDEN = [faithful.FEATURE, faithful.OPEN, faithful.OPTION, faithful.CALLBACK, faithful.CLOSE, faithful.LAST_ERROR,
             "?bdLogMessage@@YAXW4bdLogMessageType@@QEBD111I1ZZ"]


def test_worker_never_opens_a_session(env):
    for inp in faithful.inputs():
        value, buffers, writes, observed = env.call(faithful.INIT, inp["args"], ret="char", setup=inp["setup"],
                                                    fakes={name: forbid for name in FORBIDDEN})
        assert value == 0 and not writes and not observed, (value, writes, observed)
        assert buffers == inp["args"]
