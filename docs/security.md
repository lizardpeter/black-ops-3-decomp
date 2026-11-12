# Security

Security findings in the original, with what the enhanced build should do about them. Each has a row in
`records/bugs.tsv`; this file holds the longer write-up. Public CVEs and the fixes community clients apply go here
too, once confirmed against the reconstruction.

## B0004: Havok Visual Debugger server on TCP 25001 (fixed in the enhanced build: P0008)

The Store build runs Havok's Visual Debugger (VDB) server in retail. While a level's navigation volumes load
(141EBE450, the `%s_navvolume` loader), 141EBC350 creates Havok AI's debug object and the visual debugger (142AE2510,
"VDB Server instance has been created") and calls `hkVisualDebugger::serve(25001)` (142AE2740). serve gets a socket
from `hkSocket::s_create` (hkBsdSocket, `System\Io\Platform\Bsd\hkBsdSocket.cpp`), whose `listen` (142A43730) binds
**INADDR_ANY** on port 25001 and listens with a backlog of 2; the debugger then polls for and accepts clients every
frame (142A438F0 accept). So for the rest of the session the game client listens on every interface for Havok's VDB
protocol, a debug stream format never designed for untrusted peers. Whether anything reaches it depends on the
machine's firewall.

This has not been observed in a running game yet (the offline run has not reached a level), but nothing on the path
checks a dvar or build flag: 141EBE450 calls 141EBC350 unconditionally, and 141EBC350 only checks that it has not run
before.

The enhanced build's `serve` does nothing (P0008), so no socket is ever created; the visual debugger object is still
made, and its per-frame step finds no server. `serve`'s faithful version matches the original
(tests/differential/test_hkVisualDebugger.py).

## T7 Patch reference audit and enhanced-build implementation status (2026-11-12)

