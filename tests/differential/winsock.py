"""A model of Winsock (ws2_32) for differential tests: no call ever reaches a real socket.

Each test input builds a Winsock state and installs it on the machine from its setup. Every ws2_32 import the Store
build has is modelled (an unmodelled one would fall back to the harness's `return 0` stub, which this module
refuses: install() checks that every ws2_32 import of the image has a behaviour). The model holds, per input:

- whether WSAStartup fails, and the WSAGetLastError codes handed out in order;
- the socket handles socket() returns (or INVALID_SOCKET), and the results of ioctlsocket, setsockopt, bind, connect;
- send/sendto results (default: everything sent), recv replies (a scripted SOCKS server: each recv takes the next
  reply, bytes or an error), recvfrom datagrams (data and source sockaddr, or an error);
- gethostname's name and gethostbyname's hosts (address type and address list), built as real hostent structures
  in scratch memory.

Every call is logged with its arguments into the machine's observed calls (the bytes sent, the sockaddr, the lengths),
so the original and the reconstruction must make the same Winsock calls in the same order. Pure helpers (htons,
ntohl, inet_addr) compute real results. memcmp (vcruntime140) is given a real implementation too, since the network
code compares addresses with it; the harness's default stub would always report equality.
"""
import struct
from dataclasses import dataclass, field

from harness import SCRATCH
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

INVALID_SOCKET = (1 << 64) - 1
SOCKET_ERROR = -1
WSAEWOULDBLOCK, WSAECONNREFUSED, WSAECONNRESET, WSAEMSGSIZE = 10035, 10061, 10054, 10040
HOSTENT_AREA = SCRATCH + 0xC0000  # gethostbyname results (scratch is cleared before every call)


def _i32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


def inet_aton(s: bytes):
    """inet_addr's result for a dotted quad, else INADDR_NONE (decimal parts only: the tests use nothing else)."""
    parts = s.split(b".")
    if len(parts) != 4 or not all(p.isdigit() and int(p) < 256 for p in parts):
        return 0xFFFFFFFF
    return struct.unpack("<I", bytes(int(p) for p in parts))[0]


def sockaddr_in(ip: bytes, port: int, zero=bytes(8)) -> bytes:
    """A 16-byte AF_INET sockaddr: port in host order here, stored big-endian."""
    return struct.pack("<H", 2) + struct.pack(">H", port) + ip + zero


