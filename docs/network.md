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

### 2. Xbox services HTTP client (libHttpClient)

29 functions at 142D749B0–142D81860 using both WinHTTP and XCurl (`curl_multi_*`), near the Xbox Live URLs
`sessiondirectory.xboxlive.com` and `wss://rta.xboxlive.com/connect` (real-time activity), which no code references
directly (they are reached through data). It is Microsoft's libHttpClient, linked with XAL (its own strings:
`xbox::httpclient::NetworkState::HttpCallPerformAsync`, `CurlProvider::PerformAsync`, `HCWebSocketConnectAsync`, the
`libHttpClient/1.0.0.0` user agent, a `...\External\xal\External\libHttpClient\Source\...` path). Leaves: the
XCurl wrappers 142D749B0 (global cleanup), 142D74F20 (global init), 142D78C70–142D7AC00 (easy/multi), and the
WinHTTP wrappers 142D75F20–142D81860 (the WebSocket provider).

Every operation starts with `XAsyncBegin` (14291FD40, a GDK runtime thunk), so with the offline package's
`xgameruntime` stub none can start at all, and the Xbox services API has no signed-in user to make requests for.
In code: **HTTP is cut** at `NetworkState::HttpCallPerformAsync` (142D6DEB0, the single entry every request takes:
decompiled, matches; P0007 refuses it with HRESULT_FROM_WIN32(ERROR_NETWORK_UNREACHABLE)). **The WebSocket is
not cut in code yet:** its entry is `NetworkState::WebSocketConnectAsync` (142D6E3C0, called only by the public
`HCWebSocketConnectAsync` 142D6B670), which moves two std::strings and a shared_ptr into its context; until it is
reconstructed, the RTA WebSocket depends on the GDK stub.

### 3. Telemetry: the Store port's crash reporter

One module at 1423B87C0–1423B9F70 (no `__FILE__` strings; named here by behaviour):

| function | what |
|---|---|
| 1423B9AB0 | init: `curl_global_init`, registers the dvars behind the reporter (Analytics URL `https://ssl.google-analytics.com/collect`, tracking id `UA-69466650-2`, a sample rate defaulting to 0.05, two enable flags) |
| 1423B9C70 | builds the crash *signature*: MD5 of the return addresses from `RtlCaptureStackBackTrace`, as hex, into 149331788 |
| 1423B9F70 | called by `Com_Error_` (142210B90): at most once per 600 s, makes the signature, copies the error text, and raises an exception |
| 1423B9DE0 | the report (reached from the exception path through 1423F1F80): rate-limited, then 1423B87C0, then with probability = sample rate 1423B8BA0, and the log file the same way |
| 1423B87C0 | **sends** the Analytics event `?v=1&t=event&tid=…&cid=<machine GUID>&ec=signature&ea=…&el=…` with `curl_easy_perform` |
| 1423B8BA0 | writes `crash_reports/<time>.gltn` (signature, machine GUIDs, platform, build `CL(20660835) … BEYQBBUILD132`, build info, error text, timestamp, then the dump) and runs `system("start CrashUploader.exe …")`, a separate uploader |

Both 1423B87C0 and 1423B8BA0 identify the machine persistently: a random GUID stored in
`HKLM\SOFTWARE\Activision\HardwareSurvey\Host` (created on first use), and 1423B8BA0 adds the Windows volume's
object id (`DeviceIoControl` 0x900C0 on the Windows directory). So **every engine error is reported off the machine
with a hardware identifier**, and crashes are uploaded by an external program the game launches. Replacing
1423B87C0 and 1423B8BA0 (or 1423B9DE0 above them) cuts all of it; the faithful versions are self-contained apart from
the registry, curl and file calls. First to replace (B0006).

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
through Demonware matchmaking and relays. **Decided (the user): the engine's UDP path stays** in the enhanced build,
for local and LAN play and later the user's own server; none of the functions above is overridden.

The STUN/QoS probe (1414F7F00) is not engine traffic: it fills a Demonware `bdSocketRouterConfig` with the four STUN
hosts and starts Demonware's socket router, whose socket comes from `bdSocket::create` (14297B660) and so from
`bdPlatformSocket::create`. With P0004 that creation fails, the router does not start (the probe records state 0), and
no STUN packet or lookup is sent. 141ED4750's direct `bdPlatformSocket::getHostByName` call is cut the same way.

