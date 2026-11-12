// T7 enhanced offline WinHTTP boundary for the 16 exact Store imports.
// Never creates network handles, starts a request or pretends to authenticate.
// This is app-local and suitable for PRIVATE offline Wine experiments only.
// It is not a generic system winhttp.dll replacement.
#define T7_EXPORT extern "C" __declspec(dllexport)
using DWORD = unsigned long;
using WORD = unsigned short;
using HINTERNET = void *;
using LPCWSTR = const wchar_t *;
using BOOL = int;
using DWORD_PTR = unsigned long long;
extern "C" __declspec(dllimport) void SetLastError(DWORD);
extern "C" int __stdcall _DllMainCRTStartup(void *, unsigned int, void *) { return 1; }

namespace {
void Offline() { SetLastError(12029); } // ERROR_WINHTTP_CANNOT_CONNECT
BOOL Fail() { Offline(); return 0; }
HINTERNET FailHandle() { Offline(); return nullptr; }
}

T7_EXPORT HINTERNET WinHttpOpen(LPCWSTR, DWORD, LPCWSTR, LPCWSTR, DWORD)
{ return FailHandle(); }
T7_EXPORT HINTERNET WinHttpConnect(HINTERNET, LPCWSTR, WORD, DWORD)
{ return FailHandle(); }
T7_EXPORT HINTERNET WinHttpOpenRequest(HINTERNET, LPCWSTR, LPCWSTR, LPCWSTR,
                                      LPCWSTR, const LPCWSTR *, DWORD)
{ return FailHandle(); }
T7_EXPORT BOOL WinHttpCloseHandle(HINTERNET)
{ SetLastError(6); return 0; } // ERROR_INVALID_HANDLE (no handle was allocated)
T7_EXPORT BOOL WinHttpCrackUrl(LPCWSTR, DWORD, DWORD, void *)
{ return Fail(); }
T7_EXPORT BOOL WinHttpAddRequestHeaders(HINTERNET, LPCWSTR, DWORD, DWORD)
{ return Fail(); }
T7_EXPORT BOOL WinHttpSendRequest(HINTERNET, LPCWSTR, DWORD, void *,
                                 DWORD, DWORD, DWORD_PTR)
{ return Fail(); }
T7_EXPORT BOOL WinHttpReceiveResponse(HINTERNET, void *)
{ return Fail(); }
T7_EXPORT BOOL WinHttpQueryDataAvailable(HINTERNET, DWORD *bytes)
{ if (bytes) *bytes = 0; return Fail(); }
T7_EXPORT BOOL WinHttpReadData(HINTERNET, void *, DWORD, DWORD *bytes)
{ if (bytes) *bytes = 0; return Fail(); }
T7_EXPORT BOOL WinHttpWriteData(HINTERNET, const void *, DWORD, DWORD *bytes)
{ if (bytes) *bytes = 0; return Fail(); }
T7_EXPORT BOOL WinHttpQueryHeaders(HINTERNET, DWORD, LPCWSTR, void *,
                                  DWORD *size, DWORD *)
{ if (size) *size = 0; return Fail(); }
T7_EXPORT BOOL WinHttpQueryOption(HINTERNET, DWORD, void *, DWORD *size)
{ if (size) *size = 0; return Fail(); }
T7_EXPORT BOOL WinHttpSetOption(HINTERNET, DWORD, void *, DWORD)
{ return Fail(); }
T7_EXPORT BOOL WinHttpSetTimeouts(HINTERNET, int, int, int, int)
{ return Fail(); }
T7_EXPORT void *WinHttpSetStatusCallback(HINTERNET, void *, DWORD, DWORD_PTR)
{ Offline(); return (void *)~0ULL; } // WINHTTP_INVALID_STATUS_CALLBACK
