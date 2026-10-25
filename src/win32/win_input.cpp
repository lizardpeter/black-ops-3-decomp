// Mouse input. Names follow the IW lineage (CoD4's win32/win_input.cpp: IN_MouseMove, IN_RecenterMouse); the raw
// input thread is BO3's own (records/names.tsv has the evidence for each address).
//
// BO3 reads the mouse with raw input, not from the cursor: a thread of its own (sub_1423F4B70, Sys_CreateThread
// index 0x16) owns a message-only window that the renderer's window setup (141DAB250) registers for the mouse with
// RIDEV_INPUTSINK, and adds every report's movement to two counters; IN_MouseMove takes them once a frame and hands
// them to CL_MouseEvent. docs/input.md.

#include <windows.h>

#include "universal/dvar.h"
#include "gfx_d3d/r_dvars.h"
#include "win32/win_input.h"

extern const dvar_t *r_fullscreen;

// Client side of the input device switch (keyboard and mouse vs. gamepad). Names unknown.
struct InputDeviceState
{
	int controllerIndex;
	int localClientNum;
	int localClientNum2;
	int unknown0C;
	int unknown10;
	int lastDevice;      // 1 = keyboard and mouse
	int lastDeviceTime;  // Sys_Milliseconds of the last switch
	int unknown1C;
	int unknown20;
};
static_assert(sizeof(InputDeviceState) == 0x24, "InputDeviceState");

extern InputDeviceState cl_inputDevice[];
extern int cl_inputDeviceController;  // the controller index keyboard and mouse input belongs to
extern int unk_1494B2DC8;             // compared with 2 before the device-switch notification; meaning unknown
extern unsigned int com_sessionModeState;  // low 4 bits (signed): the session mode
struct SessionModeInfo
{
	int unknown00;  // == 1 enables IN_MouseMove's device-switch notification
	int unknown04[5];
};
extern SessionModeInfo com_sessionModeInfo[];  // one per session mode

int CL_MouseEvent(int localClientNum, int x, int y, int dx, int dy);
void sub_1422081C0(int controllerIndex, bool usingKeyboardMouse);
int sub_141F01050(int localClientNum);
void sub_141720810(int localClientNum, int mode);
char *CG_GetPredictedPlayerState(int localClientNum);

static inline int Com_SessionMode_GetMode()
{
	return (int)(com_sessionModeState << 28) >> 28;
}

// 1423BD4C0  win32/win_input.cpp
// Once a frame from IN_Frame, while the window is active. Nothing happens while the system is suspended or another
// window is in front, and then the counters are left as they are: movement made in the background is taken on the
// first frame the game is in front again (B0040). In exclusive fullscreen the cursor is kept inside the window first.
void IN_MouseMove()
{
	if (win_suspended)
		return;
	if (GetForegroundWindow() != win_hWnd)
		return;
	POINT cursor;
	GetCursorPos(&cursor);
	if (Dvar_GetInt(r_fullscreen) == 1)
	{
		RECT rect;
		GetWindowRect(win_hWnd, &rect);
		bool clamped = false;
		if (cursor.x < rect.left)
		{
			cursor.x = rect.left;
			clamped = true;
		}
		else if (cursor.x >= rect.right)
		{
			cursor.x = rect.right - 1;
			clamped = true;
		}
		if (cursor.y < rect.top)
		{
			cursor.y = rect.top;
			clamped = true;
		}
		else if (cursor.y >= rect.bottom)
		{
			cursor.y = rect.bottom - 1;
			clamped = true;
		}
		if (clamped)
			SetCursorPos(cursor.x, cursor.y);
	}
	int dx = __atomic_exchange_n(&win_rawMouseDx, 0, __ATOMIC_SEQ_CST);
	int dy = __atomic_exchange_n(&win_rawMouseDy, 0, __ATOMIC_SEQ_CST);
	if (dx || dy)
	{
		int controller = cl_inputDeviceController;
		InputDeviceState *device = &cl_inputDevice[controller];
		if (device->lastDevice != 1)
		{
			int now = Sys_Milliseconds();
			if (device->lastDeviceTime + 200 <= now)
			{
				device->lastDeviceTime = now;
				int previous = device->lastDevice;
				device->lastDevice = 1;
				if (previous)
				{
					sub_1422081C0(controller, false);
				}
				else
				{
					sub_1422081C0(controller, true);
					if (unk_1494B2DC8 != 2)
					{
						int localClientNum = device->controllerIndex == controller ? device->localClientNum : -1;
						int mode = 0;
						if (Com_SessionMode_GetMode() == 2 && sub_141F01050(localClientNum)
						    && com_sessionModeInfo[Com_SessionMode_GetMode()].unknown00 == 1)
						{
							char *ps = CG_GetPredictedPlayerState(controller);
							mode = ps && (*(unsigned long long *)(ps + 0x10) & 0x20000000000000ull) ? 1 : 2;
						}
						sub_141720810(localClientNum, mode);
					}
				}
			}
		}
	}
	win_lastCursorPos = cursor;
	ScreenToClient(win_hWnd, &cursor);
	win_mouseEventResult = CL_MouseEvent(0, cursor.x, cursor.y, dx, dy);
	if (win_mouseEventResult && (dx || dy))
	{
		IN_RecenterMouse();
		win_lastCursorPos.x = win_windowCenterX;
		win_lastCursorPos.y = win_windowCenterY;
	}
}

