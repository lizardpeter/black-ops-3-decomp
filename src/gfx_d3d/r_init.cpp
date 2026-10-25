// Renderer start-up: display modes and the swap chain description. Original function names unknown; source path
// assumed from the engine lineage (IW's gfx_d3d/r_init.cpp creates the device and swap chain).
//
// How BO3 picks its refresh rate (docs/refresh-rate.md): r_refreshRate is a number the player chooses, not "whatever
// Windows is set to". In exclusive fullscreen the swap chain asks DXGI for an exact display mode, and
// sub_141DA7A00 picks, among the enumerated modes of the chosen monitor at the chosen resolution, the one whose rate
// is closest to r_refreshRate. Windowed and borderless never get a mode: the desktop's own rate applies.

#include <dxgi.h>
#include <math.h>
#include <string.h>
#include <winuser.h>

#include "universal/dvar.h"
#include "gfx_d3d/com_call.h"
#include "gfx_d3d/r_dvars.h"
#include "gfx_d3d/r_dx.h"
#include "gfx_d3d/r_init.h"

#define T7_SOURCE "gfx_d3d/r_init.cpp"
#include <t7_static.h>

T7_STATIC const bool s_constantBufferUsed[12] T7_AT("", "s_constantBufferUsed")
	T7_INIT(= {false, true, false, true, false, false, false, false, true, false, false, false});
T7_STATIC const unsigned int s_constantBufferSize[12] T7_AT("", "s_constantBufferSize")
	T7_INIT(= {0, 3024, 944, 256, 144, 160, 1040, 240, 2016, 65520, 61152, 65472});

// 141DAA730  gfx_d3d/r_init.cpp
// qsort comparator for a monitor's display modes: by width, then height, then refresh rate, all ascending. Two
// modes with the same rate compare as 1 both ways (B0014): it never returns 0 once the sizes are equal.
int sub_141DAA730(const void *a, const void *b)
{
	const DXGI_MODE_DESC *modeA = (const DXGI_MODE_DESC *)a;
	const DXGI_MODE_DESC *modeB = (const DXGI_MODE_DESC *)b;
	int diff = (int)(modeA->Width - modeB->Width);
	if (diff)
		return diff;
	diff = (int)(modeA->Height - modeB->Height);
	if (diff)
		return diff;
	float rateA = (float)modeA->RefreshRate.Numerator / (float)modeA->RefreshRate.Denominator;
	float rateB = (float)modeB->RefreshRate.Numerator / (float)modeB->RefreshRate.Denominator;
	return rateA - rateB < 0.0f ? -1 : 1;
}

// 141DA7A00  gfx_d3d/r_init.cpp
// Fills the swap chain description for wndParms. The buffer is always described windowed (fullscreen is entered
// afterwards); in fullscreen with a refresh rate set, BufferDesc becomes the enumerated mode of that size whose rate
// is closest to wndParms->hz, so DXGI switches to exactly that mode. With no such mode the description keeps a 0/0
// refresh rate. hz comes from r_refreshRate, whose domain stops at 240 (B0012): no higher mode can win.
void sub_141DA7A00(DXGI_SWAP_CHAIN_DESC *desc, const GfxWindowParms *wndParms)
{
	*desc = DXGI_SWAP_CHAIN_DESC();
	desc->BufferDesc.Width = wndParms->displayWidth;
	desc->BufferDesc.Height = wndParms->displayHeight;
	desc->BufferDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
	desc->SampleDesc.Count = 1;
	desc->BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT | DXGI_USAGE_SHADER_INPUT;
	desc->BufferCount = Dvar_GetInt(r_backBufferCount);
	desc->OutputWindow = wndParms->hwnd;
	desc->Windowed = 1;
	desc->SwapEffect = DXGI_SWAP_EFFECT_DISCARD;
	desc->Flags = DXGI_SWAP_CHAIN_FLAG_ALLOW_MODE_SWITCH;
	if (!wndParms->fullscreen || wndParms->hz == 0.0f)
		return;
	int monitor = wndParms->monitor;
	if (!monitor || monitor - 1 >= dx_monitorCount)
		return;
	float bestDiff = 3.4028235e38f;
	for (unsigned int i = 0; i < dx_modeCount[monitor - 1]; i++)
	{
		const DXGI_MODE_DESC *mode = &dx_modes[monitor - 1][i];
		if ((int)mode->Width != wndParms->displayWidth || (int)mode->Height != wndParms->displayHeight)
			continue;
		float diff = fabsf(wndParms->hz - (float)mode->RefreshRate.Numerator / (float)mode->RefreshRate.Denominator);
		if (diff < bestDiff)
		{
			desc->BufferDesc = *mode;
			bestDiff = diff;
		}
	}
}

