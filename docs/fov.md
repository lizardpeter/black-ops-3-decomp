# Field of view

How the Store build (`BlackOps3_MSStore`) turns the player's FOV setting into the picture, what is off, and what the
enhanced build changes. Addresses are the Store build's; names and evidence in `records/names.tsv`.

## The setting is already MW2019's unit

The FOV the player sets is `cg_fov_default`, registered by `Dvar_Init` (1423ABE50) as an archived profile dvar: default
**80**, range **65–120**. config.ini stores it as `FOV`, with the game's own comment *"Horizontal field of view in
degrees assuming 16:9 aspect ratio"* (option table built by 140080840), and the code agrees: it is the horizontal FOV
at 16:9, exactly MW2019's unit (MW2019: default 80, range 60–120). So no unit conversion is needed for MW2019-style
numbers; only the range and the accuracy of the picture differ (below).

## From the setting to the picture

1. **Lens.** `sub_1405B2E80` makes a lens from the setting, BO3 modelling the view as a camera with a 14 mm-high
   sensor: focal length `f = 7 / (tan(h/2) · 9/16)` mm (in the Dead Ops Arcade gametype, "doa", the lens comes from
   the player state instead). Aiming down sights blends towards the weapon's lens (1405A02A0, 1405A8F00, 1405AC120).
   The lens lands in cg+0x2D8910 (focal length) and +0x2D8914 (focus distance).
2. **Projection.** `CG_CalcFOVfromLens` (1405AFA30), called with a negative FOV, clamps the lens to the current
   preset's limits (table at `[1486EFDA0]+0x5A0`) and computes `tan(vertical/2) = 14 / ((f/(d−f) + 1) · 2f) = 7/f − 7/d`
   for focus distance `d`, then `tan(horizontal/2) = tan(vertical/2) · aspect` (cgs+0x10, the window's shape: **Hor+**,
   wider screens see more at the same vertical FOV). It returns the FOV in degrees as `2·atan(tan(vertical/2)/0.75)`,
   the horizontal FOV at 4:3, eased over time by 14056A350.
3. **Storage.** `sub_1405B6690` (IW's CG_CalcFov) stores tanHalfFovX, tanHalfFovY (twice) and that FOV at
   cg+0x131D68..0x131D74. Scripted cameras call it with a fixed FOV instead (15, 50: horizontal at 4:3).

`cg_fov` (default 65, range 1–160) is a different thing: an FOV in the 4:3 unit used by the cg_drawMinimap lens path and
by 1400C44A0. 1408E3D40 copies the setting into it unconverted (B0022).

| setting (h at 16:9) | vertical | h at 4:3 (cg_fov unit) | h at 21:9 |
|---:|---:|---:|---:|
| 60 | 35.98 | 46.83 | 74.31 |
| 65 | 39.43 | 51.08 | 79.80 |
| 80 | 50.53 | 64.37 | 95.52 |
| 90 | 58.72 | 73.74 | 105.39 |
| 100 | 67.67 | 83.58 | 114.82 |
| 110 | 77.55 | 93.93 | 123.84 |
| 120 | 88.51 | 104.82 | 132.51 |

(ideal values: `vertical = 2·atan(tan(h/2)·9/16)`, `4:3 = 2·atan(tan(h/2)·3/4)`.)

## The picture is narrower than the setting (B0020)

With depth of field off — cg+0x131D28 & 0x30000 == 0, which `sub_1405B4BF0` leaves clear outside scripted cameras —
`CG_CalcFOVfromLens` ignores the lens's focus and uses `d = max(500 mm, f + 1)`. A lens focused at half a metre
magnifies, so `tan(vertical/2)` loses `7/500 = 0.014`. Measured by running the original function in the emulator
(focus far away, aspect 16:9):

| setting | shown at 16:9 (original) | with depth of field on |
|---:|---:|---:|
| 65 | 62.95 | 65.00 |
| 80 | 78.31 | 80.00 |
| 90 | 88.56 | 90.00 |
| 100 | 98.81 | 100.00 |
| 110 | 109.05 | 110.00 |
| 120 | 119.28 | 120.00 |

Weapon zooms go through the same lens and are narrowed the same way, but those are the zooms the game shipped with.

## Enhanced build

- **P0015** (`enhanced/universal/dvar.cpp`): `cg_fov_default` accepts **60–120**, MW2019's range (B0021). Default
  stays 80. The settings menu's slider is Lua inside the fastfiles and keeps its own range; 60–64 is reachable through
  config.ini (`FOV`) or the console.
- **P0016** (`enhanced/cgame/cg_view.cpp`): hip fire shows exactly the set FOV. After `CG_CalcFOVfromLens`, for the
  lens view with depth of field off, `tanHalfFovY` gets `(1 − fWeaponPosFrac) · 7/500` back (focus at infinity when
  not aiming), `tanHalfFovX` keeps the aspect, and the stored FOV moves by the same angle. Fully aimed down sights is
  the original's zoom, so weapon zooms are unchanged; the transition stays continuous. Depth of field on, the
  cg_drawMinimap lens and fixed scripted-camera FOVs are untouched.

Tests: `tests/enhanced/test_fov.py` runs the real `CG_CalcFOVfromLens` against both builds (hip FOV exact to 0.01° for
60–120, Hor+ at 21:9, ADS identical to the original, the other lenses identical). The faithful
`Dvar_Init` and `sub_1405B6690` pass their differential tests (`tests/differential/test_dvar.py`, `test_cg_view.py`).

Sensitivity no longer depends on FOV in the enhanced build (the mouse work); in the original, hip-fire sensitivity
is scaled by tanHalfFovY / 0.4778, so the narrowing of B0020 also lowers it by about 4% at the default 80.

## Obfuscated pointers: calling the game's code from recon.dll

`cg` (149B25A20), `cgs` (149B25A28) and dvar values are stored encoded. Every use decodes inline with a state
machine picked by the PEB address (`(PEB >> 12) & 15`: 16 variants). The machines also look at the return address of
the function they sit in and the bytes before it: from a caller outside the exe their start state changes, and the
machine can then loop forever. Measured in the emulator (all 16 PEB variants):

- the standalone cg decoder 141406ED0 called from 180000FF8 (recon.dll's range) hangs in 9 of 16 variants, from
  100000FF8 in 7;
- `CG_CalcFOVfromLens`'s inline decoders hang when it returns to 180001005 (variant 2);
- **`Dvar_GetBool`, `Dvar_GetFloat` and `Dvar_GetInt` hang in every variant** when called from either range.

So once reconstructed code runs in the game, any direct call from recon.dll into such an original function
(including the dvar getters) would freeze the game, depending on where Windows put the PEB. Tests don't show it:
they fake the getters, and a direct call to the obfuscated code from the test's sentinel hangs too.

`tools/recon/include/t7_exe_call.h` is the way round used here: `T7ExeCall(fn, args...)` calls `fn` with its return
address at `140096EE8`, an `add rsp, 28h; ret` right after a real call in the exe, which then returns to the caller.
Decoding from there gives the same results as from the exe's own call sites, in all 16 variants (dvar getters and
141406ED0 tested). At most five arguments. The test harness gained `ret_site` (return into the exe from the function
under test) and `at` (run Python mid-function, e.g. to place a known pointer where a decoder leaves its result).
