// Deterministic no-device Sony-pad compatibility for the BO3 Store *offline*
// enhanced package. This is not a DualShock/DualSense controller driver.
// Pinned original BO3 imports exactly these 7 named entry points, verified
// against its EXE import directory in CI (2026-11-12 run 43315837602).
// No Xbox, PlayStation Network, system DLL, USB, HID, network or user imports.
//
// The only "success" is optional subsystem setup/shutdown (no resources).
// All actual device operations fail, without writing caller-owned buffers.
// True gamepad support requires a separate native input backend.
#define EXPORT extern "C" __declspec(dllexport)
static constexpr int Unavailable = -1;

extern "C" int __stdcall _DllMainCRTStartup(void *, unsigned int, void *) { return 1; }
EXPORT int scePadInit() { return 0; }
EXPORT int scePadTerminate() { return 0; }
EXPORT int scePadOpen(int, int, int, const void *) { return Unavailable; }
EXPORT int scePadClose(int) { return Unavailable; }
EXPORT int scePadReadState(int, void *) { return Unavailable; }
EXPORT int scePadSetVibration(int, const void *) { return Unavailable; }
EXPORT int scePadGetControllerInformation(int, void *) { return Unavailable; }
