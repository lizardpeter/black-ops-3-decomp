# BO3 offline runtime and direct-play integration

This project preserves two fundamentally different surfaces. **The retail EXE is not a custom service emulator**,
and the enhanced build must not forge Xbox users, licensing, entitlements, or vendor tokens.

## Current verified state

- The original Store EXE (SHA-256 pinned in `target.toml`) launched under isolated Wine, and a GDK replacement
  in the prefix's `system32` passed the initial Xbox runtime fatal gate without modifying the EXE.
  Startup stalled before opening `zone/*.ff`; no menu, game load, or multiplayer join has been verified.
- The old patched-PE `tools/offline/package.py` experiment fails in a TLS anti-tamper callback; it is not
  the selected launch route and **must not** be reported as a working package.
- `enhanced/offline/xgameruntime_stub.cpp` now traces at most 64 GDK API identifiers to the debugger, never
  player names/tokens and never the IID data; it reports unavailable APIs with `E_NOTIMPL`, clearing the output
  pointer. The replacement imports only `GetCommandLineA` and `OutputDebugStringA` from `kernel32`.
- `enhanced/direct/profile.cpp` and `startup.cpp` validate a local, user-generated 64-bit identity and
  name from a single `+direct_player <16hex> "<name>"` argument. This is independent, not an XUID or XUser.
- `enhanced/direct/transport.cpp` is an isolated IPv4 UDP implementation with numeric endpoints, bounded
  payloads, framing, checksums, explicit peer selection, and no DNS or vendor infrastructure.
  **It has NOT yet been wired into BO3's engine packet send/receive and session admission. The Win32 transport initializes Winsock once per process (rather
than leaking per-session WSAStartup references).**
- The linked `--enhanced` reconstruction and the isolated GDK stub remain **two development artifacts**.
  BO3 does not yet have Ghosts' canonical packaged running-enhanced client or local-match support.

## Build and check, without game assets

```sh
python3 tests/direct/run.py
python3 tools/offline/build_gdk_stub.py --out build/BlackOps3_MSStore/gdk-stub
python3 tests/direct/gdk_stub.py --dll build/BlackOps3_MSStore/gdk-stub/xgameruntime.dll
```

The stub is only for an isolated Wine prefix, using legitimate original game files. Never install it into the
real Windows system directory. The local transport's tests exercise two real loopback UDP sockets and malformed
packets without connecting to the internet.

## Remaining critical path

1. Trace which GDK `QueryApiImpl` calls precede the first FastFile open; re-run the existing
   `tools/offline/wine_run.py` under its AF_UNIX-only seccomp sandbox with the newly built stub. Evidence must
   come from an actual run; these source changes do not show the startup stall is solved.
2. Identify a safe engine-hosting integration for the enhanced reconstruction **without** editing the guarded
   Store PE. The existing standalone stub does not load `recon.dll` or replace the game call sites.
3. Map BO3's actual multiplayer address/message layouts and exact entrypoints, then bridge the local UDP
   transport and identity into BO3's command/session flow. Do not borrow Ghosts' absolute addresses or netadr
   layout guesses. Keep original direct game UDP isolated from third-party services.
4. Validate Windows startup with legitimate complete assets, on real hardware, with outbound traffic blocked
   and controlled logs. Only then claim menu success, map load, or successful local join.

The independent profile is intentionally self-asserted. It cannot be used as proof of online authentication.

## Capturing bounded Wine startup evidence

The existing `tools/offline/wine_run.py` now includes `+debugstr` by default and prefers the
prefix-local `xgameruntime` shim. A run produces both the raw `wine.log` and a derived
`startup.json`. Only observed GDK markers appear in the derived trace; it never treats
initialization as proof of FastFile or menu progress. Stable custom player IDs and names are
redacted from `result.json` command arguments; review the **raw** Wine log before sharing.

```sh
python3 tools/offline/startup_trace.py --log path/to/wine.log
```

The reduction code is independently tested using synthetic log lines. Those tests do **not**
constitute a Wine run or native Windows test.
