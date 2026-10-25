// P0017: the flip-model present, made where the frame is finished (B0030, B0031, B0015).
//
// Replaces src/gfx_d3d/r_present.cpp's sub_141D46720. With a flip-model swap chain (enhanced/gfx_d3d/r_init.cpp):
// - the thread that finished the frame presents it itself, instead of sending message 0x8043 to the window thread and
//   waiting until that thread's 1 ms sleep ends (the window thread still makes and resizes the swap chain and switches
//   fullscreen); the present happens under the D3D context lock the callers hold, as the original's does;
// - with r_vsync 0 in a window (not exclusive fullscreen) it presents with DXGI_PRESENT_ALLOW_TEARING when the swap
//   chain allows it, so the frame goes out at once, uncapped or with VRR;
// - flip model unbinds the back buffer at Present: the render targets bound before it are bound again after it, as
//   the renderer's state cache still believes they are;
// - each successful present is counted for the frame-latency wait (P0018);
// - the AMD loading-screen sleep (B0015) is dropped: the frame-latency wait paces the frames.
// Without flip model (a system that refused it) everything is the original. The SLI check, the error report and
// 3D Vision are unchanged. docs/presentation.md.

#include <dxgi.h>
#include <winuser.h>

#include "gfx_d3d/com_call.h"
#include "gfx_d3d/r_dvars.h"
#include "gfx_d3d/r_dx.h"
#include "gfx_d3d/r_present.h"
#include "qcommon/qcommon.h"
#include "universal/dvar.h"
#include "universal/sys_critsect.h"

#include "r_flip.h"

#define T7_SOURCE "gfx_d3d/r_present.cpp"
#include <t7_static.h>

T7_STATIC int s_lastAfrIndex T7_AT("", "s_lastAfrIndex");

enum
{
	D3D11_SIMULTANEOUS_RENDER_TARGET_COUNT = 8,
};

// Presents dx_swapChain from this thread: sync interval 1 with vsync, else 0 and tearing in a window when allowed.
// The bound render targets and depth-stencil view are taken before and bound again after.
HRESULT R_PresentFlip(bool vsync)
{
	unsigned int flags = 0;
	if (!vsync && r_flipAllowTearing)
	{
		BOOL fullscreen = 0;
		ComCall<HRESULT>(dx_swapChain, SWAPCHAIN_GetFullscreenState, &fullscreen, (void *)nullptr);
		if (!fullscreen)
			flags = DXGI_PRESENT_ALLOW_TEARING;
	}
	void *renderTargets[D3D11_SIMULTANEOUS_RENDER_TARGET_COUNT] = {};
	void *depthStencil = nullptr;
	ComCall<void>(dx_context, CTX_OMGetRenderTargets, (unsigned int)D3D11_SIMULTANEOUS_RENDER_TARGET_COUNT,
	              renderTargets, &depthStencil);
	const HRESULT hr = ComCall<HRESULT>(dx_swapChain, SWAPCHAIN_Present, vsync ? 1u : 0u, flags);
	if (hr >= 0)
		R_CountPresent();
	ComCall<void>(dx_context, CTX_OMSetRenderTargets, (unsigned int)D3D11_SIMULTANEOUS_RENDER_TARGET_COUNT,
	              (void *const *)renderTargets, depthStencil);
	for (int i = 0; i < D3D11_SIMULTANEOUS_RENDER_TARGET_COUNT; i++)
	{
		if (renderTargets[i])
			ComCall<unsigned long>(renderTargets[i], UNK_Release);
	}
	if (depthStencil)
		ComCall<unsigned long>(depthStencil, UNK_Release);
	return hr;
}

// src: 141D46720. Enhanced: a flip-model swap chain is presented here (R_PresentFlip).
void sub_141D46720()
{
	if (dx_nvapiInitialized && dx_gpuCount > 1)
	{
		ScopedCriticalSection lock;
		ScopedCriticalSection_Construct(&lock, CRITSECT_D3D_CONTEXT, SCOPED_CRITSECT_NORMAL);
		NV_GET_CURRENT_SLI_STATE sliState;
		sliState.version = NV_GET_CURRENT_SLI_STATE_VER1;
		const int status = NvAPI_D3D_GetCurrentSLIState(dx_device, &sliState);
		const int afrIndex = (int)sliState.currentAFRIndex;
		if (status == 0 && s_lastAfrIndex == afrIndex)
			dx_afrIndexRepeated = true;
		s_lastAfrIndex = afrIndex;
		ScopedCriticalSection_Destruct(&lock);
	}
	const bool vsync = Dvar_GetBool(r_vsync);
	HRESULT hr;
	if (r_flipModel && dx_swapChain)
	{
		hr = R_PresentFlip(vsync);
	}
	else
	{
		if (dx_remoteScreenUpdateNesting && vsync && dx_vendor == 2)
		{
			const int pace = -2 - (int)(-1000.0f / Dvar_GetFloat(r_refreshRate));
			Sleep(pace > 0 ? (DWORD)pace : 0);
		}
		hr = (HRESULT)SendMessageA(g_hWnd, 0x8043, (WPARAM)vsync, 0);
	}
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
