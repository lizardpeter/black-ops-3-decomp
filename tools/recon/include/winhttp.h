// The WinHTTP declarations the reconstruction uses.
//
// Build environment, not game source. The original includes the Windows SDK's winhttp.h; these are the same
// declarations, trimmed. In the hybrid build each function resolves to the original's import address table entry.
#pragma once

#include <windows.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void *HINTERNET;
typedef unsigned long long DWORD_PTR;
typedef void (*WINHTTP_STATUS_CALLBACK)(HINTERNET hInternet, DWORD_PTR dwContext, DWORD dwInternetStatus,
                                        void *lpvStatusInformation, DWORD dwStatusInformationLength);

#define WINHTTP_ACCESS_TYPE_AUTOMATIC_PROXY 4
#define WINHTTP_FLAG_ASYNC 0x10000000
#define WINHTTP_FLAG_SECURE_DEFAULTS 0x30000000
#define WINHTTP_OPTION_SECURE_PROTOCOLS 84
#define WINHTTP_FLAG_SECURE_PROTOCOL_TLS1_2 0x00000800
#define WINHTTP_FLAG_SECURE_PROTOCOL_TLS1_3 0x00002000
#define WINHTTP_CALLBACK_FLAG_ALL_NOTIFICATIONS 0xFFFFFFFF
#define WINHTTP_INVALID_STATUS_CALLBACK ((WINHTTP_STATUS_CALLBACK)(-1LL))

HINTERNET WinHttpOpen(const wchar_t *pszAgentW, DWORD dwAccessType, const wchar_t *pszProxyW,
                      const wchar_t *pszProxyBypassW, DWORD dwFlags);
BOOL WinHttpSetOption(HINTERNET hInternet, DWORD dwOption, void *lpBuffer, DWORD dwBufferLength);
WINHTTP_STATUS_CALLBACK WinHttpSetStatusCallback(HINTERNET hInternet, WINHTTP_STATUS_CALLBACK lpfnInternetCallback,
                                                 DWORD dwNotificationFlags, DWORD_PTR dwReserved);
BOOL WinHttpCloseHandle(HINTERNET hInternet);

#ifdef __cplusplus
}
#endif
