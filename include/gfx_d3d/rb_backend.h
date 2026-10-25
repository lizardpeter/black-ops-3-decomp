// gfx_d3d/rb_backend.h (reconstructed: only what reconstructed code uses so far)
#pragma once

// The frontend data the render thread is drawing (one of the two 0xF9760-byte buffers R_BeginFrame flips between),
// set by 141D470F0 from what R_EndFrame published. Offsets used: +0xF6568 the last scene's index, +0xF656C the
// scene count, +0xF6570 the scenes (viewInfo, 0xD5F60 bytes each).
extern char *backEndData;                 // 1482808D0
extern char gfxCmdBufSourceState[];       // 14A3240D0, the render thread's source state (gfx_d3d/r_state.h)
extern int dword_1486BEEA0;               // 2 once the renderer is up (141DAD840); scenes draw through 141D4E220
extern unsigned short word_1486F0DA4;     // the technique 141DEECD0 starts each scene with

enum
{
	FRONTEND_LAST_SCENE = 0xF6568,
	FRONTEND_SCENE_COUNT = 0xF656C,
	FRONTEND_SCENES = 0xF6570,
	VIEW_INFO_SIZE = 0xD5F60,
	VIEW_INFO_INPUT = 0x1430,         // the scene's 0x1960-byte input block
	VIEW_INFO_DRAW_PREVIOUS = 0xB24C8, // char: draw the scene before this one too
};

void sub_141D4E220(char *source, char *frontEnd, char *viewInfo);
void sub_141DF1770(char *source, char *frontEnd, void *input);
void sub_141DEECD0(char *source, unsigned short technique);
void sub_141D46D30();
