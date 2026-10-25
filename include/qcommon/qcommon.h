// qcommon/qcommon.h (reconstructed: only what reconstructed code uses so far)
#pragma once

enum errorParm_t
{
	ERR_FATAL = 0,
	ERR_DROP = 1,
};

// 142210B90: BO3's Com_Error takes the source file and line first (both empty here: the Store build is a ship build)
void Com_Error_(const char *file, int line, errorParm_t code, const char *fmt, ...);
