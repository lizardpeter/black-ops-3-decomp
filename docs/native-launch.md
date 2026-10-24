# Bringing the Store build up offline

Goal: get the Store build (`BlackOps3_MSStore`) to start with no network, as the base for hosting reconstructed
functions (`src/`) in the running process. This is a startup investigation on Linux/Wine with a software GPU
(Mesa llvmpipe/lavapipe), not a playable build and not a claim about native Windows hardware. All of it runs with
every IP socket blocked by an inherited seccomp policy (`tools/offline/wine_run.py`), so nothing can reach any
server, official or custom.

Method and tooling come from `ghosts-decomp` (its `docs/native-launch.md`, `docs/offline-package.md`,
`tools/offline/`). The game files are only read; the patched exe is always a separate copy
(`tools/offline/package.py`).

## Run 1 — the unmodified Store exe

`BlackOps3.exe` loads under Wine and stays up. It reaches its own window and stops at the first expected gate:
a dialog, **"XGameRuntime failed with error code -1994129151"** (0x89240101). That is the Xbox GDK runtime
(`xgameruntime.dll`), which only exists on Windows/Xbox. `WinMain` (1423EA4D0) treats a failed
`XGameRuntimeInitialize` as fatal. The GDK static layer is at 14291FA64 (init) / 14291FCC0 (dispatch);
`XGameRuntimeInitialize` is 142920308.

## The offline package

`tools/offline/package.py` writes a separate `BlackOps3_offline.exe` plus `recon.dll`
(`tools/offline/build_dll.py`, `enhanced/offline/`). It adds a `.t7off` section with new import descriptors and
lookup tables, points the Store exe's original IAT slots for network, HTTP, process launch, COM activation, event
tracing and dynamic loading at `recon.dll` failure adapters (57 redirects, P0001), and replaces
`XGameRuntimeInitialize` with an adapter that reports success without loading the runtime (P0002). The original's
section-header table is full, so the packager first makes room for one more header by shifting every section's
file offset by one `FileAlignment` block; virtual addresses, and so every code/data reference, are unchanged.
`manifest.json` records every change and the exe/dll hashes.

The structural rewrite was verified harmless in isolation: a copy with **only** the header growth and a
recomputed checksum (no entry patch, no import redirects) runs exactly like the unmodified exe — same gate, no
early exit. Its only loaded-image differences from the original are three debug-directory pointer bytes that moved
with the header shift.

## Run 2 — the offline package: the anti-tamper gate

With the entry patch and import redirects applied, the process exits early (about 1.5 s), during a **TLS callback
at process attach** (access violation, `c0000005`). The unmodified exe never faults there; the structural-only
copy never faults there. So the fault is the game reacting to the modified image, not the PE surgery.

The Store exe's TLS callback (`142253A70`, "tls_callback_0") is a single ~50 KB function that Ghidra cannot type
cleanly — the usual shape of an obfuscated anti-tamper routine. BO3 is known to ship a self-integrity/anti-tamper
layer (the community preservation clients BOIII and t7patch neutralize it to run the game offline; this project's
`docs/prior-art.md` tracks them). So starting a *modified* Store exe offline runs into that check, exactly as the
`ghosts-decomp` offline work ran into Ghosts' equivalents.

This is the current blocker. The relevant choice is recorded in the session, not pre-decided here:

- **Leave `.text` and the import table untouched.** If the check only covers the exe's own code, keeping the exe
  byte-for-byte original and instead satisfying the GDK layer with a stub/replacement `xgameruntime.dll` beside it
  (the BOIII approach), and reaching our reconstructed code through a loaded module rather than a code patch,
  should pass it. Most faithful to the "don't modify the original" principle; the open question is how much of the
  GDK API dispatch (`QueryApiImpl`) a stub must cover.
- **Characterise and satisfy the check** within the reviewed offline-patch set, as `ghosts-decomp` did for its
  integrity/reporting entries — a documented, reviewed patch rather than an ad-hoc change.

Nothing here establishes ban immunity or online compatibility, and none is sought: the build is for offline
preservation and for running this repo's reconstructed engine code in a process the user owns.

## Run 3 — byte-identical exe + stub xgameruntime.dll (the chosen path)

The exe is left **completely unmodified**; our behaviour goes in from outside it. The Store exe loads
`xgameruntime.dll` from system32 with `LoadLibraryExA(..., LOAD_LIBRARY_SEARCH_SYSTEM32)` (14291FC80) and resolves
five entries: `InitializeApiImpl`, `InitializeApiImplEx`, `UninitializeApiImpl`, `XErrorReport`, `QueryApiImpl`.
`enhanced/offline/xgameruntime_stub.cpp` is a minimal stand-in: `InitializeApi*` report success, `QueryApiImpl`
reports `E_NOTIMPL` and clears its out pointer, `XErrorReport` is swallowed. It fabricates no user, licence or
online result; GDK features degrade rather than run.

Result, with the **unmodified** `BlackOps3.exe` and this stub in the prefix's system32:

- **Anti-tamper stays quiet: zero TLS-callback faults.** Keeping the exe byte-for-byte original passes the
  self-integrity check, confirming the byte-identical approach.
- **Past the GDK fatal gate.** No "XGameRuntime failed" dialog; the process stays up for the full run instead of
  exiting at ~1.5 s.

So the decision is settled: don't modify the exe. Get our code and the no-network behaviour in through replacement
DLLs (the GDK stub, a proxy for `recon.dll`, socket stubs), not through `.text`/import patches.

### Current stall

Startup then reaches localization loading (`localization_*.txt` all open) and stalls there, black, before any
`zone/*.ff` fastfile is opened — so it is a startup/GDK stall, not a missing map. The likely cause is
`QueryApiImpl` returning `E_NOTIMPL`: the game waits on a GDK service (user, storage or presence) that never
initialises. Next: give the stub enough of the GDK API dispatch for startup to proceed, then fastfile loading and
the renderer (the latter needs the full game install, which is being uploaded). The `tools/offline/package.py`
`.text`/import path is kept for reference but is not the route to a running build.
