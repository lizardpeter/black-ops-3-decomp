// UI Lua calls (the LuaCall_* functions the menus call into C). Source path unknown; names are the community clients'
// (records/names.tsv).

#include <stdio.h>

#include "_external/hks/hks.h"
#include "gfx_d3d/r_init.h"

// 1420E7490  ui/lua_cod_luacalls.cpp
// GetAvailableRefreshRates(width, height, monitor): a table {"144.000", "120.000", ...} of the refresh rates of the
// monitor's display modes at width x height, highest first. Only the first 128 modes of the monitor's list (sorted
// by size, smallest first) are looked at (B0013): on a monitor with more modes, the large resolutions list nothing,
// and the settings menu offers no refresh rate for them. The menu stores the chosen string in r_refreshRate.
int Lua_CoD_LuaCall_GetAvailableRefreshRates(lua_State *luaVM)
{
	int width = hks_obj_tonumber(luaVM, 1);
	int height = hks_obj_tonumber(luaVM, 2);
	unsigned int monitor = hks_obj_tonumber(luaVM, 3) - 1;
	int count = 0;
	char buffer[4096];
	const char *rateNames[128];
	if (monitor < DX_MAX_MONITORS)
	{
		char *out = buffer;
		int last = (int)dx_modeCount[(int)monitor] > 128 ? 128 : (int)dx_modeCount[(int)monitor];
		for (long long i = last - 1; i >= 0; i--)
		{
			const DXGI_MODE_DESC *mode = &dx_modes[(int)monitor][i];
			if ((int)mode->Width != width || (int)mode->Height != height)
				continue;
			rateNames[count] = out;
			int len = sprintf(out, "%.3f",
			                  (double)((float)mode->RefreshRate.Numerator / (float)mode->RefreshRate.Denominator));
			count++;
			out += len + 1;
		}
	}
	HksObject table = {};
	table.t = TTABLE;
	table.v.ptr = lua_createtable(luaVM, 0, 0);
	*luaVM->top = table;
	luaVM->top++;
	for (long long i = 0; i < count; i++)
	{
		lua_pushnumber(luaVM, (float)(int)(i + 1));
		lua_pushstring(luaVM, rateNames[i]);
		lua_settable(luaVM, -3);
	}
	return 1;
}
