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
typedef struct HMENU__ *HMENU;
typedef struct HINSTANCE__ *HMODULE;
typedef void *HANDLE;
typedef unsigned short USHORT;
typedef unsigned long ULONG;
typedef long long (*FARPROC)(void);

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

#define HWND_MESSAGE ((HWND)-3)

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

#define WM_QUIT 0x0012
#define PM_REMOVE 0x0001
#define PM_NOYIELD 0x0002
#define QS_ALLINPUT 0x04FF

// Raw input (winuser.h)
typedef struct tagRAWINPUTHEADER
{
	DWORD dwType;
	DWORD dwSize;
	HANDLE hDevice;
	WPARAM wParam;
} RAWINPUTHEADER;

typedef struct tagRAWMOUSE
{
	USHORT usFlags;
	union
	{
		ULONG ulButtons;
		struct
		{
			USHORT usButtonFlags;
			USHORT usButtonData;
		};
	};
	ULONG ulRawButtons;
	LONG lLastX;
	LONG lLastY;
	ULONG ulExtraInformation;
} RAWMOUSE;

typedef struct tagRAWINPUT
{
	RAWINPUTHEADER header;
	union
	{
		RAWMOUSE mouse;
		unsigned char raw[40];
	} data;
} RAWINPUT;

#define RIM_TYPEMOUSE 0
#define MOUSE_MOVE_ABSOLUTE 0x01
#define QS_RAWINPUT 0x0400
#define MWMO_INPUTAVAILABLE 0x0004
#define WAIT_TIMEOUT 0x102
#define WAIT_FAILED 0xFFFFFFFF

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
HWND CreateWindowExA(DWORD dwExStyle, const char *lpClassName, const char *lpWindowName, DWORD dwStyle, int X, int Y,
                     int nWidth, int nHeight, HWND hWndParent, HMENU hMenu, HINSTANCE hInstance, void *lpParam);
UINT GetRawInputBuffer(RAWINPUT *pData, UINT *pcbSize, UINT cbSizeHeader);
void Sleep(DWORD dwMilliseconds);
DWORD timeGetTime(void);
HMODULE GetModuleHandleA(const char *lpModuleName);
FARPROC GetProcAddress(HMODULE hModule, const char *lpProcName);
BOOL PeekMessageA(MSG *lpMsg, HWND hWnd, UINT wMsgFilterMin, UINT wMsgFilterMax, UINT wRemoveMsg);
BOOL TranslateMessage(const MSG *lpMsg);
long long DispatchMessageA(const MSG *lpMsg);
BOOL SetEvent(HANDLE hEvent);

#ifdef __cplusplus
}
#endif
