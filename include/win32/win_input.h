// win32/win_input.h (reconstructed: only what reconstructed code uses so far)
#pragma once

#include <windows.h>

// Window globals (IW's g_wv, kept as separate symbols until the struct is laid out).
extern HWND win_hWnd;            // the game window
extern HWND win_hRawInputWnd;    // the raw input thread's message-only window
extern HINSTANCE win_hInstance;
extern int win_suspended;        // set by the window procedure on PBT_APMSUSPEND, cleared on resume
extern int win_mouseEventResult; // CL_MouseEvent's last result

// Mouse movement in device counts, added by the raw input thread and taken by IN_MouseMove.
extern int win_rawMouseDy;
extern int win_rawMouseDx;
extern RAWINPUT win_rawInputBuffer[];  // 0x400 bytes, the raw input thread's GetRawInputBuffer buffer

extern POINT win_lastCursorPos;  // screen position of the cursor at the last IN_MouseMove
extern int win_windowCenterY;    // IN_RecenterMouse's target
extern int win_windowCenterX;

// Sys_CreateThread's slots (thread index 0x16 is the raw input thread).
extern HANDLE sys_threadHandle[];
extern void *sys_threadFunc[];
extern volatile bool sys_rawInputThreadQuit;  // set at shutdown; the thread clears it when it has stopped
extern volatile bool sys_windowThreadQuit;    // the same for the window thread
extern HANDLE sys_quitEvent;                  // set by the window thread on WM_QUIT; Sys_GetEvent quits on it
extern DWORD win_lastMessageTime;             // MSG.time of the last message the window thread dispatched
extern int win_showCursor;                    // the window thread shows the cursor while this or unk_1490E7E44 is set
extern int unk_1490E7E44;
extern DWORD win_style;                       // CreateWindowExA arguments, set up by 141DAB970
extern int win_x;
extern int win_y;
extern int win_width;
extern int win_height;

// Sys_Milliseconds, inlined in the Store build (the name records/names.tsv gives 1425E7D70 by matching is not it:
// that is a four-argument function).
extern int sys_timeInitialized;
extern int sys_timeBase;

static inline int Sys_Milliseconds()
{
	if (!sys_timeInitialized)
	{
		sys_timeBase = (int)timeGetTime();
		sys_timeInitialized = 1;
	}
	return (int)timeGetTime() - sys_timeBase;
}

void IN_RecenterMouse();
void IN_MouseMove();
void sub_1423F4B70(unsigned int threadContext);
void sub_1423F49B0(unsigned int threadContext);
