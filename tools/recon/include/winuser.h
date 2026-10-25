// More user32 and kernel32 declarations, for the swap chain's creation and resize and the present (winuser.h).
//
// Build environment, not game source: the Windows SDK's declarations, trimmed to what the reconstruction uses. In the
// hybrid build each function resolves to the original's import address table entry. windows.h has the common ones;
// these are the renderer's.
#pragma once

#include <windows.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct HMONITOR__ *HMONITOR;

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
#define PM_NOREMOVE 0x0000
#define RIDEV_INPUTSINK 0x00000100
#define HID_USAGE_PAGE_GENERIC 0x01
#define HID_USAGE_GENERIC_MOUSE 0x02
#define WAIT_OBJECT_0 0x00000000
#define WAIT_IO_COMPLETION 0x000000C0

int GetSystemMetrics(int nIndex);
BOOL GetMonitorInfoA(HMONITOR hMonitor, MONITORINFO *lpmi);
BOOL RegisterRawInputDevices(const RAWINPUTDEVICE *pRawInputDevices, UINT uiNumDevices, UINT cbSize);
long long SendMessageA(HWND hWnd, UINT Msg, WPARAM wParam, LPARAM lParam);
BOOL GetMessageA(MSG *lpMsg, HWND hWnd, UINT wMsgFilterMin, UINT wMsgFilterMax);
BOOL CloseHandle(HANDLE hObject);
DWORD WaitForSingleObjectEx(HANDLE hHandle, DWORD dwMilliseconds, BOOL bAlertable);

#ifdef __cplusplus
}
#endif
