// The render thread's 3D scenes. Original function name unknown; source path assumed from the engine lineage (IW's
// rb_backend.cpp draws the frame on the render thread). docs/late-latch.md, "The path", step 7.

#include "gfx_d3d/rb_backend.h"

#define T7_SOURCE "gfx_d3d/rb_backend.cpp"
#include <t7_static.h>

static void RB_DrawScene(char *frontEnd, char *viewInfo)
{
	if (dword_1486BEEA0)
	{
		sub_141D4E220(gfxCmdBufSourceState, frontEnd, viewInfo);
		return;
	}
	sub_141DF1770(gfxCmdBufSourceState, frontEnd, *(void **)(viewInfo + VIEW_INFO_INPUT));
	sub_141DEECD0(gfxCmdBufSourceState, word_1486F0DA4);
}

// 141D46D30  gfx_d3d/rb_backend.cpp
// Draws the frame's last scene, and the one before it as well when the last asks for that (+0xB24C8): during play
// through 141D4E220, before the renderer is up by setting up the source state and the first technique only.
void sub_141D46D30()
{
	char *frontEnd = backEndData;
	if (!*(int *)(frontEnd + FRONTEND_SCENE_COUNT))
		return;
	unsigned int last = *(unsigned int *)(frontEnd + FRONTEND_LAST_SCENE);
	char *viewInfo = *(char **)(frontEnd + FRONTEND_SCENES) + (unsigned long long)last * VIEW_INFO_SIZE;
	if (!*(char *)(viewInfo + VIEW_INFO_DRAW_PREVIOUS))
	{
		RB_DrawScene(frontEnd, viewInfo);
		return;
	}
	long long index = (int)last;
	long long first = (int)(last - 1);
	if (index < first)
		return;
	long long offset = index * VIEW_INFO_SIZE;
	for (long long count = index - first + 1; count; count--, offset -= VIEW_INFO_SIZE)
		RB_DrawScene(frontEnd, *(char **)(frontEnd + FRONTEND_SCENES) + offset);
}
