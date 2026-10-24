# Online surface of the Store build

Everything in `BlackOps3_MSStore` that can reach a network, grouped by subsystem, with the functions to replace so
the game never connects online. The goal (the user's) is that every call reaching a server is replaced by a
reconstructed function, the exe staying byte-identical (docs/native-launch.md). This file is the map and the order
of work; the per-function data is generated.

## How it was found

`tools/net/surface.py` writes `analysis/BlackOps3_MSStore/net/` from the generated analysis and the exe's import
table:

| file | what |
|---|---|
| `imports.tsv` | the 87 imports from network DLLs (ws2_32 33, WinHTTP 16, XCurl 17, GameChat2 16, wlanapi 4, iphlpapi 1) and how many functions reference each IAT slot |
| `hosts.tsv` | the 45 strings naming a server or URL, and the functions that use them |
| `functions.tsv` | 688 functions: the 90 that reference a network import directly, plus every function in the Demonware library, attributed by the library's own `__FILE__` strings (`code\libs\DemonWareGDK\...`) and `bdClass::` log strings |
| `callers.tsv` | the direct callers of each of those (2,308 edges) |

A reference is any instruction operand equal to an IAT slot or a string address, so calls through the slot and
loads of it into a register both count. Every import except `WSASetLastError` is referenced.

**Not visible to this pass:** calls through the GDK runtime's API table (`QueryApiImpl`: XUser, Xbox Live
multiplayer/presence/achievements, store, XNetworking) and calls through vtables. The GDK side is already cut at
the DLL by `enhanced/offline/xgameruntime_stub.cpp`, which answers every `QueryApiImpl` with `E_NOTIMPL`. Vtable
calls end in the same import-calling functions listed here, so cutting those still cuts them.

## The subsystems

Addresses are Store build VAs. "Leaves" are the functions that call the OS network API themselves; replacing the
leaves cuts the subsystem whatever calls it.

### 1. Demonware (lobby, auth, matchmaking, storage, NAT, relays)

589 functions attributed to `DemonWareGDK` source files, the largest groups bdLobby (280: lobby service, LSG
services, content streaming, login queue, matchmaking, anti-cheat), bdSocket (88: NAT, QoS, DTLS, socket router),
bdCore (74), bdMessageRelay (50: TURN over DTLS), bdHTTP (34), bdConnection (34), bdNet (24: **UPnP port mapping**,
gethostbyname). All of its traffic goes through three leaf layers:

| layer | leaves | source file |
|---|---|---|
| UDP sockets | 1429C3E70, 1429C3ED0 (inet_pton), 1429C3F60 (bind), 1429C4290 (close), 1429C4320 (create), 1429C4620 (getaddrinfo), 1429C4790 (recvfrom), 1429C4AC0 (sendto) | bdPlatform/bdPlatformSocket/bdPlatformSocket-xboxone.cpp |
| TCP sockets | 142D16EC0, 142D16F40, 142D17050, 142D171E0, 142D172D0, 142D173A0, 142D17530, 142D176F0 | bdPlatform/bdPlatformSocket/bdPlatformStreamSocket-xboxone.cpp |
| HTTPS | 142D10FC0, 142D11930 (response), 142D12770 … 142D15D80 (worker: WinHttpOpen, Connect, OpenRequest, SendRequest, ReadData, WriteData) | bdHTTP/bdHTTPResponse, bdHTTPWorker/bdHTTPWorkerWinHTTP.cpp |

25 functions. Replacing them with versions that fail the way an unreachable network fails (socket creation
fails, name lookup fails, HTTP open fails) cuts all of Demonware, including UPnP, STUN and the TURN relays.

**Server addresses.** The Demonware hosts are chosen in three static initializers, each constructing a host
selector global from a dev and a prod name (through 1429A5EB0):

| initializer | global | dev | prod |
|---|---|---|---|
| 140050D40 | 149F941D0 | lsg.2705.dev.demonware.net | lsg.2710.prod.demonware.net |
| 140050D70 | 149F935D0 | auth3.dev.demonware.net | auth3.prod.demonware.net |
| 140050DA0 | 149F94DD0 | t7-pc-qbl.dev.demonware.net | ops3-pc-qbl.prod.demonware.net |

The Umbrella (14299E7E0, 1429AD600) and UNO (1429A2F40) URLs are picked by environment in code. These are where
a future own main server would be pointed, instead of re-enabling any of the leaves above.

### 2. Xbox services HTTP client (probably libHttpClient)

29 functions at 142D749B0–142D81860 using both WinHTTP and XCurl (`curl_multi_*`), near the Xbox Live URLs
`sessiondirectory.xboxlive.com` and `wss://rta.xboxlive.com/connect` (real-time activity), which no code references
directly (they are reached through data). No `__FILE__` strings: identified by API use and address range only. Leaves: the XCurl wrappers 142D749B0 (global cleanup), 142D74F20 (global
init), 142D78C70–142D7AC00 (easy/multi), and the WinHTTP wrappers 142D75F20–142D81860.

