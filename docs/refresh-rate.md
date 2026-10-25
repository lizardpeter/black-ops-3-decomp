# Refresh rate

How the Store build (`BlackOps3_MSStore`) chooses the display's refresh rate, why it cannot go above 240 Hz, and what
the enhanced build changes. Addresses are the Store build's; names in `records/names.tsv`.

## How the rate is chosen

BO3 asks for a rate; it does not take the desktop's.

- **`r_refreshRate`** is a latched float dvar, registered by `sub_141D976E0` (141D976E0) next to `r_monitor` and
  `r_mode`: default 60, **domain [1, 240]**.
- **First run.** The hardware detection (141DA9620, reached from 141DA9940 when the config is new) sets `r_mode` to
  the largest enumerated mode and `r_refreshRate` to that mode's rate, and `com_maxfps` to the rate rounded.
- **The menu.** `GetAvailableRefreshRates(width, height, monitor)` (1420E7490) lists the rates of the monitor's modes
  at that size as strings ("143.998"); the chosen one is written to `r_refreshRate`.
- **The swap chain.** 141DABB90 collects `r_fullscreen`, `r_monitor`, `r_mode`, `r_refreshRate` into the window
  parameters, and `sub_141DA7A00` (141DA7A00) builds the `DXGI_SWAP_CHAIN_DESC`. In exclusive fullscreen
  (`r_fullscreen 1`) it copies the enumerated `DXGI_MODE_DESC` of that size whose rate is **closest** to
  `r_refreshRate`; DXGI then switches the display to exactly that mode (`ResizeTarget`, swap chain vtable +0x70).
  Windowed and borderless (`r_fullscreen 0` / `2`) never request a mode: the desktop's own rate applies.
- **Display modes** (141DAA790): per DXGI output of the adapter, `GetDisplayModeList(R8G8B8A8_UNORM,
  DXGI_ENUM_MODES_SCALING)`; modes under 800x600 dropped, the rest sorted by size then rate (`sub_141DAA730`) and
  duplicates merged. Nothing here limits the rate.

Why a chosen value rather than the current one: exclusive fullscreen needs a complete display mode (size *and*
rate), and DXGI's own choice for a zero rate is up to the driver; the game makes the rate a setting and matches it
against the modes the monitor reports. Games that follow the desktop either run borderless (the desktop mode is used
as is) or fill the fullscreen mode from the output's current mode instead of a dvar.

## The 240 Hz cap (B0012)

`Dvar_SetVariant` (1423A21C0) checks every new value with `Dvar_ValueInDomain` (14239D330); outside the domain it
prints "'%s' is not a valid value for dvar '%s'" and keeps the old value. With the domain ending at 240:

- on a 360 Hz monitor the first-run detection's `r_refreshRate 360` is refused, so a fresh config sits at **60 Hz**;
- picking 360 in the menu, or `r_refreshRate 360` in the console, is refused the same way;
- the swap chain can then only pick the mode closest to at most 240.

`com_maxfps` (int, 0..1000) is not involved: the frame cap already goes past 240.

A second, smaller limit (B0013): `GetAvailableRefreshRates` only scans the first 128 entries of the monitor's mode
list. That list is sorted smallest first, so on a monitor reporting more than 128 modes the largest sizes, usually
the native one, show no rates at all.

## Enhanced build

- **P0009** (`enhanced/gfx_d3d/r_dvars.cpp`): `r_refreshRate`'s domain becomes [1, 1000], `com_maxfps`'s own ceiling.
  Detection, the menu and the console can set any rate the monitor reports, and `sub_141DA7A00` selects it.
- **P0010** (`enhanced/ui/lua_cod_luacalls.cpp`): the menu lists rates from the whole mode list (still highest first,
  at most 128), so the native resolution's rates are offered.

Both are tested in `tests/enhanced/test_refresh_rate.py` against the faithful functions, which pass their
differential tests (`tests/differential/test_r_dvars.py`, `test_r_init.py`, `test_lua_cod_luacalls.py`).

These take effect once the reconstruction is hosted in the running game (docs/native-launch.md); until then they are
verified in the emulator only. A config written by the original keeps whatever `r_refreshRate` it saved (60 after a
refused detection): set it once in the menu, or with `r_refreshRate <rate>` in the console (it is latched: the video-mode check, 141DAC790, applies it).

## Not done yet

- **Follow the desktop.** A "0 = use the monitor's current or highest rate" setting would need the present path
  first: on AMD with vsync on, during a loading screen, 141D46720 sleeps `1000 / r_refreshRate - 2` ms before each
  present (B0015, docs/presentation.md), which would be undefined for 0; the enhanced flip-model path drops it (P0019).
- The comparator that never returns 0 (B0014).
