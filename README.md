# black-ops-3-decomp

Reverse engineering and reconstruction of **Call of Duty: Black Ops III (T7), PC x64**, with a verified faithful source path and a documented **enhanced** variant.

The project deliberately keeps original `src/` behavior separate from fixes in `enhanced/`. Function reconstruction status is tracked in [STATUS.md](STATUS.md); see [AGENTS.md](AGENTS.md) before editing.

## Canonical enhanced build

**Use [`tools/enhanced/build.py`](tools/enhanced/build.py)** to build the one enhanced package, with the original pinned Store executable, reconstructed `recon.dll`, local identity/authenticated direct transport, GDK offline compatibility and XCurl/WinHTTP failure boundaries. The package verifier checks hashes, exports and reconstruction provenance.

See **[Enhanced build and launch instructions](docs/enhanced-build.md)**.

**Current limitation:** The enhanced engine overrides are compiled and packaged but not yet activated in the original Store game's callsites. Native Windows launch, playable menus, local multiplayer and comprehensive service isolation remain unverified. The Wine launcher is an isolated startup diagnostic, not a finished playable release. The original game files are not included in this repository and must be supplied legitimately.

The reversal methodology follows [ghosts-decomp](https://github.com/lizardpeter/ghosts-decomp) and [black-ops-1-decomp](https://github.com/lizardpeter/black-ops-1-decomp).
