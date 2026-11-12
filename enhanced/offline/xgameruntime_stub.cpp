// Non-vendor GDK shim for an unmodified T7 Store executable in an isolated Wine prefix.
// IMPORTANT: not an Xbox identity, entitlement, multiplayer, or license emulator.
// The Store binary requests these five exports through system32 LOAD_LIBRARY_SEARCH_SYSTEM32.
// Do not install this test DLL in a real Windows system directory.
#define T7_EXPORT extern "C" __declspec(dllexport)
using HRESULT = long;
using U64 = unsigned long long;
extern "C" __declspec(dllimport) void OutputDebugStringA(const char *);
extern "C" int T7DirectLoadStartupProfile();
static volatile unsigned int querySequence;
static volatile unsigned int errorSequence;
static volatile unsigned int initialized;

extern "C" int __stdcall _DllMainCRTStartup(void *, unsigned int, void *) { return 1; }

static void EmitQuery(U64 api)
{
    // Debug only; log bounded query IDs, not caller strings, names, tokens, or usernames.
    const unsigned int count = __sync_fetch_and_add(&querySequence, 1U);
    if (count >= 64) return;
    char line[] = "T7GDK:QUERY_API=0000000000000000";
    const char digits[] = "0123456789ABCDEF";
    for (unsigned int i = 0; i < 16; ++i)
        line[16 + i] = digits[(api >> ((15 - i) * 4)) & 15];
    OutputDebugStringA(line);
}
static void PrepareLocal()
{
    // Initialization may be invoked from more than one original entry point.
    // A second call never changes the local identity or runs a vendor API.
    if (__sync_lock_test_and_set(&initialized, 1U)) return;
    const int ready = T7DirectLoadStartupProfile();
    OutputDebugStringA(ready ? "T7GDK:LOCAL_PROFILE_PREPARED" : "T7GDK:LOCAL_PROFILE_UNSET");
    OutputDebugStringA("T7GDK:INIT_OK_NO_VENDOR");
}
T7_EXPORT HRESULT InitializeApiImpl(U64, U64) { PrepareLocal(); return 0; }
T7_EXPORT HRESULT InitializeApiImplEx(U64, U64, U64) { PrepareLocal(); return 0; }
T7_EXPORT void UninitializeApiImpl() { OutputDebugStringA("T7GDK:UNINITIALIZE"); }
T7_EXPORT void XErrorReport(unsigned int, const char *)
{
    if (__sync_fetch_and_add(&errorSequence, 1U) < 8)
        OutputDebugStringA("T7GDK:ERROR_REPORT_IGNORED");
}
T7_EXPORT HRESULT QueryApiImpl(U64 api, U64, void **out)
{
    if (out) *out = nullptr;
    EmitQuery(api);
    return static_cast<HRESULT>(0x80004001U); // E_NOTIMPL; never claim authenticated GDK state
}
