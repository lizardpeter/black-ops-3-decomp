// Minimal stand-in for the Xbox GDK's xgameruntime.dll, for the offline/preservation build on non-GDK hosts.
//
// The Store exe loads this with LoadLibraryExA("xgameruntime.dll", 0, LOAD_LIBRARY_SEARCH_SYSTEM32) (14291FC80)
// and resolves five entry points by name (14291FA64). On Windows/Xbox this DLL is the GDK runtime; it does not
// exist elsewhere, so WinMain aborts with "XGameRuntime failed". This stub lets initialization report success so
// startup continues, WITHOUT touching the game executable (so its self-integrity check still sees an unmodified
// image). It fabricates no user, licence, entitlement or online result: InitializeApi* just succeed, and the API
// dispatcher QueryApiImpl reports "not implemented" so individual GDK features degrade rather than run.
//
// This is a first, deliberately small stub: it answers whether the untouched exe starts past the GDK gate. How
// much of the GDK API surface a fuller offline build needs is tracked in docs/native-launch.md.
#define WIN32_LEAN_AND_MEAN
using HRESULT = long;
using ULONGLONG = unsigned long long;
constexpr HRESULT S_OK = 0;
constexpr HRESULT E_NOTIMPL = (HRESULT)0x80004001;

extern "C" int __stdcall _DllMainCRTStartup(void *, unsigned int, void *) { return 1; }

// InitializeApiImpl(version, flags) / InitializeApiImplEx(a, b, flags): GDK bring-up. Report success without
// standing up any Xbox service.
extern "C" __declspec(dllexport) HRESULT InitializeApiImpl(ULONGLONG, ULONGLONG) { return S_OK; }
extern "C" __declspec(dllexport) HRESULT InitializeApiImplEx(ULONGLONG, ULONGLONG, ULONGLONG) { return S_OK; }
extern "C" __declspec(dllexport) void UninitializeApiImpl() {}

// XErrorReport(code, message): the runtime's error sink. Swallow it.
extern "C" __declspec(dllexport) void XErrorReport(unsigned int, const char *) {}

// QueryApiImpl(apiId, iid, out): the GDK's "give me interface X" dispatcher. Report not-implemented and clear the
// out pointer if one was passed, so callers that check the HRESULT take their unavailable path instead of calling
// through an uninitialized table. (The exact signature is a GDK internal; three register args cover what the
// Store build passes.)
extern "C" __declspec(dllexport) HRESULT QueryApiImpl(ULONGLONG, ULONGLONG, void **out)
{
    if (out) *out = nullptr;
    return E_NOTIMPL;
}