// 141DAB250  gfx_d3d/r_init.cpp
// Makes the window's swap chain and what depends on it. The swap chain itself is made on the window thread: the
// window procedure (1423F3CE0) handles message 0x8042 with IDXGIFactory::CreateSwapChain and stores the result in
// dx_swapChain. Then: DXGI may not touch the window (no Alt+Enter, no Print Screen, no window changes); the size of the
// monitor the swap chain is on is noted (the desktop's when that fails); a fullscreen window enters fullscreen, and if
// it didn't, r_fullscreen falls back to windowed and the video check redoes the mode; the shared constant buffers are
// made and bound; the raw-input thread's window starts receiving the mouse, even in the background. Returns the
// window procedure's result. The DXGI device, adapter and factory are not released when it fails (B0034).
HRESULT sub_141DAB250(const GfxWindowParms *wndParms)
{
	dx_desktopWidth = GetSystemMetrics(SM_CXSCREEN);
	dx_desktopHeight = GetSystemMetrics(SM_CYSCREEN);
	void *dxgiDevice;
	void *adapter;
	void *factory;
	HRESULT hr = ComCall<HRESULT>(dx_device, UNK_QueryInterface, &IID_IDXGIDevice1, &dxgiDevice);
	if (hr < 0)
		return hr;
	hr = ComCall<HRESULT>(dxgiDevice, OBJECT_GetParent, &IID_IDXGIAdapter1, &adapter);
	if (hr < 0)
		return hr;
	hr = ComCall<HRESULT>(adapter, OBJECT_GetParent, &IID_IDXGIFactory1, &factory);
	if (hr < 0)
		return hr;
	DXGI_SWAP_CHAIN_DESC swapChainDesc;
	sub_141DA7A00(&swapChainDesc, wndParms);
	hr = (HRESULT)SendMessageA(win_hWnd, 0x8042, (WPARAM)factory, (LPARAM)&swapChainDesc);
	if (hr < 0)
		return hr;
	ComCall<HRESULT>(factory, FACTORY_MakeWindowAssociation, wndParms->hwnd,
	                 (unsigned int)(DXGI_MWA_NO_WINDOW_CHANGES | DXGI_MWA_NO_ALT_ENTER | DXGI_MWA_NO_PRINT_SCREEN));
	ComCall<unsigned long>(factory, UNK_Release);
	ComCall<unsigned long>(adapter, UNK_Release);
	ComCall<unsigned long>(dxgiDevice, UNK_Release);
	bool monitorSizeKnown;
	if (dx_swapChain)
	{
		void *output;
		ComCall<HRESULT>(dx_swapChain, SWAPCHAIN_GetContainingOutput, &output);
		if (output)
		{
			DXGI_OUTPUT_DESC outputDesc;
			ComCall<HRESULT>(output, OUTPUT_GetDesc, &outputDesc);
			ComCall<unsigned long>(output, UNK_Release);
			MONITORINFO monitorInfo;
			monitorInfo.cbSize = sizeof(monitorInfo);
			if (GetMonitorInfoA(outputDesc.Monitor, &monitorInfo))
			{
				dx_monitorWidth = monitorInfo.rcMonitor.right - monitorInfo.rcMonitor.left;
				dx_monitorHeight = monitorInfo.rcMonitor.bottom - monitorInfo.rcMonitor.top;
				monitorSizeKnown = true;
				goto haveMonitorSize;
			}
		}
	}
	dx_monitorWidth = GetSystemMetrics(SM_CXSCREEN);
	dx_monitorHeight = GetSystemMetrics(SM_CYSCREEN);
	monitorSizeKnown = dx_monitorWidth > 0 && dx_monitorHeight > 0;
haveMonitorSize:
	dx_monitorSizeKnown = monitorSizeKnown;
	if (wndParms->fullscreen)
		sub_141DAC020();
	BOOL fullscreen;
	ComCall<HRESULT>(dx_swapChain, SWAPCHAIN_GetFullscreenState, &fullscreen, (void *)nullptr);
	if (!fullscreen && wndParms->fullscreen)
	{
		Dvar_SetInt(r_fullscreen, 0, DVAR_SOURCE_EXTERNAL);
		GfxWindowParms windowed;
		sub_141DABB90(&windowed);
		sub_141DAB810(&windowed);
		sub_141DAC3E0();
		dx_needVideoChange = true;
		dx_needFullscreen = true;
	}
	D3D11_BUFFER_DESC bufferDesc;
	bufferDesc.BindFlags = D3D11_BIND_CONSTANT_BUFFER;
	bufferDesc.ByteWidth = 0;
	bufferDesc.MiscFlags = 0;
	bufferDesc.StructureByteStride = 0;
	bufferDesc.Usage = D3D11_USAGE_DYNAMIC;
	bufferDesc.CPUAccessFlags = D3D11_CPU_ACCESS_WRITE;
	for (unsigned int i = 0; i < 12; i++)
	{
		if (s_constantBufferUsed[i])
		{
			bufferDesc.ByteWidth = s_constantBufferSize[i];
			ComCall<HRESULT>(dx_device, DEV_CreateBuffer, &bufferDesc, (const void *)nullptr, &dx_constantBuffers[i]);
		}
		else
		{
			dx_constantBuffers[i] = nullptr;
		}
	}
	sub_141DAB1C0(dx_context);
	RAWINPUTDEVICE rawMouse;
	rawMouse.usUsagePage = HID_USAGE_PAGE_GENERIC;
	rawMouse.usUsage = HID_USAGE_GENERIC_MOUSE;
	rawMouse.dwFlags = RIDEV_INPUTSINK;
	rawMouse.hwndTarget = win_hRawInputWnd;
	RegisterRawInputDevices(&rawMouse, 1, sizeof(rawMouse));
	return hr;
}

