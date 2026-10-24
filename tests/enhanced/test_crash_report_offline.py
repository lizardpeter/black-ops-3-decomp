"""P0003: the crash reporter's entry (sub_1423B9DE0) never reports, whatever state the reporter is in.

The faithful copy is driven through every path in tests/differential/test_crash_report.py. Here the same states
(signature set, rate limit expired, every dvar on, a sample that would pass) must lead nowhere: false returned,
nothing written, and none of the senders, dvars, clock, random number or string routines called. Any of those
being reached fails the test at once.
"""
import itertools

import test_crash_report as faithful

ENTRY = faithful.SYM
REACHABLE = [faithful.SEND_EVENT, faithful.WRITE_REPORT, faithful.TIME, faithful.RAND, faithful.STRRCHR,
             faithful.STRDUP, faithful.STRNCPY, "?Dvar_GetBool@@YA_NPEBUdvar_t@@@Z",
             "?Dvar_GetFloat@@YAMPEBUdvar_t@@@Z"]


def forbid(mu):
    raise AssertionError("the offline crash reporter reached a sender or one of its inputs")


def test_reporter_never_reports(env):
    states = itertools.product([b"", b"0123456789abcdef0123456789abcdef"], [0, 1_700_000_000],
                               [None, 1], [None, 1], [None, 1.0])
    for signature, last, enable, upload, rate in states:
        for path in (faithful.PATHS[0] + b"\0", 0):
            value, buffers, writes, observed = env.call(
                ENTRY, [path, b"C:\\logs\\console.log\0", b"pc\0"], ret="char",
                setup=faithful.setup(signature, last, enable, upload, rate),
                fakes={name: forbid for name in REACHABLE}, observe={name: "" for name in REACHABLE})
            assert value == 0, value
            assert not writes, writes
            assert not observed, observed
