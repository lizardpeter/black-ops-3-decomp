// P0002: the offline package does not use the Xbox GDK runtime.
//
// BlackOps3_MSStore links the GDK's static XGameRuntime layer. Every GDK API goes through it (14291FCC0): it loads
// xgameruntime.dll on first use (14291FC80) and otherwise returns the GDK's own error, 0x89240101
// (E_GAMERUNTIME_DLL_NOT_FOUND here, since the offline package refuses to load the DLL: egress.cpp). WinMain
// (1423EA4D0) treats a failed XGameRuntimeInitialize as fatal ("XGameRuntime failed with error code %d").
//
// The offline package replaces XGameRuntimeInitialize (142920308, `xor ecx,ecx; jmp 14291FA64`) with this: it
// reports success without loading or initializing anything. The runtime stays unloaded, so every later GDK call
// (users, Xbox Live, Store, PlayFab) still fails through the original layer with the GDK's own error; no user,
// licence or service result is fabricated here. Faithful source is unchanged.
extern "C" __declspec(dllexport) int T7OfflineGameRuntimeInitialize()
{
    return 0; // S_OK: WinMain continues; the GDK runtime is deliberately not loaded
}
