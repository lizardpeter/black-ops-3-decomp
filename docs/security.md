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
