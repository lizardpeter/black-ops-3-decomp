#!/usr/bin/env python3
"""Regression: same-peer re-selection must never bypass authenticated UDP replay defense.

Uses the actual enhanced transport and its keyed SipHash implementation over
real localhost UDP, without engine assets or vendor services.
"""
import ctypes as C
import socket
import subprocess
import tempfile
from pathlib import Path

from transport import load, receive

ROOT = Path(__file__).resolve().parents[2]
PROGRAM = r"""
#include "wire_auth.h"
extern "C" unsigned long long ProbeTag(const unsigned char *key,
    const unsigned char *packet, unsigned length, unsigned char role)
{
    return T7WireAuth::MacDirectional(key, packet, length, role);
}
"""


def main():
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        runtime = folder / "transport.so"
        libmac = folder / "mac.so"
        subprocess.run([
            "g++", "-std=c++17", "-O1", "-Wall", "-Wextra", "-Werror",
            "-shared", "-fPIC", "-pthread", "-I" + str(ROOT / "include"),
            str(ROOT / "enhanced/direct/transport.cpp"), "-o", str(runtime)
        ], check=True)
        source = folder / "mac.cpp"
        source.write_text(PROGRAM)
        subprocess.run([
            "g++", "-std=c++17", "-O1", "-Wall", "-Wextra", "-Werror",
            "-shared", "-fPIC", "-I" + str(ROOT / "enhanced/direct"),
            str(source), "-o", str(libmac)
        ], check=True)
        client = load(runtime)
        tag = C.CDLL(str(libmac)).ProbeTag
        tag.argtypes = [C.c_void_p, C.c_void_p, C.c_uint, C.c_ubyte]
        tag.restype = C.c_ulonglong
        key = bytes(range(16))
        keydata = C.create_string_buffer(key)
        assert client.SetKey(key.hex().encode())
        assert client.WireVersion() == 3
        assert client.Open(b"127.0.0.1:0", 0)
        port = client.Port()
        assert port

        def signed_packet(seq, payload=b"guarded"):
            head = (b"T7DP" + bytes((3, 0)) + len(payload).to_bytes(2, "big")
                    + seq.to_bytes(8, "big") + payload)
            buf = C.create_string_buffer(head)
            mac = tag(keydata, buf, len(head), ord("S"))
            return head + mac.to_bytes(8, "big")

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
            sender.bind(("127.0.0.1", 0))
            endpoint = ("127.0.0.1:%d" % sender.getsockname()[1]).encode()
            assert client.SelectPeer(endpoint)
            wire = signed_packet(1)
            destination = ("127.0.0.1", port)

            sender.sendto(wire, destination)
            assert receive(client)[:2] == (1, b"guarded")
            sender.sendto(wire, destination)
            assert not receive(client)[0]

            # A local UI/command may select the same host again; this must
            # not reset the replay state for an already admitted source.
            assert client.SelectPeer(endpoint)
            sender.sendto(wire, destination)
            assert not receive(client)[0], "reselect accepted replayed packet"

            # An invalid intermediate selection revokes the destination,
            # but must not erase its replay history for a later reselect.
            assert not client.SelectPeer(b"invalid")
            assert client.SelectPeer(endpoint)
            sender.sendto(wire, destination)
            assert not receive(client)[0], "invalid-then-reselect accepted replay"

            sender.sendto(signed_packet(2), destination)
            assert receive(client)[:2] == (1, b"guarded")

        # A genuinely distinct endpoint still gets its own initial window.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender2:
            sender2.bind(("127.0.0.1", 0))
            endpoint2 = ("127.0.0.1:%d" % sender2.getsockname()[1]).encode()
            assert client.SelectPeer(endpoint2)
            sender2.sendto(signed_packet(1, b"new-peer"), ("127.0.0.1", port))
            assert receive(client)[:2] == (1, b"new-peer")
        client.Close()
    print("PASS: keyed v3 replay survives same-peer and invalid re-selection; new peer works")


if __name__ == "__main__":
    main()