**References:** [T7Patch-src by Scroptss](https://github.com/Scroptss/T7Patch-src)
(`Protection.cpp` and `Hooks.cpp`), and T7 Patch release notes. These
protections target its *Steam* client. Our target is the Store build; upstream
Steam function addresses are not interchangeable with Store addresses.

| T7 Patch or local issue | What is supported by the reference | BO3 enhanced status |
|---|---|---|
| Crafted Steam P2P instant messages | `ReadP2PPacket` rejects selected message kinds, including join and cbuf classes | **Unresolved in game engine.** No Steam P2P API in the Store-targeted direct path; full native lobby/instant-message dispatcher still needs matching and an effective hook. |
| Join-party count overflow | `MSG_JoinParty_Package_Inspect` checks for more than 18 members and inconsistent list length | **Unresolved.** Reconstruct the Store lobby decoder, reject invalid counts *before* allocation or copying. |
| Lobby-state and heartbeat list overflow | `MSG_LobbyState_Package_Inspect` validates client lists (18 bound); `MSG_HostHeartbeat_Inspect` validates nominee list length (18 bound) | **Unresolved** until equivalent Store message entrypoints are found and wired. |
| Malformed lobby info responses | `MSG_InfoResponseSafe` bounds nested lobby arrays and fields | **Unresolved**, require bounded parsing of all nested data. |
| Unauthorized invites, info probes and remote command-buffer traffic | T7 Patch exposes friends-only, network-password, and packet-type guards | **Partial.** Experimental BO3 direct UDP is localhost-only without a key, and now supports independently authenticated v2 framing. Original game's peer message handlers are **not** verified safe. |
| Malicious network packets on custom UDP | T7 Patch restricts hostile P2P traffic | **New enhanced direct module protection:** `enhanced/direct/transport.cpp` limits payloads to 1262 bytes and 64 datagrams per polling pass; requires magic/version/exact length, selected-peer checks, and per-peer 64-sequence replay windows for 128-bit shared-key SipHash v2. No key = loopback-only v1. Tested in `tests/direct/transport.py`. |
| Unnecessary external listeners | Store retail Havok VDB listens on TCP 25001 | **Fixed in enhanced P0008:** `hkVisualDebugger::serve` opens no socket. |
| Vendor network and crash-report egress | Demonware, Xbox HTTP/WebSocket, analytics and uploaders | **Already partly guarded:** P0001/P0003–P0007. Additional offline import mapping now blocks `recv`, `recvfrom`, `WSARecv*`, socket binding, accepting, listening, polling, and related operations; guards reverse DNS and indirect OS loader names. Regression: `tests/security/offline_boundary.py`. |

### Explicit security boundaries

1. The **faithful** `src/` reconstruction is unchanged.
2. `enhanced/direct/transport.cpp` is a **custom, experimental** direct
   transport. It is not yet wired into every original engine networking path.
3. The **offline package** (`tools/offline/package.py`) denies both inbound
   and outbound socket operations at import boundaries. It is a contained
   diagnostic configuration, not proof that every enhanced native game path is
   completely isolated. `--enhanced` source reconstruction and the standalone
   offline DLL currently have different integration/packaging paths.
4. Shared-key v2 authentication is **not encryption**, individual peer
   authentication, a fresh session handshake, or remote-content validation;
   all keyholders can impersonate one another. Replay state is per socket
   lifetime. Key exposure via process command lines should be avoided.
5. T7 Patch RCE mitigation completeness cannot be inferred from its public
   version/release notes. None of the unreconstructed native Store lobby
   decoders is labelled 'fixed' until directly tested with malformed packets.

### Next security implementation gates

Identify and annotate the Store equivalents of `LobbyMsgRW_Package*`,
`MSG_JoinParty`, `MSG_LobbyState`, `MSG_HostHeartbeat`, and
`MSG_InfoResponse`; retain original secure content/fastfile checks;
reconstruct the parser/dispatch entrypoints in `src/` before adding
bounded, fail-closed `enhanced/` replacements. Add negative corpus tests
for out-of-range counts, truncated nested arrays, oversized strings and
untrusted remote command-buffer message types. Finish native process ingress
and egress verification separately from static tests.

## Community T7 protection inventory (reviewed 2026-11-12)

Sources: [T7Patch](https://github.com/shiversoftdev/t7patch),
[Scroptss T7Patch-src](https://github.com/Scroptss/T7Patch-src) (the
September 2026 compatibility fork), and
[BO3Enhanced security.cpp](https://github.com/shiversoftdev/BO3Enhanced/blob/master/security.cpp).
These projects target **different executable revisions and transport paths**.
Steam offsets and Steam P2P message layouts MUST NOT be copied into the
Microsoft Store build without independent matching. Their patches are
evidence of bug classes, not proof that a Store-build function is vulnerable.
This is a defensive audit ledger; no exploit payloads belong in this repo.

| Area | Publicly documented mitigation | Store enhanced status | Acceptance gate |
|---|---|---|---|
| Incoming Steam P2P instant messages | Reject unsafe join and remote command-buffer message types (101, 102, 109) before dispatch; control info requests | **Not mapped**: Store uses its own game/SDK transports, not Steam's vtable | Find Store-equivalent ingress, prove per-type parser boundary and fail-closed tests |
| Lobby messages and relay | Verify message type, source, lengths, nesting, and sender/session membership; T7Patch includes CL_HandleRelayPacket crash report | **Not mapped** | Reconstruct and fuzz Store lobby/relay parser with malformed and truncated messages |
| Peer admission | T7Patch optional network password and friends-only restrictions | **Not implemented for live Store engine UDP** | Adopt a cryptographic session MAC + replay protection; do not mistake checksum-XOR for authentication |
| Unsolicited OOB commands | Restrict info, join, chat and command-buffer-like messages by source/state; never accept arbitrary remote command text | **Not mapped** | Authenticated source, strict message allow-list, safe command tests |
| Identity and name spoofing | Check claimed XUID against actual admitted sender; bounded names | **Not mapped** | Verify per-session binding and bounded string handling |
| Lobby packet parsing | Field count/string/array/size/offset checks against declared message capacity | **Not mapped** | Negative/malformed/oversize corpus plus sanitizers |
| Loading scripts and mods | Restrict native DLL loading and unsafe script APIs for untrusted content | **Partially bounded by the isolated offline package**, not a complete VM sandbox | Verify Lua/HKS loader paths, signed content policy and hostile-script tests |
| Background debugger server | Never expose Havok Visual Debugger TCP listener | **Fixed in reconstructed enhanced function P0008** | Existing enhanced tests verify serve() does not listen |
| Demonware and Xbox egress | Disable unintended socket/DNS/HTTP/telemetry endpoints | **Reconstructed enhanced boundaries P0003–P0008; separate offline package redirects original IAT** | Existing offline tests and package manifest audits |
| Engine UDP ingress | Receive/parsing of local/peer game packets | **Still original and not secured by the above Demonware guards** | Establish an integrated pre-parser ingress gate before any live networking |

### Security release policy

- The **faithful** build remains an analysis artifact, never a safe multiplayer client.
- The **enhanced reconstruction DLL** and the **network-disabled offline package**
  are distinct: compiling an override does **not** redirect the retail EXE to it.
  The offline package denies network traffic, including LAN; this is strong
  containment but cannot be treated as an implemented multiplayer security patch.
- **Do not call the enhanced BO3 build safe for untrusted live multiplayer** until
  a specific Store-build inbound entrypoint is mapped, integrated into the native
  package, and tested with the full hostile-input corpus. The first priority is
  source-bound connection admission, then bounded lobby/relay parsing.
- Reuse the **design intent**, not the GPL project's code or offsets, unless the
  licensing and target-binary implications are explicitly reviewed.
- A 16-bit password-dependent checksum (as used in some community patch paths)
  is not a substitute for message authentication. Do not port it as an
  authenticated peer protocol.

### Sources and limitations

T7Patch's own README reports that it addresses RCE vulnerabilities and warns that
unpatched multiplayer remains dangerous. BO3Enhanced's README states that
some remote crashes remain even where easy RCEs are mitigated. Individual
underlying bugs are not all assigned public CVEs, and not all implementation
details can be transferred between Steam and Store binaries. A version-specific
patch without a verified Store ingress integration is **planned**, not fixed.