### 5. Voice chat (GameChat2)

10 wrappers at 141EE8070–141EEA270, plus 141FF7610 (incoming packets). Only remote users generate traffic; offline they have no one
to talk to. Low priority, but the DLL ships only with the GDK, so the stubs also remove a dependency.

### 6. Everything else

| function | what | priority |
|---|---|---|
| 142A433D0–142A43DA0 | Havok `hkBsdSocket` (`System\Io\Platform\Bsd\hkBsdSocket.cpp`): connect, **listen/accept** ("Listening on host [ ] port"). The Havok Visual Debugger's server; reached only through its vtable (142DF6E50). Whether retail ever creates it is not yet known. | security check (B0004) |
| 14149E620, 14149E870, 14149E6D0 | Development fastfile key server: UDP to `10.150.4.43` / `10.150.97.133` port 10019 (magic `0xDEADFAC4`), asking for a zone's 32-byte key when it is not in the built-in table (154AD2750, 384 entries). Called from fastfile loading (14149EAC0), only when 141FBC390 allows. Private addresses: cannot reach the internet. | low (B0005) |
| 142360D50 | the `ui_browser_new` console command (registered at 141404170): with argument 1, 2 or 3 it opens `http://www.google.com` or `https://www.google.com` in the default browser through ShellExecuteA (1423BEB90). Only runs when typed; the game itself sends nothing | none |
| 141ED5630 | WSAStartup; `fakeDWDisconnect` debug path | with Demonware |
| 141F219D0, 141FA6A20 | wlanapi / GetAdaptersInfo: reads local adapter state, sends nothing | none |
| 1423B5210, 1423B5320 | raw UDP/TCP helper; no code or data reference to 1423B5320 found | none (unreferenced) |
| 141364180, 141DA8F50, 141F02B00, 141ED6610, 141EDC660 | support/registration/MTX/Elite URLs, opened in a browser or passed to Demonware | none (no own traffic) |

## Order of work

1. **Telemetry** (1423B9DE0, 1423B87C0, 1423B8BA0, then 142360D50): the crash reporter in section 3, the only
   traffic that leaves the machine with no online play at all, and it carries a hardware identifier.
   **Done for the reporter:** 1423B9DE0 is its only entry and the only caller of both senders, so it was
   decompiled (`src/win32/crash_report.cpp`, matches) and overridden to report nothing (P0003). The senders
   themselves stay undecompiled until something else needs them. 142360D50 turned out to be a console command that
   opens google.com in the browser when typed (section 6), not traffic.
2. **Demonware leaves** (the 25 functions in section 1): cuts lobby, auth, storage, NAT, UPnP and relays at once.
   **UDP layer done:** the seven `bdPlatformSocket` methods are decompiled
   (`src/libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket-xboxone.cpp`, all match) and overridden
   (P0004): no socket is created and no name is looked up. **TCP layer done:** the nine `bdPlatformStreamSocket`
   methods (`.../bdPlatformStreamSocket-xboxone.cpp`, all match; P0005). **HTTP done:** the worker's every
   request needs the WinHTTP session `initializeWinHTTP` (142D14BA0) opens, and its thread takes no request until
   that succeeds; it is decompiled (matches) and overridden to never open one (P0006), as if the network never came
   up. The other WinHTTP leaves in the table are unreachable without that session. **All of Demonware's traffic is
   cut in the enhanced build** (UDP, TCP, DNS, HTTPS); what Demonware's callers do when it never connects is the
   next thing to check in an offline run.
   Decompile the faithful versions first (the socket wrappers are short), then the enhanced overrides return the
   network-down result. Startup must then take the "Demonware unavailable" path rather than wait for it; that is
   what `Live_BlockUntilSignedInToDemonware`, `LiveConnect_DisableDemonwareConnect` and `Live_IsDemonwareFetchingDone`
   (records/names.tsv) decide, so they follow.
3. **Xbox services HTTP client** (section 2): HTTP done (P0007); the WebSocket entry (142D6E3C0) is still to do.
4. **Havok VDB socket** (B0004): find whether the server is created; cut it either way.
5. **Engine networking** stays (section 4). **Voice** (section 5) only carries traffic to remote players.

Each replacement is a faithful function in `src/` (verified by differential test like any other) plus its
override in `enhanced/`, recorded in `records/patches.tsv`. None of this edits the exe.
