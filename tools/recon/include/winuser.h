// user32 declarations for the window thread, the swap chain and the message pumps (winuser.h).
//
// Build environment, not game source: the Windows SDK's declarations, trimmed to what the reconstruction uses. In the
// hybrid build each function resolves to the original's import address table entry. Kept apart from windows.h, which
// the SDK's windows.h would pull this in from, so code that needs these says so.
#pragma once

#include <windows.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void *HANDLE;
typedef struct HMENU__ *HMENU;
typedef struct HMONITOR__ *HMONITOR;
typedef unsigned short USHORT;

typedef struct tagMSG
{
	HWND hwnd;
	UINT message;
	WPARAM wParam;
	LPARAM lParam;
	DWORD time;
	POINT pt;
	DWORD lPrivate;
} MSG;

typedef struct tagMONITORINFO
{
	DWORD cbSize;
	RECT rcMonitor;
	RECT rcWork;
	DWORD dwFlags;
} MONITORINFO;

typedef struct tagRAWINPUTDEVICE
{
	USHORT usUsagePage;
	USHORT usUsage;
	DWORD dwFlags;
	HWND hwndTarget;
} RAWINPUTDEVICE;

#define SM_CXSCREEN 0
#define SM_CYSCREEN 1
#define WM_QUIT 0x0012
#define PM_NOREMOVE 0x0000
#define PM_REMOVE 0x0001
#define PM_NOYIELD 0x0002
#define RIDEV_INPUTSINK 0x00000100
#define HID_USAGE_PAGE_GENERIC 0x01
#define HID_USAGE_GENERIC_MOUSE 0x02

int GetSystemMetrics(int nIndex);
BOOL GetMonitorInfoA(HMONITOR hMonitor, MONITORINFO *lpmi);
BOOL RegisterRawInputDevices(const RAWINPUTDEVICE *pRawInputDevices, UINT uiNumDevices, UINT cbSize);
long long SendMessageA(HWND hWnd, UINT Msg, WPARAM wParam, LPARAM lParam);
BOOL PeekMessageA(MSG *lpMsg, HWND hWnd, UINT wMsgFilterMin, UINT wMsgFilterMax, UINT wRemoveMsg);
BOOL GetMessageA(MSG *lpMsg, HWND hWnd, UINT wMsgFilterMin, UINT wMsgFilterMax);
BOOL TranslateMessage(const MSG *lpMsg);
long long DispatchMessageA(const MSG *lpMsg);
HWND CreateWindowExA(DWORD dwExStyle, const char *lpClassName, const char *lpWindowName, DWORD dwStyle, int X, int Y,
                     int nWidth, int nHeight, HWND hWndParent, HMENU hMenu, HINSTANCE hInstance, void *lpParam);

// kernel32
void Sleep(DWORD dwMilliseconds);
BOOL SetEvent(HANDLE hEvent);
BOOL CloseHandle(HANDLE hObject);
DWORD WaitForSingleObjectEx(HANDLE hHandle, DWORD dwMilliseconds, BOOL bAlertable);
HINSTANCE GetModuleHandleA(const char *lpModuleName);
void *GetProcAddress(HINSTANCE hModule, const char *lpProcName);

#define WAIT_OBJECT_0 0x00000000
#define WAIT_IO_COMPLETION 0x000000C0
#define WAIT_TIMEOUT 0x00000102

#ifdef __cplusplus
}
#endif