// 1423F4B70  win32/win_input.cpp
// The raw input thread (Sys_CreateThread index 0x16). It creates the message-only window the mouse is registered
// to, then polls: every report waiting in the queue is read with GetRawInputBuffer and its movement added to the
// counters, then it sleeps 1 ms (timeGetTime resolution is set to 1 ms at start-up, 1423BF710) and looks again, so
// a report waits up to a millisecond or more before IN_MouseMove can take it (B0041). Every report's lLastX/lLastY
// is added whatever its usFlags say, so an absolute device (tablet, remote desktop, some virtual machines) adds
// screen coordinates as if they were movement (B0042); the counters are 32-bit. Shutdown sets the quit flag and
// waits for the thread to clear it.
void sub_1423F4B70(unsigned int threadContext)
{
	win_hRawInputWnd = CreateWindowExA(0, "CoDBlackOpsInputs", "", 0, 0, 0, 0, 0, HWND_MESSAGE, nullptr, win_hInstance,
	                                   nullptr);
	do
	{
		UINT size = 0x400;
		int count = (int)GetRawInputBuffer(win_rawInputBuffer, &size, sizeof(RAWINPUTHEADER));
		while (count > 0)
		{
			RAWINPUT *raw = win_rawInputBuffer;
			for (;;)
			{
				if (raw->header.dwType == RIM_TYPEMOUSE)
				{
					__atomic_fetch_add(&win_rawMouseDx, raw->data.mouse.lLastX, __ATOMIC_SEQ_CST);
					__atomic_fetch_add(&win_rawMouseDy, raw->data.mouse.lLastY, __ATOMIC_SEQ_CST);
				}
				if (--count <= 0)
					break;
				raw = (RAWINPUT *)(((unsigned long long)raw + raw->header.dwSize + 7) & ~7ull);
			}
			count = (int)GetRawInputBuffer(win_rawInputBuffer, &size, sizeof(RAWINPUTHEADER));
		}
		Sleep(1);
	} while (!sys_rawInputThreadQuit);
	while (!sys_rawInputThreadQuit)
		Sleep(0);
	sys_threadHandle[0x16] = nullptr;
	sys_threadFunc[0x16] = nullptr;
	sys_rawInputThreadQuit = false;
}

// 1423F49B0  win32/win_input.cpp
// The window thread (Sys_CreateThread index 0x15). BO3 gives its window a thread of its own: this creates it and
// runs its message loop, so the window procedure (keys, mouse buttons, focus) and every message the renderer sends it
// (SendMessageA 0x8042 swap chain, 0x8043 Present, 0x8044 fullscreen state) run here. The loop polls: it handles
// whatever is waiting for the window, then sleeps 1 ms before looking again. A key or button press therefore waits
// up to about a millisecond before the window procedure queues it for the game, and every Present the render thread
// makes waits for this thread to wake up before it can run (B0043). It also sets the cursor's show count from two
// flags each pass. WM_QUIT sets sys_quitEvent and ends the loop; shutdown sets sys_windowThreadQuit and waits for the
// thread to clear it.
void sub_1423F49B0(unsigned int threadContext)
{
	HWND hWnd = CreateWindowExA(0, "CoDBlackOps", "", win_style, win_x, win_y, win_width, win_height, nullptr, nullptr,
	                            win_hInstance, nullptr);
	win_hWnd = hWnd;
	bool quit = false;
	for (;;)
	{
		MSG msg;
		while (PeekMessageA(&msg, hWnd, 0, 0, PM_REMOVE | PM_NOYIELD))
		{
			if (msg.message == WM_QUIT)
			{
				quit = true;
				SetEvent(sys_quitEvent);
			}
			win_lastMessageTime = msg.time;
			TranslateMessage(&msg);
			DispatchMessageA(&msg);
			hWnd = win_hWnd;
		}
		Sleep(1);
		int target;
		BOOL show;
		if (!win_showCursor && !unk_1490E7E44)
		{
			target = -1;
			show = 0;
		}
		else
		{
			target = 0;
			show = 1;
		}
		for (int count = ShowCursor(show); count != target; count = ShowCursor(count < target))
		{
		}
		if (quit || sys_windowThreadQuit)
			break;
		hWnd = win_hWnd;
	}
	while (!sys_windowThreadQuit)
		Sleep(0);
	sys_threadHandle[0x15] = nullptr;
	sys_threadFunc[0x15] = nullptr;
	sys_windowThreadQuit = false;
}
