# Menus and settings

How the Store build (`BlackOps3_MSStore`) builds its menus and keeps its settings, and how the enhanced build can add
its own options (the late latch's `r_lateLatch`, Reflex later) to the graphics menu. Addresses are the Store build's.

## The menus are Lua

The whole UI is LUI: Lua scripts run in Havok Script (HKS), Treyarch's Lua 5.1 VM. The scripts are `luafile` assets
in the fastfiles (`zone/`, not in this repo). None of the UI is in the exe; the exe only provides the VM and the
`Engine.*` calls the scripts make.

- **Start-up.** `UI_CoD_Init` (14202BDB0) sets up the UI's Lua state (the primary VM, 149AD3B28, made by
  `Lua_CoD_GenerateLuaState_Internal` 142017E60). It then `require`s `ui.T6.CoDRoot`, which loads the rest.
- **The VM's entry points**, all identified: `hksi_hksL_loadbuffer` (141E52BB0) compiles a chunk, `hksi_lua_pcall`
  (141E54EF0) runs it, `hksL_loadfile` (141E52AC0).
- **`Engine.*` functions** are C functions registered into the VM. Their names are known by matching against the
  Steam build (`Lua_CoD_LuaCall_*`, about 1,400 of them), for example `SetDvar` (1420FA710), `DvarInt` (1420FA9B0),
  `SetHardwareProfileValue` (1420E6E30). P0010's refresh-rate list is one of them (`GetAvailableRefreshRates`,
  docs/refresh-rate.md).

## The graphics options

Each options page is a Lua *data source*: a function that returns a list of items, which the page lays out as
dropdowns, checkboxes and sliders. The PC video page is `DataSources.OptionGraphicsVideo` (`"PC.OptionGraphicsVideo"`).
BOIII's `ui_scripts/graphics_settings` replaces it from the Steam build's script, so its shape is known:

```lua
{
  models = {
    label = "PLATFORM_SYNC_EVERY_FRAME",    -- localized string ref (plain text works too)
    description = "PLATFORM_VSYNC_DESC",
    profileVarName = "r_vsync",            -- the setting it reads and writes
    widgetType = "checkbox",               -- or "dropdown" (with a datasource), "slider" (lowValue/highValue)
  },
  properties = CoD.PCUtil.OptionsGenericCheckboxProperties,
}
```

**Saving and loading.** A `profileVarName` on this page is a **hardware-profile** setting. Those are the settings
kept in `players/config.ini`, as `Key = value` lines with a comment above each. The list is fixed in the exe: 58
entries of 0x18 bytes at 1433881B0 (config key, dvar name hash, comment), filled at start-up by 140080840. The
entries are `com_maxfps`, `com_drawFPS_PC`, `com_smoothFrames`, `cg_fov_default`, the mouse settings, `r_fullscreen`,
`r_mode`, `r_refreshRate`, `r_vsync`, the quality settings and so on. The values sit in 58 strings of 0x40 bytes at
159B7D390.

Five functions use that list. Each looks a dvar up by hash among the 58 entries and does nothing with one that isn't
there:

| Function | What it does |
| --- | --- |
| 1420E6D90 | `Engine.GetHardwareProfileValue(AsString)`: the stored string |
| 1420E6E30 `Lua_CoD_LuaCall_SetHardwareProfileValue` | stores a new string, marks the profile changed (159B7E211) |
| 1423BC330 | reads `players/config.ini` (`Key = value`) into the stored strings |
| 1423BC760 | applies the stored strings to the dvars |
| 1414F1A70 | writes them back out as a "settings" section, on the save path (called from 1414F2250, which mentions `OnKVSFlush`) |

Settings the page doesn't know about are plain dvars: BOIII's quick settings use `CoD.OptionsUtility.CreateDvarSettings`
with `Engine.SetDvar`. Those are not saved in `config.ini`.

## Adding an option (the plan)

1. **Make `r_lateLatch` a hardware-profile setting**, so it is saved in `config.ini` and the video page can read and
   write it. The enhanced build gets a 59-entry list: the original 58 plus `LateLatch` / `r_lateLatch` / a comment.
   It also gets enhanced versions of the five functions, walking that list instead of the 58. They come from faithful
   decomps with differential tests, as usual. Reflex is one more entry later.
2. **Run a Lua chunk of the enhanced build's own once the UI is up**: compile it with `hksi_hksL_loadbuffer` on the
   primary VM and run it with `hksi_lua_pcall`, as BOIII does from its `UI_CoD_Init` hook. The chunk *wraps* the
   game's `DataSources.OptionGraphicsVideo` list function rather than replacing it. It calls the original and inserts
   one checkbox after V-Sync, so the game's own items, order and behaviour stay as they are:

   ```lua
   local original = DataSources.OptionGraphicsVideo.prepare  -- ListSetup's list function (name to be confirmed)
   -- ... returns the original list with {label = "Late Latch", description = "...",
   --     profileVarName = "r_lateLatch", widgetType = "checkbox"} inserted after r_vsync
   ```
3. **Where to run it.** `UI_CoD_Init` is too large to replace just to add a call after it. The better hook is a small
   function on the path that loads Lua files, run once the options scripts are loaded. That function still has to be
   found (`Lua_CoD_GetRawFile`-like, under hks `require`).

Still to find: the Store build's own options scripts. They are in the fastfiles, and BOIII's copy is the Steam
build's, so they need reading to confirm the data source's name, its `ListSetup` field and the checkbox properties
before the chunk is written.