// 141DAD0C0  gfx_d3d/r_init.cpp
// Resizes the swap chain's buffers to the current mode (called by 14148CF00 when the window's size changed): the views
// bound to the render-target slots are unbound, the back buffer is released, the calling thread's pending messages
// are handled, then IDXGISwapChain::ResizeBuffers with the description sub_141DA7A00 makes (flags fixed to
// ALLOW_MODE_SWITCH), the context is flushed and the render targets are made again at the new size. The callback is
// told whether the display size changed. ResizeBuffers' result isn't checked.
void sub_141DAD0C0()
{
	if (!dx_windowHwnd || !dx_swapChain)
		return;
	sub_141DD3730(**(void ***)((char *)gfx_renderTargetState + 0x20E8), 1);
	for (unsigned int i = 0; i < 0x6E; i++)
	{
		char *view = (char *)gfx_renderTargetState + (unsigned short)i * 0xAE0;
		if (view[0xA89] || (view[0xAD8] & 0x40))
			continue;
		for (unsigned int slot = 0; slot < 8; slot++)
			sub_141DD2C80(view, slot);
		memset(view + 0xA80, 0, 0x60);
	}
	sub_141DCA670();
	if (dx_backBuffer)
	{
		ComCall<unsigned long>(dx_backBuffer, UNK_Release);
		dx_backBuffer = nullptr;
	}
	GfxWindowParms wndParms;
	sub_141DABB90(&wndParms);
	const bool sizeChanged = wndParms.displayWidth != vidConfig_displayWidth ||
	                         wndParms.displayHeight != vidConfig_displayHeight;
	DXGI_SWAP_CHAIN_DESC swapChainDesc;
	sub_141DA7A00(&swapChainDesc, &wndParms);
	R_StoreWindowSettings(&wndParms);
	MSG msg;
	while (PeekMessageA(&msg, nullptr, 0, 0, PM_NOREMOVE))
	{
		if (!GetMessageA(&msg, nullptr, 0, 0))
			SetEvent(sys_quitEvent);
		TranslateMessage(&msg);
		DispatchMessageA(&msg);
	}
	ComCall<HRESULT>(dx_swapChain, SWAPCHAIN_ResizeBuffers, swapChainDesc.BufferCount, swapChainDesc.BufferDesc.Width,
	                 swapChainDesc.BufferDesc.Height, swapChainDesc.BufferDesc.Format,
	                 (unsigned int)DXGI_SWAP_CHAIN_FLAG_ALLOW_MODE_SWITCH);
	ComCall<void>(dx_context, CTX_Flush);
	sub_141DCDA90(vidConfig_sceneWidth, vidConfig_sceneHeight, vidConfig_displayWidth, vidConfig_displayHeight, true,
	              false);
	sub_141DB5010();
	sub_141DEBFA0();
	if (dx_videoChangeCallback)
		dx_videoChangeCallback(sizeChanged);
}
