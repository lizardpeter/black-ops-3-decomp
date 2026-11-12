# BO3 enhanced security parity audit: T7 Patch and related community fixes

Audited 2026-11-12. **This document is a threat inventory, not an implemented-fix claim.**
BO3's original Steam x64 binary, the Microsoft Store T7 binary reconstructed here,
and the reference dedicated-server builds are different binaries. Steam offsets,
Steam API interception and Arxan-specific hooks must **not** be treated as verified
addresses, types or working mitigations in `BlackOps3_MSStore`.

## Upstream evidence

- [T7 Patch release history](https://github.com/shiversoftdev/t7patch/releases)
  documents new protection against a major RCE (1.11) and further RCE protection
  (2.04); the releases alone do not identify all vulnerable engine callsites.
- [T7 Patch source continuation](https://github.com/Scroptss/T7Patch-src):
  `Hooks.cpp` and `Protection.cpp` show parser guards, instant-message
  filtering, lobby membership checks, menu-response authorization, and opt-out
  of automatic Workshop subscriptions. This implementation was designed for
  Steam BO3. Review the code and port *semantics*, not its rebased offsets.
- [Ghosts IW6 audit](https://github.com/lizardpeter/ghosts-decomp/blob/main/docs/community-patches.md)
  documents related vulnerability classes, not proof that T7 has identical bugs.

## Surface-by-surface implementation checklist

| ID | Publicly documented mitigation family | Enhanced Store status | Required implementation and evidence |
|---|---|---|---|
| T7-S01 | Drop unsolicited peer-to-peer instant messages carrying command-buffer actions | **Unmapped / not fixed** | Locate Store instant-message/transport dispatcher, verify message framing, reject untrusted command messages before any script or command buffer, test malformed/truncated variants |
| T7-S02 | Strict join-party message parsing and bounded membership count | **Unmapped / not fixed** | Map Store lobby join parser, bound all counts to destination capacity (Steam patch uses 18), reject impossible element counts and lengths with no partial state mutation |
| T7-S03 | Validate lobby-state client lists and nominee arrays | **Unmapped / not fixed** | Apply per-array count, element, and destination bounds; test zero/negative, overlong and inconsistent counts |
| T7-S04 | Validate lobby-state-game vote records | **Unmapped / not fixed** | Check actual Store allocation and type widths; original Steam patch includes a 216-vote guard but that limit must be reverified on Store |
| T7-S05 | Validate host-heartbeat nominee lists | **Unmapped / not fixed** | Bound list count and end-of-array markers; reject invalid frames without touching client/session state |
| T7-S06 | Connectionless packet / relay validation | **Unmapped / not fixed** | Require a valid sender, exact packet size/type and source/session association before dispatch; constrain unconnected traffic |
| T7-S07 | Deny unauthorized remote console commands and menu-response control | **Unmapped / not fixed** | Host-authorize match-ending and server control operations; reject remote command-buffer execution; test non-host clients |
| T7-S08 | Bind info responses to an outstanding request | **Unmapped / not fixed** | Validate response type, sender and outstanding nonce/request; reject unsolicited or replayed responses |
| T7-S09 | Validate lobby chat sender and untrusted formatting | **Unmapped / not fixed** | Require the sender be a member of the current lobby; bound text and block control/format injection |
| T7-S10 | Prevent remote-triggered automatic Workshop/mod installation | **Unmapped / not fixed** | Default to explicit local consent; never accept a peer's install request as authorization |
| T7-S11 | Script runtime and mod trust boundary | **Unmapped / not fixed** | Prevent untrusted UI/mod scripts from accessing native library loading, OS commands and unrestricted file I/O; preserve signed asset verification |
| T7-S12 | Defensive string replacement, malformed lengths, invalid character and UI indices | **Unmapped / not fixed** | Reconstruct callsite and destination sizes; use checked writes; deterministic negative/oversize tests |
| T7-S13 | Secure peer identity and session authentication | **Not implemented** | Replace vendor identity with an authenticated local identity, independent replay protection and host authorization; do not equate a checksum or XUID with identity |
| T7-S14 | Exposed Havok Visual Debugger on TCP 25001 | **Fixed in enhanced source (P0008)** | `enhanced/_external/havok/Common/Visualize/hkVisualDebugger.cpp` does not open the debug server; existing differential/enhanced tests |
| T7-S15 | Demonware UDP/TCP/DNS/HTTP, Xbox HTTP and crash telemetry egress | **Enhanced source guards exist (P0003-P0007)** | `docs/network.md` maps entrypoints and tests. This is isolation, not proof all engine peer packets are safe or that a native enhanced executable uses every replacement |
| T7-S16 | Game-engine UDP packet size/parse safety | **Not proven secure** | Native `Sys_GetPacket` 1423F2450 and `NET_SendPacket` 1423F2600 are retained; audit inbound sizes, message reader arithmetic, reliability counters, rate limits and target buffers before online exposure |

## Security release gate

1. Confirm a Store-build function address and calling convention from its actual disassembly, reference PDB or controlled differential test.
2. Reconstruct the faithful function in `src/`; keep the original unchanged.
3. Add an enhanced replacement with explicit bounds, sender authentication,
   authorization and fail-closed behavior in `enhanced/`.
4. Add adversarial tests for malformed/empty/oversized packets and for a
   legitimate packet; ensure no state change when input is rejected.
5. **Verify the native Store executable actually reaches the replacement**.
   A compiled source-linked symbol is insufficient. Audit patched entries or
   installed hooks and test the packaged artifact.
6. Run targeted fuzzing with ASan/UBSan on an isolated parser harness, then a
   network-isolated Windows smoke test before exposing a host.
7. Record verified patch ID, Store VA, tests and runtime gate in
   `records/patches.tsv` and `docs/security.md`. Do not mark completed until
   native dispatch and tests both pass.

Current conclusion: **T7 Patch parity is not achieved.** Its Steam security
hooks cannot be copied directly into this Store decomp. The known existing
BO3 protections are mainly vendor-network isolation and disabling the Havok
debug listener. Until the native multiplayer message parsers are secured,
do not expose the enhanced game to untrusted Internet peers.
