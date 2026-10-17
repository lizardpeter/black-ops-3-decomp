# Faithful and enhanced builds

The repo produces two builds from one source tree (decomp-project skill, principle 8).

| | **faithful** | **enhanced** |
|---|---|---|
| Purpose | the decomp: reproduces the original exactly, bugs included; the ground truth | the faithful code plus deliberate, documented changes: security fixes, bug fixes, modernization, features |
| Source | `src/`, `include/` | `src/` + `enhanced/` (same layout as `src/`) |
| Tests | strict: `matches` means identical behaviour to the original binary | each change's intended effect, and identical to faithful everywhere else |
| Online use | not safe: it keeps the original's known vulnerabilities (docs/security.md) | intended |

## Rules

1. **`src/` contains only original behaviour.** Never "improve" a faithful function, even for an obvious bug:
   the bug is part of the original. Record it as a finding and fix it in `enhanced/`.
2. **A function defined in `enhanced/` overrides the faithful one in the enhanced build only.** This uses the same
   per-function linking as the hybrid link, so there are no conditionals in `src/`. Faithful fixes reach the
   enhanced build automatically because it shares that code.
3. **`records/patches.tsv` lists every change:** id, functions changed (build + VA), kind (`bugfix`, `security`,
   `modernize` such as frame rate, widescreen, platform ports, or `feature`), description, test reference.
4. **Two build targets; CI builds and tests both.**
5. **Changes go on verified faithful code** wherever possible. Patching unverified code makes it impossible to
   tell a fix from a decompilation error. Security-critical functions are therefore good early decomp targets.
6. **Not yet created:** `enhanced/`, `records/patches.tsv` and the enhanced build target are added with the first
   enhancement, not before.
7. **One repo** unless licensing or contributors differ (e.g. importing GPL code from a community client, which
   the faithful repo should not take on). A separate enhanced repo would use this one as a submodule, never a
   copy, and needs the user's decision first.

Arxan and DRM are in neither build: they aren't game source.

## Known bugs

Every bug found in the original is listed in `records/bugs.tsv` (security issues too, with the detail in
docs/security.md). That list is the work queue for `bugfix` and `security` changes in the enhanced build.

## Planned enhancements

docs/roadmap.md, once there are any.
