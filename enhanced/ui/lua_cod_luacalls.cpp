// P0010: the settings menu lists the refresh rates of every display mode, not only of the first 128 (B0013).
//
// The original looks at the first 128 entries of the monitor's mode list. That list is sorted smallest size first and
// a modern monitor easily has more than 128 modes (DXGI_ENUM_MODES_SCALING lists every size at every rate), so the
// largest resolutions, usually the native one, get an empty list and the menu offers no refresh rate for them. The
// enhanced build scans the whole list, highest rate first as before, and still returns at most 128 rates (the
// table the original builds has room for that many). Lists of up to 128 modes give exactly the original's table.
// docs/refresh-rate.md.

#include <stdio.h>

#include "_external/hks/hks.h"
#include "gfx_d3d/r_init.h"

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
		for (long long i = (long long)dx_modeCount[monitor] - 1; i >= 0 && count < 128; i--)
		{
			const DXGI_MODE_DESC *mode = &dx_modes[monitor][i];
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
