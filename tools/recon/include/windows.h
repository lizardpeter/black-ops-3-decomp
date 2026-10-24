// The few Win32 declarations the reconstruction uses (user32, kernel32).
//
// Build environment, not game source. The original includes the Windows SDK; these are the same declarations,
// trimmed. In the hybrid build each function resolves to the original's import address table entry.
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#ifndef NULL
#define NULL 0
#endif

typedef int BOOL;
typedef unsigned long DWORD;
typedef unsigned int UINT;
typedef long LONG;
typedef unsigned long long WPARAM;
typedef long long LPARAM;
typedef struct HWND__ *HWND;
typedef struct HINSTANCE__ *HINSTANCE;
typedef struct HHOOK__ *HHOOK;

typedef struct tagPOINT
{
	LONG x;
	LONG y;
} POINT;

typedef struct tagRECT
{
	LONG left;
	LONG top;
	LONG right;
	LONG bottom;
} RECT;

#define WM_LBUTTONDOWN 0x0201
#define MK_LBUTTON 0x0001

HWND GetForegroundWindow(void);
BOOL GetCursorPos(POINT *lpPoint);
BOOL SetCursorPos(int X, int Y);
BOOL ClipCursor(const RECT *lpRect);
int ShowCursor(BOOL bShow);
BOOL GetWindowRect(HWND hWnd, RECT *lpRect);
BOOL GetClientRect(HWND hWnd, RECT *lpRect);
BOOL ScreenToClient(HWND hWnd, POINT *lpPoint);
BOOL ClientToScreen(HWND hWnd, POINT *lpPoint);
BOOL PostMessageA(HWND hWnd, UINT Msg, WPARAM wParam, LPARAM lParam);
DWORD GetLastError(void);

#ifdef __cplusplus
}
#endif
