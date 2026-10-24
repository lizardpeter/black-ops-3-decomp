// Havok Script (hks), BO3's Lua: the part of its C API reconstructed code uses so far. Layouts from use in the Store
// build (Lua_CoD_LuaCall_GetAvailableRefreshRates and the hks routines it calls), not from hks headers.
#pragma once

#include <string.h>  // size_t

enum HksObjectType
{
	TNIL = 0,
	TNUMBER = 3,
	TSTRING = 4,
	TTABLE = 5,
};

struct HksObject
{
	unsigned int t;      // HksObjectType in the low 4 bits
	unsigned int pad;
	union
	{
		float number;
		void *ptr;
	} v;
};
static_assert(sizeof(HksObject) == 0x10, "HksObject");

struct lua_State
{
	char unknown00[0x48];
	HksObject *top;
	HksObject *base;
};

// 1414E3C40: the value at a stack index truncated to int (numbers; strings converted; anything else 0). The Steam
// build's name for it (records/names.tsv) is kept, with the index-based prototype the Store build shows.
int hks_obj_tonumber(lua_State *s, int index);
void *lua_createtable(lua_State *s, int narr, int nrec);
void hksi_lua_pushlstring(lua_State *s, const char *str, size_t len);
void lua_settable(lua_State *s, int index);

// hks pushes inline: the Store build has these expanded at every call site.
inline void lua_pushnumber(lua_State *s, float n)
{
	HksObject *top = s->top;
	top->t = TNUMBER;
	top->v.number = n;
	s->top = top + 1;
}

inline void lua_pushnil(lua_State *s)
{
	HksObject *top = s->top;
	top->t = TNIL;
	s->top = top + 1;
}

inline void lua_pushstring(lua_State *s, const char *str)
{
	if (!str)
	{
		lua_pushnil(s);
		return;
	}
	size_t len = 0;
	while (str[len])
		len++;
	hksi_lua_pushlstring(s, str, len);
}
