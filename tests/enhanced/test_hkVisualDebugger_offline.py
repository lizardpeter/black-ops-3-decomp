"""P0008: the Havok Visual Debugger never opens its server in the enhanced build.

serve() runs on the faithful test's inputs with the socket factory, the socket's listen, the timers, the output stream
and the report forbidden: it must change nothing (m_server stays as it was) and call nothing.
"""
import test_hkVisualDebugger as faithful
from test_bdPlatformSocket_offline import forbid


def test_serve_opens_no_socket(env):
    for inp in faithful.inputs():
        hooks = {name: forbid for name in inp["fakes"]}
        value, buffers, writes, observed = env.call(faithful.SERVE, inp["args"], ret="void", setup=inp["setup"],
                                                    fakes=hooks)
        assert not writes and not observed and buffers == [inp["args"][0]], (writes, observed)
