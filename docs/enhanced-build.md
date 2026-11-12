# Canonical enhanced BO3 build

The project has **one enhanced package build path** on main:

\`tools/enhanced/build.py\`

It does **not** modify the faithful \`src/\` reconstruction. Modernizations and
security corrections belong in \`enhanced/\`, with entries in
\`records/patches.tsv\`. Original game files are never committed or
distributed.

## Current architecture

| Component | Packaged into enhanced output | Live in the game? |
|---|---|---|
| Pinned original \`BlackOps3.exe\` | Yes, byte-identical | Yes, when run under Wine |
| GDK shim \`wine-system32/xgameruntime.dll\` | Yes | Yes, **only** when installed into a private Wine prefix |
| Local profile and authenticated v3 UDP | Compiled into the GDK shim | Code loaded; engine does not yet call local transport |
| App-local XCurl and WinHTTP failure providers | Yes | Subject to actual game DLL resolution; requires native log verification |
| \`recon.dll\` faithful+enhanced reconstruction | Yes | **Not automatically loaded or hooked** into engine callsites |
| Differential/enhanced tests and source symbol provenance | Tested in CI; source records bundled | Not proof of gameplay |

The Store binary loads GDK through \`LOAD_LIBRARY_SEARCH_SYSTEM32\`.
This is why an app-local GDK DLL alone is insufficient on native Windows.
Do **not** copy the replacement into an actual Windows system folder,
disable system services, or misrepresent a Wine diagnostic as a finished
Windows game. Earlier modified-PE packaging failed in a Store TLS integrity
callback, so the canonical builder does not use it.

## Build

Install the repository's existing Clang/LLVM/lld-link/pefile toolchain and
provide a legitimate original Store executable matching \`target.toml\`.
First create the enhanced hybrid reconstruction:

\`\`\`sh
T7_ORIGINALS=.work/originals python3 tools/build_recon.py \
    --build BlackOps3_MSStore --enhanced
T7_ORIGINALS=.work/originals python3 tests/enhanced/run.py
python3 tests/direct/run.py
python3 tests/security/offline_boundary.py
\`\`\`

Then build **one** component-audited package:

\`\`\`sh
python3 tools/enhanced/build.py \
    --original .work/originals/BlackOps3_MSStore.exe \
    --recon build/BlackOps3_MSStore/enhanced/recon.dll \
    --out build/BlackOps3_MSStore/enhanced-package

python3 tools/enhanced/verify.py \
    build/BlackOps3_MSStore/enhanced-package
\`\`\`

The builder refuses unknown EXEs, missing reconstruction or source-link
tables, unreviewed component dependencies, pre-existing output directories,
and unresolved expected shim exports. It records SHA-256 and byte lengths
for every packaged binary and source provenance table. It records hybrid
unresolved-symbol counts without hiding them. A successful build is
**not** evidence that game hooks are installed.

No original executable is added to GitHub releases or published CI artifacts.

For component-only CI checks without game assets:

\`\`\`sh
python3 tools/enhanced/build.py --components-only --out /tmp/t7-components
python3 tools/enhanced/verify.py /tmp/t7-components
\`\`\`

## Isolated Wine diagnostic (current supported launch experiment)

Initialize a **private** Wine prefix, make the complete original game
installation available, and use:

\`\`\`sh
python3 tools/enhanced/run_wine.py \
    --package build/BlackOps3_MSStore/enhanced-package \
    --game /path/to/authentic/BO3-installation \
    --prefix .work/t7-private-wine \
    --out .work/t7-enhanced-run \
    --seconds 90 --player-name LocalPlayer
\`\`\`

The launcher verifies the entire package, refuses unrecognized or symlinked
Wine system directories, installs its GDK shim only for the bounded run,
persists a random self-asserted local ID in the private prefix, and launches
through \`tools/offline/wine_run.py\` with its inherited IP-socket-denying
seccomp policy. It does not automatically host or join. It cleans up its
temporary GDK shim and session lock, preserving logs locally. It does not
claim coverage of host IPC brokers, injected code, or subprocess egress
outside the runner's documented restrictions.

This is a **diagnostic**, not a validated playable BO3 release.

## Critical remaining integration

1. **GDK startup:** identify which specific \`QueryApiImpl\` requests are
   mandatory for offline initialization without manufacturing Xbox user,
   licensing, or online entitlements. Observe actual file-open, FastFile,
   renderer and menu milestones with a complete authorized installation.
2. **Engine hosting:** map the Store binary's original multiplayer message,
   command, identity, client, server, and initialization layouts. Establish
   a controlled source-aware way to activate reconstructed enhancements.
   A loaded shim or bundled \`recon.dll\` is not engine integration.
3. **Network safety:** route BO3's actual packet operations through audited
   transport and admission rules; verify malformed packet and replay
   resistance end-to-end. Static leaf-function tests are not sufficient.
4. **Security parity:** compare vulnerabilities and community fixes against
   BO3's exact Store implementation. The separate Steam/BOIII/t7patch
   mitigations cannot be assumed to share addresses, data structures,
   or complete coverage.
5. **Native Windows:** create a verified native integration route that does
   not depend on overwriting a Microsoft system DLL. The optional read-only
   \`tools/offline/ProbeNative.ps1\` is a baseline, not the enhanced client.

Neither process-wide vendor detachment nor a rendered BO3 enhanced menu,
loaded map, direct multiplayer join, or successful local match is yet
verified. Keep these gates false until measured on an actual runtime.
