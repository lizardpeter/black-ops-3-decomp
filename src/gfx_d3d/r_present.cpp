// Presenting a finished frame. Original function name and source path unknown (the back end's swap, IW's
// RB_SwapBuffers, is the closest lineage name); docs/presentation.md has the whole path.
//
// The Store build never calls IDXGISwapChain::Present itself: it sends message 0x8043 to the game window, whose
// window procedure (1423F3CE0) presents on the window thread (1423F49B0). That thread pumps its messages, then
// sleeps 1 ms, so every present waits for it to come round (B0031).

#include <dxgi.h>
#include <winuser.h>

#include "gfx_d3d/com_call.h"
#include "gfx_d3d/r_dvars.h"
#include "gfx_d3d/r_dx.h"
#include "gfx_d3d/r_present.h"
#include "universal/dvar.h"
#include "qcommon/qcommon.h"
#include "universal/sys_critsect.h"

#define T7_SOURCE "gfx_d3d/r_present.cpp"
#include <t7_static.h>

T7_STATIC int s_lastAfrIndex T7_AT("", "s_lastAfrIndex");

// 141D46720  gfx_d3d/r_present.cpp
// Presents the back buffer: with SLI, notes whether the GPU that drew this frame drew the last one too; on AMD with
// vsync, during a loading screen, first sleeps most of a refresh period (B0015); then has the window thread present
// (sync interval 1 with r_vsync, else 0); a removed or reset device is an error; with 3D Vision active, applies
// r_convergence.
void sub_141D46720()
{
	if (dx_nvapiInitialized && dx_gpuCount > 1)
	{
		ScopedCriticalSection lock;
		ScopedCriticalSection_Construct(&lock, CRITSECT_D3D_CONTEXT, SCOPED_CRITSECT_NORMAL);
		NV_GET_CURRENT_SLI_STATE sliState;
		sliState.version = NV_GET_CURRENT_SLI_STATE_VER1;
		const int status = NvAPI_D3D_GetCurrentSLIState(dx_device, &sliState);
		// read whether or not the call succeeded (B0033)
		const int afrIndex = (int)sliState.currentAFRIndex;
		if (status == 0 && s_lastAfrIndex == afrIndex)
			dx_afrIndexRepeated = true;
		s_lastAfrIndex = afrIndex;
		ScopedCriticalSection_Destruct(&lock);
	}
	const bool vsync = Dvar_GetBool(r_vsync);
	if (dx_remoteScreenUpdateNesting && vsync && dx_vendor == 2)
	{
		const int pace = -2 - (int)(-1000.0f / Dvar_GetFloat(r_refreshRate));
		Sleep(pace > 0 ? (DWORD)pace : 0);
	}
	const HRESULT hr = (HRESULT)SendMessageA(win_hWnd, 0x8043, (WPARAM)vsync, 0);
	if (hr < 0)
	{
		const char *reason;
		if (hr == DXGI_ERROR_DEVICE_REMOVED)
		{
			const HRESULT removedReason = ComCall<HRESULT>(dx_device, DEV_GetDeviceRemovedReason);
			if (removedReason == DXGI_ERROR_INVALID_CALL)
				reason = "DXGI_ERROR_INVALID_CALL";
			else if (removedReason == hr)
				reason = "DXGI_ERROR_DEVICE_REMOVED";
			else if (removedReason == DXGI_ERROR_DEVICE_HUNG)
				reason = "DXGI_ERROR_DEVICE_HUNG";
			else if (removedReason == DXGI_ERROR_DEVICE_RESET)
				reason = "DXGI_ERROR_DEVICE_RESET";
			else if (removedReason == DXGI_ERROR_DRIVER_INTERNAL_ERROR)
				reason = "DXGI_ERROR_DRIVER_INTERNAL_ERROR";
			else
				reason = "Unknown";
			Com_Error_("", 0, ERR_DROP, "DirectX error: %s [0x%08X]", reason, hr);
		}
		else if (hr == DXGI_ERROR_DEVICE_RESET)
		{
			Com_Error_("", 0, ERR_DROP, "DirectX error: %s [0x%08X]", "DXGI_ERROR_DEVICE_RESET", hr);
		}
	}
	if (dx_stereoHandle)
	{
		unsigned char stereoOn = 0;
		if (NvAPI_Stereo_IsActivated(dx_stereoHandle, &stereoOn) == 0)
		{
			dx_stereoActivated = stereoOn != 0;
			if (dx_stereoActivated)
				NvAPI_Stereo_SetConvergence(dx_stereoHandle, Dvar_GetFloat(r_convergence));
			return;
		}
	}
	dx_stereoActivated = false;
}
