// P0013, P0014: mouse input and the window thread wake on input instead of polling, and the mouse counts only what
// was made while the game was in front (B0040-B0043). docs/input.md.
//
// - The raw input thread (P0013) waits for raw input instead of sleeping a millisecond between looks: it reads the
//   reports as soon as Windows has them. It counts relative reports only (absolute devices such as tablets, remote
//   desktop and some virtual machines send screen positions, not movement), in 64-bit counters, and only while the
//   game window is in front: movement made in the background is never counted, so nothing lands on the view when the
//   game comes back to the front. IN_MouseMove takes the counts every frame and throws them away when the game isn't
//   in front or the system is suspended, instead of leaving them for later.
// - The window thread (P0014) waits for messages instead of sleeping a millisecond between looks: key and button
//   presses reach the window procedure, and the render thread's Present and swap chain messages are handled, as
//   soon as they arrive. Its other work (the cursor's show count, the quit checks) still runs at least every
//   millisecond.
//
// Both waits use MsgWaitForMultipleObjectsEx, which the exe doesn't import: it is looked up in user32 when each
// thread starts. Without it each thread polls as the original does.

#include <windows.h>

#include "universal/dvar.h"
#include "gfx_d3d/r_dvars.h"
#include "win32/win_input.h"

extern const dvar_t *r_fullscreen;

struct InputDeviceState
{
	int controllerIndex;
	int localClientNum;
	int localClientNum2;
	int unknown0C;
	int unknown10;
	int lastDevice;
	int lastDeviceTime;
	int unknown1C;
	int unknown20;
};

extern InputDeviceState cl_inputDevice[];
extern int cl_inputDeviceController;
extern int unk_1494B2DC8;
extern unsigned int com_sessionModeState;
struct SessionModeInfo
{
	int unknown00;
	int unknown04[5];
};
extern SessionModeInfo com_sessionModeInfo[];

int CL_MouseEvent(int localClientNum, int x, int y, int dx, int dy);
void sub_1422081C0(int controllerIndex, bool usingKeyboardMouse);
int sub_141F01050(int localClientNum);
void sub_141720810(int localClientNum, int mode);
char *CG_GetPredictedPlayerState(int localClientNum);

static inline int Com_SessionMode_GetMode()
{
	return (int)(com_sessionModeState << 28) >> 28;
}

typedef DWORD (*MsgWaitForMultipleObjectsEx_t)(DWORD nCount, const HANDLE *pHandles, DWORD dwMilliseconds,
                                               DWORD dwWakeMask, DWORD dwFlags);

static MsgWaitForMultipleObjectsEx_t IN_FindMsgWait()
{
	HMODULE user32 = GetModuleHandleA("user32.dll");
	return user32 ? (MsgWaitForMultipleObjectsEx_t)GetProcAddress(user32, "MsgWaitForMultipleObjectsEx") : nullptr;
}

// Movement in device counts since IN_MouseMove last took it, counted by the raw input thread.
static long long s_rawDx;
static long long s_rawDy;

// Every report waiting for the raw input window: relative movement is counted while the game is in front.
void IN_ReadRawInput()
{
	UINT size = 0x400;
	int count;
	while ((count = (int)GetRawInputBuffer(win_rawInputBuffer, &size, sizeof(RAWINPUTHEADER))) > 0)
	{
		bool inFront = GetForegroundWindow() == win_hWnd;
		RAWINPUT *raw = win_rawInputBuffer;
		for (; count > 0; count--)
		{
			if (inFront && raw->header.dwType == RIM_TYPEMOUSE && !(raw->data.mouse.usFlags & MOUSE_MOVE_ABSOLUTE))
			{
				__atomic_fetch_add(&s_rawDx, (long long)raw->data.mouse.lLastX, __ATOMIC_RELAXED);
				__atomic_fetch_add(&s_rawDy, (long long)raw->data.mouse.lLastY, __ATOMIC_RELAXED);
			}
			raw = (RAWINPUT *)(((unsigned long long)raw + raw->header.dwSize + 7) & ~7ull);
		}
	}
}

// The counts since the last call, cleared; a frame can't plausibly hold 2^31 counts, so they are clamped, not wrapped.
void IN_TakeRawMouse(int *dx, int *dy)
{
	long long x = __atomic_exchange_n(&s_rawDx, 0, __ATOMIC_RELAXED);
	long long y = __atomic_exchange_n(&s_rawDy, 0, __ATOMIC_RELAXED);
	*dx = x > 0x7FFFFFFF ? 0x7FFFFFFF : x < -0x7FFFFFFF ? -0x7FFFFFFF : (int)x;
	*dy = y > 0x7FFFFFFF ? 0x7FFFFFFF : y < -0x7FFFFFFF ? -0x7FFFFFFF : (int)y;
}

void sub_1423F4B70(unsigned int threadContext)
{
	win_hRawInputWnd = CreateWindowExA(0, "CoDBlackOpsInputs", "", 0, 0, 0, 0, 0, HWND_MESSAGE, nullptr, win_hInstance,
	                                   nullptr);
	MsgWaitForMultipleObjectsEx_t wait = IN_FindMsgWait();
	do
	{
		IN_ReadRawInput();
		if (sys_rawInputThreadQuit)
			break;
		// wakes as soon as raw input is waiting; the timeout only bounds how long shutdown waits for this thread
		if (wait)
			wait(0, nullptr, 10, QS_RAWINPUT, MWMO_INPUTAVAILABLE);
		else
			Sleep(1);
	} while (!sys_rawInputThreadQuit);
	sys_threadHandle[0x16] = nullptr;
	sys_threadFunc[0x16] = nullptr;
	sys_rawInputThreadQuit = false;
}

// As the original, but the counts come from the 64-bit counters and are always taken: when the game isn't in front
// or the system is suspended they are thrown away.
void IN_MouseMove()
{
	int dx, dy;
	IN_TakeRawMouse(&dx, &dy);
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

void sub_1423F49B0(unsigned int threadContext)
{
	HWND hWnd = CreateWindowExA(0, "CoDBlackOps", "", win_style, win_x, win_y, win_width, win_height, nullptr, nullptr,
	                            win_hInstance, nullptr);
	win_hWnd = hWnd;
	MsgWaitForMultipleObjectsEx_t wait = IN_FindMsgWait();
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
		// wakes as soon as a message is posted or sent to this thread (input, the renderer's SendMessageA), and at
		// least every millisecond as the original's Sleep(1) did
		if (wait)
			wait(0, nullptr, 1, QS_ALLINPUT, 0);
		else
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
