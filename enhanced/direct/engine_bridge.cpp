// First in-process, source-linked enhanced execution boundary for the pinned
// BlackOps3_MSStore image. Called only by our private-Wine GDK shim after the
// unchanged EXE dynamically loads recon.dll. Not an engine packet/menu hook.
// No CRT, filesystem, network, vendor dependencies, original offsets or globals.
using U64 = unsigned long long;
#define T7E extern "C" __declspec(dllexport)
static volatile unsigned int gdkDispatchCount;
static volatile U64 latestQueryArgument;
static volatile unsigned int latestCallerRva;

T7E unsigned int T7EnhancedReconProbe()
{
    return 0x54374531U; // "T7E1": known revision, not proof of game integration
}
T7E void T7EnhancedObserveGdkDispatch(U64 argument, unsigned int callerRva)
{
    __sync_fetch_and_add(&gdkDispatchCount, 1U);
    latestQueryArgument = argument;
    latestCallerRva = callerRva;
}
T7E unsigned int T7EnhancedObservedGdkCalls()
{
    return __sync_fetch_and_add(&gdkDispatchCount, 0U);
}
T7E U64 T7EnhancedLastGdkArgument() { return latestQueryArgument; }
T7E unsigned int T7EnhancedLastGdkCallerRva() { return latestCallerRva; }