### 3. Telemetry: Google Analytics

| function | what |
|---|---|
| 1423B9AB0 | `curl_global_init`, sets up `https://ssl.google-analytics.com/collect` with tracking id `UA-69466650-2` |
| 1423B87C0 | builds `?v=1&t=event&tid=…&cid=<random GUID>&ec=signature&ea=…&el=…` and sends it with `curl_easy_perform` |

Reached from `Com_Error_` (142210B90) through 1423B9F70, and from 1423F1F80 through 1423B9DE0: **every engine
error is reported to Google Analytics** by the Store port. Two leaves, both small. First to replace.

### 4. Engine networking (peer-to-peer and listen server)

| function | what |
|---|---|
| 1423F2450 `Sys_GetPacket` | recvfrom on the game socket |
| 1423F2600 `NET_SendPacket` | sendto; 15 callers (`SV_DirectConnect`, `NET_OutOfBandPrint`, `CL_CheckForResend`, …) |
| 1423F2840 | gethostname / gethostbyname (local address) |
| 1423F2DA0 | socket shutdown; reads `net_ip`, `net_port` |
| 142241240, 1422414C0 | WSAStartup; `255.255.255.255` broadcast and `localhost` lookup (LAN) |
| 142007DA0 | gethostbyname / inet_addr |
| 1414F7F00 | QoS probe: `stun.{us,eu,au,jp}.demonware.net`, `127.0.0.1` |
| 141F97310 | QoS configuration (`qosconfig4.csv`), inet_addr |

This is game traffic between players, not to Activision's servers, but in retail it reaches other players only
through Demonware matchmaking and relays. **Decision for the user:** keep the engine's UDP path (local and LAN
play, and later the own server) and cut only the STUN/QoS probe, or cut it all for the first offline build.

### 5. Voice chat (GameChat2)

10 wrappers at 141EE8070–141EEA270, plus 141FF7610 (incoming packets). Only remote users generate traffic; offline they have no one
to talk to. Low priority, but the DLL ships only with the GDK, so the stubs also remove a dependency.

### 6. Everything else

| function | what | priority |
|---|---|---|
| 142A433D0–142A43DA0 | Havok `hkBsdSocket` (`System\Io\Platform\Bsd\hkBsdSocket.cpp`): connect, **listen/accept** ("Listening on host [ ] port"). The Havok Visual Debugger's server; reached only through its vtable (142DF6E50). Whether retail ever creates it is not yet known. | security check (B0004) |
| 14149E620, 14149E870, 14149E6D0 | Development fastfile key server: UDP to `10.150.4.43` / `10.150.97.133` port 10019 (magic `0xDEADFAC4`), asking for a zone's 32-byte key when it is not in the built-in table (154AD2750, 384 entries). Called from fastfile loading (14149EAC0), only when 141FBC390 allows. Private addresses: cannot reach the internet. | low (B0005) |
| 142360D50 | connectivity check against `www.google.com` (reached through a function pointer at 141404170) | with telemetry |
| 141ED5630 | WSAStartup; `fakeDWDisconnect` debug path | with Demonware |
| 141F219D0, 141FA6A20 | wlanapi / GetAdaptersInfo: reads local adapter state, sends nothing | none |
| 1423B5210, 1423B5320 | raw UDP/TCP helper; no code or data reference to 1423B5320 found | none (unreferenced) |
| 141364180, 141DA8F50, 141F02B00, 141ED6610, 141EDC660 | support/registration/MTX/Elite URLs, opened in a browser or passed to Demonware | none (no own traffic) |

## Order of work

1. **Telemetry** (1423B87C0, 1423B9AB0, 142360D50): small, self-contained, and the only traffic that leaves
   the machine on a crash.
2. **Demonware leaves** (the 25 functions in section 1): cuts lobby, auth, storage, NAT, UPnP and relays at once.
   Decompile the faithful versions first (the socket wrappers are short), then the enhanced overrides return the
   network-down result. Startup must then take the "Demonware unavailable" path rather than wait for it; that is
   what `Live_BlockUntilSignedInToDemonware`, `LiveConnect_DisableDemonwareConnect` and `Live_IsDemonwareFetchingDone`
   (records/names.tsv) decide, so they follow.
3. **Xbox services HTTP client** (section 2), unless the xgameruntime stub already keeps it idle; check in the
   offline run which of its leaves are ever called.
4. **Havok VDB socket** (B0004): find whether the server is created; cut it either way.
5. **Engine networking and voice**, after the user's decision in section 4.

Each replacement is a faithful function in `src/` (verified by differential test like any other) plus its
override in `enhanced/`, recorded in `records/patches.tsv`. None of this edits the exe.
