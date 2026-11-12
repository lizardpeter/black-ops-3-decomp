// GDK fail-closed replacement for the unmodified BO3 Store EXE in a private Wine prefix.
// Not an Xbox user, license, entitlement, party or online-service implementation.
// Called from inside the executable's normal (unmodified) GDK import boundary.
// The first invocation also *attempts* to load the canonical package's app-local
// recon.dll and call a harmless source-linked probe. Neither loading nor observing
// GDK dispatches proves a menu, map or game-network engine hook.
#define T7_EXPORT extern "C" __declspec(dllexport)
using HRESULT = long;
using U64 = unsigned long long;
extern "C" __declspec(dllimport) void OutputDebugStringA(const char *);
extern "C" __declspec(dllimport) unsigned int GetModuleFileNameW(void *, wchar_t *, unsigned int);
extern "C" __declspec(dllimport) void *GetModuleHandleW(const wchar_t *);
extern "C" __declspec(dllimport) void *LoadLibraryW(const wchar_t *);
extern "C" __declspec(dllimport) void *GetProcAddress(void *, const char *);
extern "C" __declspec(dllimport) unsigned int GetLastError();
extern "C" __declspec(dllimport) int FreeLibrary(void *);
extern "C" int T7DirectLoadStartupProfile();
static volatile unsigned int querySequence;
static volatile unsigned int errorSequence;
static volatile unsigned int initialized;
static void *reconstruction;
using Observer = void (*)(U64, unsigned int);
static Observer observeDispatch;
using CountObserver = unsigned int (*)();
static CountObserver observedCount;

extern "C" int __stdcall _DllMainCRTStartup(void *, unsigned int, void *) { return 1; }

static void Hex(unsigned long long value, char *out, unsigned count)
{
    const char digits[] = "0123456789ABCDEF";
    for (unsigned i = 0; i < count; ++i)
        out[i] = digits[(value >> (4 * (count - i - 1))) & 15];
}
static void EmitLoadFailure(const char *reason)
{
    OutputDebugStringA(reason);
    char detail[] = "T7GDK:RECON_LOAD_ERROR=00000000";
    Hex(GetLastError(), detail + 23, 8);
    OutputDebugStringA(detail);
}
static void TryLoadEnhancedRecon()
{
    // Resolve alongside the package EXE, never the process working directory
    // (which must point to the user's authentic game assets).
    wchar_t path[1024] = {};
    const unsigned length = GetModuleFileNameW(nullptr, path, 1024);
    if (!length || length >= 1024) { EmitLoadFailure("T7GDK:RECON_EXE_PATH_UNAVAILABLE"); return; }
    unsigned directory = length;
    while (directory && path[directory - 1] != L'\\' && path[directory - 1] != L'/') --directory;
    const wchar_t filename[] = L"recon.dll";
    if (!directory || directory + sizeof(filename) / sizeof(filename[0]) > 1024)
    { OutputDebugStringA("T7GDK:RECON_INVALID_EXE_DIRECTORY"); return; }
    for (unsigned i = 0; i < sizeof(filename) / sizeof(filename[0]); ++i)
        path[directory + i] = filename[i];

    void *module = LoadLibraryW(path);
    if (!module) { EmitLoadFailure("T7GDK:RECON_LOAD_FAILED"); return; }
    using Probe = unsigned int (*)();
    auto probe = (Probe)GetProcAddress(module, "T7EnhancedReconProbe");
    auto observer = (Observer)GetProcAddress(module, "T7EnhancedObserveGdkDispatch");
    auto count = (CountObserver)GetProcAddress(module, "T7EnhancedObservedGdkCalls");
    if (!probe || !observer || !count || probe() != 0x54374531U)
    {
        OutputDebugStringA("T7GDK:RECON_INVALID_PROBE");
        FreeLibrary(module);
        return;
    }
    reconstruction = module;
    observeDispatch = observer;
    observedCount = count;
    OutputDebugStringA("T7GDK:RECON_PROBE_OK");
    OutputDebugStringA("T7GDK:RECON_IN_PROCESS");
}
static unsigned int ReturnRva(void *returnAddress)
{
    void *base = GetModuleHandleW(nullptr);
    const unsigned long long address = (unsigned long long)returnAddress;
    const unsigned long long start = (unsigned long long)base;
    // Only emit an RVA from the pinned original image. Never log raw pointers.
    return base && address >= start && address - start < 0x1A53F000ULL ?
        (unsigned int)(address - start) : 0xFFFFFFFFU;
}
static void EmitQuery(U64 api, unsigned int rva)
{
    const unsigned int count = __sync_fetch_and_add(&querySequence, 1U);
    if (count >= 128) return;
    char id[] = "T7GDK:QUERY_API=0000000000000000";
    Hex(api, id + 16, 16);
    OutputDebugStringA(id);
    char caller[] = "T7GDK:QUERY_CALLER_RVA=00000000";
    Hex(rva, caller + 23, 8);
    OutputDebugStringA(caller);
}
static void PrepareLocal()
{
    // Runs from InitializeApiImpl, not from DllMain/loader-lock context.
    if (__sync_lock_test_and_set(&initialized, 1U)) return;
    const int ready = T7DirectLoadStartupProfile();
    OutputDebugStringA(ready ? "T7GDK:LOCAL_PROFILE_PREPARED" : "T7GDK:LOCAL_PROFILE_UNSET");
    TryLoadEnhancedRecon();
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
    // This return address identifies the original GDK dispatch wrapper.
    // The ABI and deeper original game caller are not yet verified.
    const unsigned int rva = ReturnRva(__builtin_return_address(0));
    EmitQuery(api, rva);
    if (observeDispatch)
    {
        observeDispatch(api, rva);
        // One-time evidence that code in *recon.dll* actually executed.
        // A loaded DLL or resolved export alone is not enough.
        if (observedCount && observedCount() == 1U)
            OutputDebugStringA("T7GDK:RECON_CALLBACK_EXECUTED");
    }
    return static_cast<HRESULT>(0x80004001U); // E_NOTIMPL, fail closed
}
T7_EXPORT unsigned int T7EnhancedCapabilities() { return 7U; }
T7_EXPORT int T7EnhancedEngineIntegrated() { return 0; } // no game packet/menu hook
T7_EXPORT int T7EnhancedReconLoaded() { return reconstruction && observeDispatch ? 1 : 0; }
