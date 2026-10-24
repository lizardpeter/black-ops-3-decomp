// Demonware's WinHTTP worker (reconstructed: only what reconstructed code uses so far). The class and method names are
// the library's own log strings ("bdHTTPWorkerWinHTTPImpl::initializeWinHTTP"); there is no symbol build of this GDK
// variant, so the layout is only what the reconstructed methods use, and the prototypes are this reconstruction's.
#pragma once

#include <winhttp.h>

class bdHTTPWorkerWinHTTPImpl
{
public:
	bool initializeWinHTTP();
	static void WinHttpStatusCallback(HINTERNET handle, DWORD_PTR context, DWORD status, void *info, DWORD length);

	unsigned char m_unknown0[0x98];
	bool m_initialized; // 0x98
	HINTERNET m_session; // 0xA0
};
