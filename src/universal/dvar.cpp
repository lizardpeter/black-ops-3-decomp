// The dvar system's start. Names: Dvar_Init from its place and work (WinMain's call that registers the archived
// profile dvars and then the dvar commands), as in IW's universal/dvar.cpp; records/names.tsv has the evidence.
//
// Unlike most of the Store build these dvars are registered by name: the names are hashed here (Dvar_GenerateHash)
// and also passed, with their descriptions, because they are the ones a player's profile and config.ini carry.

#include "universal/dvar.h"

// The dvar_t pointers it fills (r_cmdbuf_worker, snd_losOcclusion, cg_fov_default, cg_fov_default_thirdperson,
// cg_chatHeight, sv_cheats) are the original's globals, declared in universal/dvar.h (hybrid link).

// 1423ABE50  universal/dvar.cpp
// cg_fov_default is the player's field of view: the horizontal FOV at 16:9, 65 to 120, default 80 (docs/fov.md).
void Dvar_Init()
{
	byte_158835226 = 1;
	dword_1599E7624 = 0;
	r_cmdbuf_worker = Dvar_RegisterBool(Dvar_GenerateHash("r_cmdbuf_worker"), "r_cmdbuf_worker", false, 0x4400,
	                                    "Process command buffer in a separate thread", false);
	snd_losOcclusion = Dvar_RegisterBool(Dvar_GenerateHash("snd_losOcclusion"), "snd_losOcclusion", true, 0x4400,
	                                     "occlusion based off of LOS", false);
	cg_fov_default = Dvar_RegisterFloat(Dvar_GenerateHash("cg_fov_default"), "cg_fov_default", 80.0f, 65.0f, 120.0f,
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
