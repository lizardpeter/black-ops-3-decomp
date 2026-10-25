// P0018 (moved) and P0020: the frame-latency wait comes before the frame's second event loop, so keys and mouse
// buttons pressed during it reach this frame's commands, like the mouse.
//
// Com_Frame (1422174C0): client frame (141402E70), sub_1413ED0D0, Com_EventLoop again (key and button events into
// CL_KeyEvent and the bindings' kbuttons), the command buffer, the command step (141403040: commands built and sent),
// then SCR_UpdateScreen (14148CF00), where in game the cgame's draw calls 1413BFDE0: IN_Frame takes the mouse and
// 1413BBF50 builds the command the frame is drawn from. The original never waits between the event loop and that
// command. With the frame-latency wait inside IN_Frame (P0018 as first ported) the mouse was read right after the
// wait but keys pressed during it waited a frame. Here the wait runs at the start of sub_1413ED0D0 instead: keys
// and mouse are both taken after it, by the original's own code in its own order; nothing is dispatched mid-frame
// (Ghosts' P0009 has to choose which keys are safe; here none needs choosing). The mouse is now read after the
// event loop, the command step and the start of the draw rather than straight after the wait: that time is not
// measured yet. sub_1413ED0D0 also runs once at shutdown, where the wait finds at most the last frame's present.

#include "client/cl_keys.h"
#include "../gfx_d3d/r_flip.h"

void sub_1413ED0D0()
{
	R_WaitForFrameLatency();
	int *modified = key_bindingsModified;
	for (int localClientNum = 0; localClientNum < MAX_LOCAL_CLIENTS; localClientNum++, modified += 0x650)
	{
		if (*modified != 1)
			continue;
		*modified = 0;
		char name[0x104];
		const char *formatted = va("%s_%d", "bindings", localClientNum);
		if (!formatted)
		{
			name[0] = 0;
		}
		else
		{
			unsigned long long i = 0;
			for (;;)
			{
				char c = formatted[i];
				name[i] = c;
				if (!c)
					break;
				if (++i == sizeof(name))
				{
					name[sizeof(name) - 1] = 0;
					break;
				}
			}
		}
		sub_1423B4570(name, sizeof(name));
		sub_1413ECF90(localClientNum, name);
	}
}
