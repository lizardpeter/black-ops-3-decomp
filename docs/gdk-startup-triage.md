# BO3 GDK dispatch and pre-menu startup triage

**Build:** pinned `BlackOps3_MSStore` EXE, byte-identical, private isolated Wine only.
**Goal:** get the first authentic BO3 FastFiles and menu loaded, without invoking
Xbox/MS Store/Demonware services. Nothing in this note claims a menu has rendered.

## Corrected GDK ABI

The public clean-room GDK interface investigation documents
`QueryApiImpl(const GUID* classId, REFIID interfaceId, void** out)`.
The previous stub treated `classId` as a 64-bit numeric ID. That recorded a
pointer, not a class identity, and prevented meaningful diagnosis. The new
shim logs the **GUID content** when it comes from the pinned EXE's image,
never raw pointers. Unknown pointers are not dereferenced for telemetry.

Sources / interoperable facts:
- https://github.com/xodus-gaming/xgameruntime-docs/blob/main/QueryApiImpl.md
- https://github.com/xodus-gaming/xgameruntime-docs/blob/main/COM/README.md
- https://learn.microsoft.com/en-us/gaming/gdk/docs/reference/system/xgameruntimefeature/functions/xgameruntimeisfeatureavailable

The documented fallback for an unsupported COM class is
`HRESULT_FROM_WIN32(ERROR_NOT_SUPPORTED)` (`0x80070032`), not a fabricated
successful interface or an Xbox account. The GDK replacement returns this
unless the specifically opted-in offline feature interface handles the request.

## Narrow in-process recon path

During `InitializeApiImpl*` (not DllMain), the GDK replacement resolves an
absolute `recon.dll` path beside the original EXE. It loads the canonical
enhanced DLL, resolves and executes `T7EnhancedReconProbe`, and registers
`T7EnhancedObserveGdkDispatch`. Each subsequent GDK `QueryApiImpl` can
enter source-defined enhanced code. Positive evidence in Wine debug logs:

- `T7GDK:RECON_PROBE_OK`: the exported reconstruction probe returned its
  expected version.
- `T7GDK:RECON_CALLBACK_EXECUTED`: a later runtime dispatch passed through
  the reconstruction's observer; the recon-side count was read back.
- `T7GDK:RECON_LOAD_FAILED` / `T7GDK:RECON_LOAD_ERROR=...`: a DLL/dependency
  or fixed-base loader problem requiring investigation.

A probe/callback is an **in-process interop milestone**, not an engine
packet/session/menu hook. `T7EnhancedEngineIntegrated()` remains 0 until
actual engine function replacement is verified.

## Isolated GDK COM A/B probe

The independently implemented `XGameRuntimeFeatureImpl` singleton implements
IUnknown and `XGameRuntimeIsFeatureAvailable`. It returns **false for every
feature**, including Xbox services and Store features. It supplies no XUser,
XStore license, entitlement, network callback, or online token.

Only the same canonical enhanced build is used. Default run leaves the COM
class unavailable; `--local-feature-interface` enables this one
offline-safe COM interface. This is a diagnostic A/B, **not** a second
enhanced build or a bypass for licensing.

### Run A: baseline enhanced GDK dispatch

```sh
python3 tools/enhanced/run_wine.py --package build/BlackOps3_MSStore/enhanced-package \
  --game /path/to/owned/BO3 --prefix .work/private-t7-wine \
  --out .work/t7-baseline --seconds 90 --trace-files
```

### Run B: local offline feature interface

```sh
python3 tools/enhanced/run_wine.py --package build/BlackOps3_MSStore/enhanced-package \
  --game /path/to/owned/BO3 --prefix .work/private-t7-wine \
  --out .work/t7-feature-probe --seconds 90 --trace-files --local-feature-interface
```

The prefix must be private, initialized, and unused by any other process.
The launcher supplies native overrides for the three audited offline shims
(`xgameruntime`, `xcurl`, `winhttp`). An inherited Linux seccomp filter
blocks IPv4/IPv6 networking during Wine runs. Do not install the runtime DLL
into real Windows system32 or run this experiment with live Xbox services.

Review `startup.json` from both runs. Inspect which COM classes were queried
and whether the last request changes between runs; track FastFile path
mentions separately. File mentions are **not** successful opens, and window
creation does not mean a rendered menu. Raw `wine.log` contains local file
paths: keep it private.

## Remaining blockers

1. Verify the bridge actually loads/calls under Wine. If it fails, use its
   loader error and check recon's fixed-base address and dependencies.
2. See which actual COM class is requested before localization loading
   finishes. Implement only that class's **offline-safe** operations with
   exact ABI checks; do not guess vtable layouts or fabricate platform
   identities. Task queues and local storage are candidates, not verified
   sources of the black-screen stall.
3. Confirm actual successful FastFile opens/decompression before claiming a
   menu fix.
4. Hook BO3's real networking, session and menu entrypoints only after
   checking exact Store build layouts and runtime call sequences.
5. Execute a controlled native Windows enhanced run with legitimate assets
   to verify real menus and local gameplay.

There has been no new native game-startup execution in this development
session; component tests and code commits are not a menu pass.

## Confirmed pre-GDK Wine loader failure in minimal EXE-only diagnostic

The 2026-11-12 pinned Store EXE Wine probe, [CI run 43314796699](https://github.com/lizardpeter/black-ops-3-decomp/actions/runs/43314796699),
exited with code 53 before any GDK or recon.dll markers. The new Wine
`+module` diagnostics reported missing `gamechat2.dll` and
`libScePad.dll`. This **precedes** the previously observed full-install
localization stall, so that older stall is not yet resolved.

The single canonical enhanced package now includes an app-local,
**fail-closed GameChat2 import shim** exporting the 16 names BO3 statically
imports. This shim has no Xbox user, XUID, HTTP or network dependencies;
it cannot provide actual voice-chat functionality. It is only an import
loader boundary. Its generic Win64 signatures are not yet fully validated
against every GameChat2 API prototype; game-side calls still require runtime
investigation before this can be considered complete compatibility.

The workflow now inventories exact `libScePad.dll` import names or
ordinals from the pinned executable. No controller stub should be claimed
complete until its export and ABI requirements are established.
The minimal CI game directory also has **no `zone/*.ff` assets**,
so even a successful GDK probe cannot demonstrate a rendered menu.
