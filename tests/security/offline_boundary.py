#!/usr/bin/env python3
"""Security policy regression tests for the offline BO3 PE import rewriting.

These tests do not require the original game. The integration package builder
still verifies each exact pinned EXE hash before applying any redirects.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "offline"))
from package import adapter  # noqa: E402

def test_network_denial():
    socket_ops = (
        "socket", "WSASocketA", "WSASocketW", "connect", "WSAConnect",
        "send", "sendto", "WSASend", "WSASendTo",
        "recv", "recvfrom", "WSARecv", "WSARecvFrom",
        "accept", "WSAAccept", "bind", "listen", "select", "WSAPoll",
        "ioctlsocket", "WSAIoctl", "shutdown", "setsockopt",
    )
    for name in socket_ops:
        assert adapter("ws2_32.dll", name) == "T7DenySocket", name
    for name in ("gethostbyname", "gethostbyaddr"):
        assert adapter("ws2_32.dll", name) == "T7DenyDns", name
    assert adapter("ws2_32.dll", "getaddrinfo") == "T7DenyAddrInfo"
    assert adapter("ws2_32.dll", "getnameinfo") == "T7DenyNameInfo"
    # The safe control APIs must retain their real semantics for startup/cleanup.
    for name in ("WSAStartup", "WSACleanup", "WSAGetLastError", "closesocket"):
        assert adapter("ws2_32.dll", name) is None, name

def test_dynamic_loading():
    for name in ("LoadLibraryA", "LoadLibraryW", "LoadLibraryExA",
                 "LoadLibraryExW", "GetProcAddress"):
        assert adapter("kernel32.dll", name) == "T7Offline" + name, name
    for name in ("CreateProcessA", "CreateProcessW", "LoadPackagedLibrary"):
        assert adapter("kernel32.dll", name) == "T7DenyNull", name
    assert adapter("shell32.dll", "ShellExecuteA") == "T7DenyStatus"
    assert adapter("api-ms-win-crt-process-l1-1-0.dll", "system") == "T7DenyMinusOne"
    assert adapter("ole32.dll", "CoCreateInstance") == "T7DenyCom"

def test_export_definitions():
    source = (ROOT / "enhanced/offline/egress.cpp").read_text()
    for name in ("T7DenySocket", "T7DenyDns", "T7DenyNameInfo",
                 "T7DenyAddrInfo", "T7OfflineGetProcAddress"):
        assert "T7_EXPORT " in source and name + "(" in source, name
    for name in ("LdrLoadDll", "LdrGetProcedureAddress", "LoadPackagedLibrary"):
        assert '"' + name + '"' in source

if __name__ == "__main__":
    test_network_denial()
    test_dynamic_loading()
    test_export_definitions()
    print("PASS: offline socket, DNS, process, loader and export boundaries")
