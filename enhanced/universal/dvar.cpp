// P0015: the FOV setting goes down to 60, MW2019's minimum (B0021).
//
// cg_fov_default is the player's field of view, already in MW2019's unit (the horizontal FOV at 16:9, docs/fov.md),
// default 80 like MW2019's, but registered with the range 65-120. The enhanced build allows 60-120, MW2019's range;
// everything else Dvar_Init does is unchanged. The settings menu's slider is Lua in the game's fastfiles and keeps its
// own range; 60-64 can be set in config.ini ("FOV") or the console.

#include "universal/dvar.h"

void Dvar_Init()
{
	byte_158835226 = 1;
	dword_1599E7624 = 0;
	r_cmdbuf_worker = Dvar_RegisterBool(Dvar_GenerateHash("r_cmdbuf_worker"), "r_cmdbuf_worker", false, 0x4400,
	                                    "Process command buffer in a separate thread", false);
	snd_losOcclusion = Dvar_RegisterBool(Dvar_GenerateHash("snd_losOcclusion"), "snd_losOcclusion", true, 0x4400,
	                                     "occlusion based off of LOS", false);
	// P0015: the minimum was 65
	cg_fov_default = Dvar_RegisterFloat(Dvar_GenerateHash("cg_fov_default"), "cg_fov_default", 80.0f, 60.0f, 120.0f,
	                                    0x4400, "User default field of view angle in degrees", false);
	cg_fov_default_thirdperson =
		Dvar_RegisterFloat(Dvar_GenerateHash("cg_fov_default_thirdperson"), "cg_fov_default_thirdperson", 40.0f, 1.0f,
	                       160.0f, 0x4400, "User default 3rd person field of view angle in degrees", false);
	cg_chatHeight = Dvar_RegisterInt(Dvar_GenerateHash("cg_chatHeight"), "cg_chatHeight", 0, 0, 8, 0x4400,
	                                 "The font height of a chat message", false);
	sv_cheats = Dvar_RegisterBool(0xF70E34E1, "", false, 0x84, "", false);              // sv_cheats
	Dvar_RegisterBool(0xBFA02692, "", false, 0x1000, "", false);                       // allClientDvarsEnabled
	Dvar_AddCommands();
}
