// Offline package failure boundaries (P0001). Ported from ghosts-decomp enhanced/offline/egress.cpp (its P0011).
// tools/offline/package.py points the Store exe's original IAT slots for network, HTTP, process launch and dynamic
// loading at these adapters; the slots keep their addresses. Win64 machine-ABI adapters: extra arguments ignored.
extern "C" __declspec(dllimport) void SetLastError(unsigned int error);
extern "C" __declspec(dllimport) void WSASetLastError(int error);
extern "C" __declspec(dllimport) void *GetProcAddress(void *, const char *);
extern "C" __declspec(dllimport) void *LoadLibraryA(const char *);
extern "C" __declspec(dllimport) void *LoadLibraryW(const wchar_t *);
extern "C" __declspec(dllimport) void *LoadLibraryExA(const char *, void *, unsigned int);
extern "C" __declspec(dllimport) void *LoadLibraryExW(const wchar_t *, void *, unsigned int);
extern "C" __declspec(dllimport) unsigned int GetModuleFileNameW(void *, wchar_t *, unsigned int);

#define T7_EXPORT extern "C" __declspec(dllexport)

namespace
{
unsigned int Lower(unsigned int c) { return c >= 'A' && c <= 'Z' ? c + 32 : c; }
template <class C> bool Same(const C *a, const char *b)
{
    while (*a && *b && Lower(*a) == Lower(*b)) { ++a; ++b; }
    return !*a && !*b;
}
// Modules the offline package never loads dynamically: the GDK runtime (Xbox Live, Store, users), the HTTP and
// socket stacks, and the GDK networking/party SDKs that ship beside the exe.
template <class C> bool Blocked(const C *path)
{
    if (!path) return false;
    const C *base = path;
    for (const C *p = path; *p; ++p) if (*p == '/' || *p == '\\') base = p + 1;
    const char *names[] = {"xgameruntime", "xcurl", "winhttp", "wininet", "urlmon", "ws2_32",
                           "playfabmultiplayergdk", "party", "partyxboxlive"};
    for (const char *name : names)
    {
        const C *p = base; const char *q = name;
        while (*p && *q && Lower(*p) == Lower(*q)) { ++p; ++q; }
        if (!*q && (!*p || Same(p, ".dll"))) return true;
    }
    return false;
}
void Denied() { SetLastError(5); } // ERROR_ACCESS_DENIED
}

T7_EXPORT unsigned long long T7DenyNull() { Denied(); return 0; }
T7_EXPORT unsigned long long T7DenyMinusOne() { Denied(); return ~0ULL; }
T7_EXPORT int T7DenyStatus() { Denied(); return 5; }
T7_EXPORT int T7DenyCurl() { Denied(); return 2; }      // CURLE_FAILED_INIT
T7_EXPORT int T7DenyCurlMulti() { Denied(); return 4; } // CURLM_INTERNAL_ERROR
T7_EXPORT const char *T7OfflineErrorText() { return "Network disabled by offline build"; }
T7_EXPORT unsigned long long T7DenySocket() { WSASetLastError(10013); return ~0ULL; } // WSAEACCES, INVALID_SOCKET/-1
T7_EXPORT void *T7DenyDns() { WSASetLastError(10013); return nullptr; }
T7_EXPORT int T7DenyAddrInfo(const char *, const char *, const void *, void **result)
{
    if (result) *result = nullptr;
    WSASetLastError(10013);
    return 10013;
}
T7_EXPORT int T7DenyCom(const void *, void *, unsigned int, const void *, void **result)
{
    if (result) *result = nullptr;
    Denied();
    return (int)0x80070005; // E_ACCESSDENIED
}
T7_EXPORT int T7DenyEventRegister(const void *, void *, void *, unsigned long long *handle)
{
    if (handle) *handle = 0;
    Denied();
    return 5;
}
T7_EXPORT void *T7OfflineLoadLibraryA(const char *path)
{
    if (Blocked(path)) { Denied(); return nullptr; }
    return LoadLibraryA(path);
}
T7_EXPORT void *T7OfflineLoadLibraryW(const wchar_t *path)
{
    if (Blocked(path)) { Denied(); return nullptr; }
    return LoadLibraryW(path);
}
T7_EXPORT void *T7OfflineLoadLibraryExA(const char *path, void *file, unsigned int flags)
{
    if (Blocked(path)) { Denied(); return nullptr; }
    return LoadLibraryExA(path, file, flags);
}
T7_EXPORT void *T7OfflineLoadLibraryExW(const wchar_t *path, void *file, unsigned int flags)
{
    if (Blocked(path)) { Denied(); return nullptr; }
    return LoadLibraryExW(path, file, flags);
}
T7_EXPORT void *T7OfflineGetProcAddress(void *module, const char *name)
{
    wchar_t path[512];
    const unsigned int count = GetModuleFileNameW(module, path, 512);
    if (!count || count >= 512 || Blocked(path) ||
        ((unsigned long long)name > 0xFFFF && (Same(name, "RoGetActivationFactory") || Same(name, "RoActivateInstance"))))
    {
        Denied();
        return nullptr;
    }
    // A second dynamic lookup of the loader/process APIs stays inside the same boundary.
    if ((unsigned long long)name > 0xFFFF)
    {
        if (Same(name, "GetProcAddress")) return (void *)&T7OfflineGetProcAddress;
        if (Same(name, "LoadLibraryA")) return (void *)&T7OfflineLoadLibraryA;
        if (Same(name, "LoadLibraryW")) return (void *)&T7OfflineLoadLibraryW;
        if (Same(name, "LoadLibraryExA")) return (void *)&T7OfflineLoadLibraryExA;
        if (Same(name, "LoadLibraryExW")) return (void *)&T7OfflineLoadLibraryExW;
        if (Same(name, "CreateProcessA") || Same(name, "CreateProcessW")) return (void *)&T7DenyNull;
        if (Same(name, "ShellExecuteA") || Same(name, "ShellExecuteW")) return (void *)&T7DenyStatus;
    }
    return GetProcAddress(module, name);
}
