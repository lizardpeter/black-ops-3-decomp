// GDK fail-closed replacement for the unmodified BO3 Store EXE in a private Wine prefix.
// Not an Xbox user, license, entitlement, party or online-service implementation.
// Called from inside the executable's normal (unmodified) GDK import boundary.
// The first invocation also *attempts* to load the canonical package's app-local
// recon.dll and call a harmless source-linked probe. Neither loading nor observing
// GDK dispatches proves a menu, map or game-network engine hook.
#include "gdk_feature.h"
#define T7_EXPORT extern "C" __declspec(dllexport)
using HRESULT = long;
using U64 = unsigned long long;
extern "C" __declspec(dllimport) void OutputDebugStringA(const char *);
extern "C" __declspec(dllimport) unsigned int GetModuleFileNameW(void *, wchar_t *, unsigned int);
extern "C" __declspec(dllimport) void *GetModuleHandleW(const wchar_t *);
extern "C" __declspec(dllimport) void *LoadLibraryW(const wchar_t *);
extern "C" __declspec(dllimport) void *GetProcAddress(void *, const char *);
struct T7MemoryRegion
{
    void *baseAddress;
    void *allocationBase;
    unsigned int allocationProtect;
    unsigned short partitionId;
    unsigned short alignment;
    U64 regionSize;
    unsigned int state;
    unsigned int protect;
    unsigned int type;
    unsigned int padding;
};
static_assert(sizeof(T7MemoryRegion) == 48, "Win64 MEMORY_BASIC_INFORMATION layout");
extern "C" __declspec(dllimport) U64 VirtualQuery(const void *, T7MemoryRegion *, U64);
extern "C" __declspec(dllimport) unsigned int GetLastError();
extern "C" __declspec(dllimport) unsigned int GetEnvironmentVariableA(const char *, char *, unsigned int);
extern "C" __declspec(dllimport) int FreeLibrary(void *);
extern "C" int T7DirectLoadStartupProfile();
static volatile unsigned int querySequence;
static volatile unsigned int errorSequence;
static volatile unsigned int initialized;
static bool localFeatureEnabled;
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
    // Capture the loader error *before* debugger output can overwrite it.
    const unsigned int error = GetLastError();
    OutputDebugStringA(reason);
    char detail[] = "T7GDK:RECON_LOAD_ERROR=00000000";
    Hex(error, detail + 23, 8);
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
static bool MainImageRange(const void *address, U64 bytes)
{
    // An untrusted/invalid address must never crash the tracer. The old
    // 0x1A53F000 fixed bound assumed every page in the Store EXE's large
    // virtual .data range was committed and readable. That is not true.
    if (!address || !bytes) return false;
    const void *mainImage = GetModuleHandleW(nullptr);
    if (!mainImage) return false;
    T7MemoryRegion region = {};
    if (VirtualQuery(address, &region, sizeof(region)) != sizeof(region))
        return false;
    if (region.allocationBase != mainImage || region.state != 0x1000)
        return false; // MEM_COMMIT in the original EXE allocation
    const unsigned protect = region.protect;
    const unsigned access = protect & 0xFF;
    if (protect & 0x100) return false; // PAGE_GUARD
    if (access != 0x02 && access != 0x04 && access != 0x08 &&
        access != 0x20 && access != 0x40 && access != 0x80)
        return false; // never dereference NOACCESS or EXECUTE-only memory
    const U64 start = (U64)region.baseAddress, target = (U64)address;
    if (target < start || target - start > region.regionSize)
        return false;
    return bytes <= region.regionSize - (target - start);
}
static unsigned int ReturnRva(void *returnAddress)
{
    if (!MainImageRange(returnAddress, 1))
        return 0xFFFFFFFFU;
    const U64 start = (U64)GetModuleHandleW(nullptr);
    const U64 offset = (U64)returnAddress - start;
    return offset <= 0xFFFFFFFEULL ? (unsigned int)offset : 0xFFFFFFFFU;
}
static bool IsOriginalGuid(const T7Guid *value)
{
    // Log GUID contents only from committed pages of the pinned EXE, never
    // dereference an arbitrary pointer or print a process address.
    return MainImageRange(value, sizeof(T7Guid));
}
static void FormatGuid(const T7Guid *guid, char *chars)
{
    Hex(guid->a, chars, 8);
    Hex(guid->b, chars + 9, 4);
    Hex(guid->c, chars + 14, 4);
    Hex(((unsigned int)guid->d[0] << 8) | guid->d[1], chars + 19, 4);
    for (unsigned i = 2; i < 8; ++i)
        Hex(guid->d[i], chars + 24 + (i - 2) * 2, 2);
}
static U64 GuidIdentity(const T7Guid *guid)
{
    if (!IsOriginalGuid(guid)) return 0;
    // Stable diagnostic fingerprint of all 16 class-ID bytes, not a raw pointer.
    U64 value = 0xcbf29ce484222325ULL;
    const unsigned char *bytes = (const unsigned char *)guid;
    for (unsigned i = 0; i < 16; ++i)
        value = (value ^ bytes[i]) * 0x100000001b3ULL;
    return value;
}
static void EmitQuery(const T7Guid *classId, const T7Guid *iid, unsigned int rva)
{
    const unsigned int count = __sync_fetch_and_add(&querySequence, 1U);
    if (count >= 128) return;
    if (IsOriginalGuid(classId))
    {
        char className[] = "T7GDK:QUERY_CLASS_GUID=00000000-0000-0000-0000-000000000000";
        FormatGuid(classId, className + sizeof("T7GDK:QUERY_CLASS_GUID=") - 1);
        OutputDebugStringA(className);
    }
    else OutputDebugStringA("T7GDK:QUERY_CLASS_GUID_UNAVAILABLE");
    if (IsOriginalGuid(iid))
    {
        char interfaceName[] = "T7GDK:QUERY_INTERFACE_GUID=00000000-0000-0000-0000-000000000000";
        FormatGuid(iid, interfaceName + sizeof("T7GDK:QUERY_INTERFACE_GUID=") - 1);
        OutputDebugStringA(interfaceName);
    }
    else OutputDebugStringA("T7GDK:QUERY_INTERFACE_GUID_UNAVAILABLE");
    char caller[] = "T7GDK:QUERY_CALLER_RVA=00000000";
    Hex(rva, caller + sizeof("T7GDK:QUERY_CALLER_RVA=") - 1, 8);
    OutputDebugStringA(caller);
}
static void PrepareLocal()
{
    // Runs from InitializeApiImpl, not from DllMain/loader-lock context.
    if (__sync_lock_test_and_set(&initialized, 1U)) return;
    const int ready = T7DirectLoadStartupProfile();
    OutputDebugStringA(ready ? "T7GDK:LOCAL_PROFILE_PREPARED" : "T7GDK:LOCAL_PROFILE_UNSET");
    char featureFlag[2] = {};
    localFeatureEnabled = GetEnvironmentVariableA("T7_ENHANCED_LOCAL_FEATURE", featureFlag, 2) == 1 &&
                          featureFlag[0] == '1';
    if (localFeatureEnabled)
        OutputDebugStringA("T7GDK:LOCAL_FEATURE_INTERFACE_ENABLED");
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
T7_EXPORT HRESULT QueryApiImpl(const T7Guid *classId, const T7Guid *interfaceId, void **out)
{
    if (out) *out = nullptr;
    // This return address identifies the original GDK dispatch wrapper.
    // The ABI and deeper original game caller are not yet verified.
    const unsigned int rva = ReturnRva(__builtin_return_address(0));
    EmitQuery(classId, interfaceId, rva);
    const U64 classFingerprint = GuidIdentity(classId);
    if (observeDispatch)
    {
        observeDispatch(classFingerprint, rva);
        // One-time evidence that code in *recon.dll* actually executed.
        // A loaded DLL or resolved export alone is not enough.
        if (observedCount && observedCount() == 1U)
            OutputDebugStringA("T7GDK:RECON_CALLBACK_EXECUTED");
    }
    // Optional, strictly local COM feature query. All features are reported
    // unavailable. Never provide Xbox users, licensing, or vendor objects.
    if (localFeatureEnabled && IsOriginalGuid(classId) && IsOriginalGuid(interfaceId))
    {
        const int result = T7OfflineFeatureQuery(classId, interfaceId, out);
        if (!result)
        {
            OutputDebugStringA("T7GDK:LOCAL_FEATURE_INTERFACE_GRANTED");
            return 0;
        }
    }
    return static_cast<HRESULT>(0x80070032U); // documented HRESULT_FROM_WIN32(ERROR_NOT_SUPPORTED)
}
T7_EXPORT unsigned int T7EnhancedCapabilities() { return 7U; }
T7_EXPORT int T7EnhancedEngineIntegrated() { return 0; } // no game packet/menu hook
T7_EXPORT int T7EnhancedReconLoaded() { return reconstruction && observeDispatch ? 1 : 0; }