@dataclass
class Winsock:
    startup: int = 0                                  # WSAStartup's result
    errors: list = field(default_factory=list)        # WSAGetLastError results, in order
    last_error: int = WSAEWOULDBLOCK                  # once errors is used up
    sockets: list = field(default_factory=list)       # socket() results in order (a handle or INVALID_SOCKET)
    next_socket: int = 0x1F0                          # handles once sockets is used up
    ioctl: list = field(default_factory=list)         # ioctlsocket results (0 or SOCKET_ERROR); then 0
    setsockopt: list = field(default_factory=list)
    bind: list = field(default_factory=list)
    connect: list = field(default_factory=list)
    send: list = field(default_factory=list)          # send results (None: all bytes); then all bytes
    sendto: list = field(default_factory=list)
    recv: list = field(default_factory=list)          # replies: bytes, or an int result; then SOCKET_ERROR
    recvfrom: list = field(default_factory=list)      # (data, 16-byte sockaddr) or an int result; then SOCKET_ERROR
    hostname: bytes = b"gamepc"                       # gethostname's name, None: SOCKET_ERROR
    hosts: dict = field(default_factory=dict)         # name -> (h_addrtype, [4-byte addresses])

    def copy(self):
        return Winsock(**{k: (list(v) if isinstance(v, list) else dict(v) if isinstance(v, dict) else v)
                          for k, v in vars(self).items()})

    def install(self, m):
        s = self
        heap = [HOSTENT_AREA]

        def log(name, *args):
            m.observed.append(("import", name, *args))

        def ret(mu, v):
            mu.reg_write(UC_X86_REG_RAX, v & 0xFFFFFFFFFFFFFFFF)

        def arg(mu, i):
            if i < 4:
                return mu.reg_read((UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)[i])
            # the stub runs at its `ret`: [rsp] is the return address, then 32 bytes of shadow space
            return struct.unpack("<Q", bytes(mu.mem_read(mu.reg_read(UC_X86_REG_RSP) + 8 + 8 * i, 8)))[0]

        def read(mu, a, n):
            return bytes(mu.mem_read(a, n)) if n > 0 else b""

        def write(a, data):
            m._emulated_write(a, data)  # journaled when it lands in an image, like an instruction's write

        def take(lst, default):
            return lst.pop(0) if lst else default

        def alloc(data):
            a = heap[0]
            write(a, data)
            heap[0] = (a + len(data) + 15) & ~15
            return a

        def wsa_startup(mu):
            version, data = arg(mu, 0) & 0xFFFF, arg(mu, 1)
            log("WSAStartup", version)
            if s.startup == 0:
                write(data, struct.pack("<HHHHQ", 0x101, 0x202, 0, 0, 0) + b"WinSock 2.0".ljust(257, b"\0")
                      + b"Running".ljust(129, b"\0") + bytes(6))
            ret(mu, s.startup)

        def wsa_get_last_error(mu):
            log("WSAGetLastError")
            ret(mu, take(s.errors, s.last_error))

        def socket(mu):
            log("socket", _i32(arg(mu, 0)), _i32(arg(mu, 1)), _i32(arg(mu, 2)))
            h = take(s.sockets, None)
            if h is None:
                h, s.next_socket = s.next_socket, s.next_socket + 4
            ret(mu, h)

        def closesocket(mu):
            log("closesocket", arg(mu, 0))
            ret(mu, 0)

        def ioctlsocket(mu):
            sock, cmd, argp = arg(mu, 0), arg(mu, 1) & 0xFFFFFFFF, arg(mu, 2)
            log("ioctlsocket", sock, cmd, struct.unpack("<I", read(mu, argp, 4))[0])
            ret(mu, take(s.ioctl, 0))

        def setsockopt(mu):
            sock, level, name, val, n = arg(mu, 0), _i32(arg(mu, 1)), _i32(arg(mu, 2)), arg(mu, 3), _i32(arg(mu, 4))
            log("setsockopt", sock, level, name, read(mu, val, min(n, 64)), n)
            ret(mu, take(s.setsockopt, 0))

        def addr_call(name, results):
            def run(mu):
                # sin_family, sin_port and sin_addr: sin_zero is not looked at by AF_INET bind/connect, and the
                # original leaves it uninitialized
                sock, addr, n = arg(mu, 0), arg(mu, 1), _i32(arg(mu, 2))
                log(name, sock, read(mu, addr, 8), n)
                ret(mu, take(results, 0))
            return run

        def send(mu):
            sock, buf, n, flags = arg(mu, 0), arg(mu, 1), _i32(arg(mu, 2)), _i32(arg(mu, 3))
            log("send", sock, read(mu, buf, min(n, 0x1000)), n, flags)
            r = take(s.send, None)
            ret(mu, n if r is None else r)

        def sendto(mu):
            sock, buf, n, flags, to, tolen = (arg(mu, 0), arg(mu, 1), _i32(arg(mu, 2)), _i32(arg(mu, 3)),
                                              arg(mu, 4), _i32(arg(mu, 5)))
            log("sendto", sock, read(mu, buf, min(n, 0x1000)), n, flags, read(mu, to, min(tolen, 16)), tolen)
            r = take(s.sendto, None)
            ret(mu, n if r is None else r)

        def recv(mu):
            sock, buf, n, flags = arg(mu, 0), arg(mu, 1), _i32(arg(mu, 2)), _i32(arg(mu, 3))
            log("recv", sock, n, flags)
            reply = take(s.recv, SOCKET_ERROR)
            if isinstance(reply, int):
                ret(mu, reply)
                return
            data = reply[:max(n, 0)]
            write(buf, data)
            ret(mu, len(data))

        def recvfrom(mu):
            sock, buf, n, flags, frm, fromlen = (arg(mu, 0), arg(mu, 1), _i32(arg(mu, 2)), _i32(arg(mu, 3)),
                                                 arg(mu, 4), arg(mu, 5))
            have = _i32(struct.unpack("<I", read(mu, fromlen, 4))[0]) if fromlen else None
            log("recvfrom", sock, n, flags, have)
            item = take(s.recvfrom, SOCKET_ERROR)
            if isinstance(item, int):
                ret(mu, item)
                return
            data, source = item
            data = data[:max(n, 0)]
            write(buf, data)
            if frm and fromlen:
                write(frm, source[:max(min(have, 16), 0)])
                write(fromlen, struct.pack("<i", 16))
            ret(mu, len(data))

        def htons(mu):
            v = arg(mu, 0) & 0xFFFF
            log("htons", v)
            ret(mu, ((v & 0xFF) << 8) | (v >> 8))

        def ntohl(mu):
            v = arg(mu, 0) & 0xFFFFFFFF
            log("ntohl", v)
            ret(mu, int.from_bytes(v.to_bytes(4, "little"), "big"))

        def inet_addr(mu):
            name = m.read_cstr(arg(mu, 0))
            log("inet_addr", name)
            ret(mu, inet_aton(name))

        def gethostname(mu):
            buf, n = arg(mu, 0), _i32(arg(mu, 1))
            log("gethostname", n)
            if s.hostname is None:
                ret(mu, SOCKET_ERROR)
                return
            write(buf, (s.hostname + b"\0")[:n])
            ret(mu, 0)

        def gethostbyname(mu):
            name = m.read_cstr(arg(mu, 0))
            log("gethostbyname", name)
            host = s.hosts.get(name)
            if host is None:
                ret(mu, 0)
                return
            addrtype, addrs = host
            h_name = alloc(name + b"\0")
            aliases = alloc(bytes(8))
            ptrs = [alloc(a) for a in addrs]
            addr_list = alloc(b"".join(struct.pack("<Q", p) for p in ptrs) + bytes(8))
            ret(mu, alloc(struct.pack("<QQhhIQ", h_name, aliases, addrtype, 4, 0, addr_list)))

        def memcmp(mu):
            a, b, n = arg(mu, 0), arg(mu, 1), arg(mu, 2)
            x, y = read(mu, a, n), read(mu, b, n)
            r = next((p - q for p, q in zip(x, y) if p != q), 0)
            ret(mu, r)

        fns = {
            "WSAStartup": wsa_startup, "WSAGetLastError": wsa_get_last_error, "socket": socket,
            "closesocket": closesocket, "ioctlsocket": ioctlsocket, "setsockopt": setsockopt,
            "bind": addr_call("bind", s.bind), "connect": addr_call("connect", s.connect), "send": send,
            "sendto": sendto, "recv": recv, "recvfrom": recvfrom, "htons": htons, "ntohl": ntohl,
            "inet_addr": inet_addr, "gethostname": gethostname, "gethostbyname": gethostbyname,
        }
        # imports this file does not use yet (the Store build's and the PS4 server's): refuse them, so no test silently gets the harness's `return 0`
        for name in ("select", "getaddrinfo", "freeaddrinfo", "WSAIoctl", "inet_pton", "inet_ntop", "__WSAFDIsSet",
                     "ntohs", "WSARecvFrom", "WSASendTo", "WSASocketA", "WSACleanup", "getsockname", "getsockopt",
                     "WSASetLastError", "shutdown", "inet_ntoa"):
            fns.setdefault(name, _unmodelled(name))
        for name, fn in fns.items():
            m.on_import("ws2_32.dll!" + name, fn)
        m.on_import("vcruntime140.dll!memcmp", memcmp)
        missing = {n.split("!", 1)[1] for n in m._stub_names.values() if n.lower().startswith("ws2_32.dll!")} - set(fns)
        if missing:
            raise RuntimeError(f"ws2_32 imports without a model: {sorted(missing)}")


def _unmodelled(name):
    def run(mu):
        raise RuntimeError(f"ws2_32!{name} is not modelled")
    return run
