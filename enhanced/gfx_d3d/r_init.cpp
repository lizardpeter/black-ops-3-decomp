// P0017: flip-model presentation; P0018: the frame-latency waitable object (B0030, B0032).
//
// Replaces src/gfx_d3d/r_init.cpp's sub_141DAB250 (the swap chain's creation) and sub_141DAD0C0 (its resize):
// - the swap chain is DXGI_SWAP_EFFECT_FLIP_DISCARD instead of the blit model's DISCARD, so Windows can hand the
//   game's buffers to the display (independent flip) in fullscreen and in a borderless window covering the monitor
//   instead of copying them through the desktop compositor; the buffer count stays r_backBufferCount;
// - tearing is allowed when DXGI supports it (IDXGIFactory5), so r_vsync 0 in a window runs uncapped or with VRR;
// - it is made with DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT, and its waitable object, with the latency
//   r_maxFrameLatency asks for (the GPU count if more, as the original's device setting), lets IN_Frame wait for the
//   display before the frame's mouse is read (enhanced/win32/win_input.cpp);
// - a system that refuses the waitable flag gets a flip-model swap chain without it; one that refuses flip model gets
//   the original swap chain, and everything stays as in the original;
// - ResizeBuffers passes the flags the swap chain was made with (the original's fixed ALLOW_MODE_SWITCH would be
//   refused for a waitable or tearing swap chain).
// The swap chain is still made on the window thread (message 0x8042), as in the original. docs/presentation.md.

#include <dxgi.h>
#include <math.h>
#include <string.h>
#include <winuser.h>

#include "universal/dvar.h"
#include "gfx_d3d/com_call.h"
#include "gfx_d3d/r_dvars.h"
#include "gfx_d3d/r_dx.h"
#include "gfx_d3d/r_init.h"

#include "r_flip.h"

#define T7_SOURCE "gfx_d3d/r_init.cpp"
#include <t7_static.h>

T7_STATIC const bool s_constantBufferUsed[12] T7_AT("", "s_constantBufferUsed");
T7_STATIC const unsigned int s_constantBufferSize[12] T7_AT("", "s_constantBufferSize");

extern "C" long _InterlockedIncrement(long volatile *addend);

// {7632e1f5-ee65-4dca-87fd-84cd75f8838d}
static const GUID IID_IDXGIFactory5_Enhanced = {0x7632E1F5, 0xEE65, 0x4DCA, {0x87, 0xFD, 0x84, 0xCD, 0x75, 0xF8, 0x83, 0x8D}};
// {a8be2ac4-199f-4946-b331-79599fb98de7}
static const GUID IID_IDXGISwapChain2_Enhanced = {0xA8BE2AC4, 0x199F, 0x4946, {0xB3, 0x31, 0x79, 0x59, 0x9F, 0xB9, 0x8D, 0xE7}};

bool r_flipModel;
bool r_flipAllowTearing;
unsigned int r_swapChainFlags = DXGI_SWAP_CHAIN_FLAG_ALLOW_MODE_SWITCH;

// The frame-latency waitable object. Only the main thread waits on it (IN_Frame); the thread that presents counts the
// presents. A wait is paired with each counted present: the wait for present p returns once present p-1 is on screen,
// so one frame stays queued while the next frame's input is read. Ported from ghosts-decomp (P0004).
static void *s_frameLatencyWaitable;          // the swap chain's waitable object, or null (no waits)
static void *s_frameLatencySwapChain;         // the swap chain it belongs to
static volatile long s_presentCount;          // presents on that swap chain
static long s_waitedPresentCount;             // presents waited for
static volatile bool s_resyncFrameLatency;    // a wait timed out: take every pending signal, then count again

// Whether DXGI can present with tearing (IDXGIFactory5::CheckFeatureSupport(PRESENT_ALLOW_TEARING)); false when the
// factory is older than DXGI 1.5.
static bool R_CheckTearingSupport(void *factory)
{
	void *factory5 = nullptr;
	BOOL allowTearing = 0;
	if (ComCall<HRESULT>(factory, UNK_QueryInterface, &IID_IDXGIFactory5_Enhanced, &factory5) >= 0 && factory5)
	{
		if (ComCall<HRESULT>(factory5, FACTORY5_CheckFeatureSupport, (unsigned int)DXGI_FEATURE_PRESENT_ALLOW_TEARING,
		                     &allowTearing, (unsigned int)sizeof(allowTearing)) < 0)
			allowTearing = 0;
		ComCall<unsigned long>(factory5, UNK_Release);
	}
	return allowTearing != 0;
}

// The window's swap chain, made by the window procedure (message 0x8042): flip model with the waitable object, else
// flip model without it (before Windows 8.1), else the original description (before Windows 10).
HRESULT R_CreateSwapChain(void *factory, const DXGI_SWAP_CHAIN_DESC *originalDesc)
{
	const bool tearing = R_CheckTearingSupport(factory);
	DXGI_SWAP_CHAIN_DESC flipDesc = *originalDesc;
	flipDesc.SwapEffect = DXGI_SWAP_EFFECT_FLIP_DISCARD;
	flipDesc.Flags |= DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT |
	                  (tearing ? (unsigned int)DXGI_SWAP_CHAIN_FLAG_ALLOW_TEARING : 0u);
	for (int attempt = 0; attempt < 2; attempt++)
	{
		const HRESULT hr = (HRESULT)SendMessageA(g_hWnd, 0x8042, (WPARAM)factory, (LPARAM)&flipDesc);
		if (hr >= 0)
		{
			r_flipModel = true;
			r_flipAllowTearing = tearing;
			r_swapChainFlags = flipDesc.Flags;
			return hr;
		}
		flipDesc.Flags &= ~(unsigned int)DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT;
	}
	r_flipModel = false;
	r_flipAllowTearing = false;
	r_swapChainFlags = originalDesc->Flags;
	return (HRESULT)SendMessageA(g_hWnd, 0x8042, (WPARAM)factory, (LPARAM)originalDesc);
}

// The new swap chain's waitable object. The previous one's handle is closed and the counts start again. Without one
// (no flip model, the flag refused, no IDXGISwapChain2), IN_Frame doesn't wait. The latency is the one the original
// gives the device (141DAA790): r_maxFrameLatency, raised to the GPU count with alternate-frame rendering; with 0
// (DXGI's default) it isn't set.
void R_AcquireFrameLatencyWaitable()
{
	if (s_frameLatencyWaitable)
		CloseHandle(s_frameLatencyWaitable);
	s_frameLatencyWaitable = nullptr;
	s_frameLatencySwapChain = nullptr;
	s_presentCount = 0;
	s_waitedPresentCount = 0;
	s_resyncFrameLatency = false;
	if (!r_flipModel || !(r_swapChainFlags & DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT) || !dx_swapChain)
		return;
	void *swapChain2 = nullptr;
	if (ComCall<HRESULT>(dx_swapChain, UNK_QueryInterface, &IID_IDXGISwapChain2_Enhanced, &swapChain2) < 0 ||
	    !swapChain2)
		return;
	int latency = Dvar_GetInt(r_maxFrameLatency);
	if (latency)
	{
		if (dx_gpuCount > latency)
			latency = dx_gpuCount;
		ComCall<HRESULT>(swapChain2, SWAPCHAIN2_SetMaximumFrameLatency, (unsigned int)latency);
	}
	s_frameLatencyWaitable = ComCall<void *>(swapChain2, SWAPCHAIN2_GetFrameLatencyWaitableObject);
	s_frameLatencySwapChain = s_frameLatencyWaitable ? dx_swapChain : nullptr;
	ComCall<unsigned long>(swapChain2, UNK_Release);
}

void R_CountPresent()
{
	if (s_frameLatencyWaitable)
		_InterlockedIncrement(&s_presentCount);
}

// How long one wait may take before it counts as a missed signal: two refresh periods at r_refreshRate, 50 ms to 1 s
static DWORD R_FrameLatencyTimeout()
{
	const float hz = Dvar_GetFloat(r_refreshRate);
	DWORD timeout = 50;
	if (hz > 0.0f)
	{
		const float periods = 2000.0f / hz;
		if (periods >= 1000.0f)
		{
			timeout = 1000;
		}
		else if (periods > 50.0f)
		{
			timeout = (DWORD)periods;
			if ((float)timeout < periods)
				timeout++;
		}
	}
	return timeout;
}

static DWORD R_WaitFrameLatencyObject(void *waitable, DWORD timeout)
{
	DWORD result;
	do
		result = WaitForSingleObjectEx(waitable, timeout, 1);
	while (result == WAIT_IO_COMPLETION);
	return result;
}

// Waits once for each present counted since the last wait (from IN_Frame, before the frame's mouse is read). With
// latency 1 the wait for present p returns once present p-1 is on screen. Frames that weren't presented are never
// waited for. A wait that times out leaves its signal unaccounted for: the next frame takes every pending signal
// instead of counting. Once the swap chain is gone or replaced, the object is closed and nothing is waited for.
void R_WaitForFrameLatency()
{
	void *waitable = s_frameLatencyWaitable;
	if (!waitable)
		return;
	if (s_frameLatencySwapChain != dx_swapChain)
	{
		CloseHandle(waitable);
		s_frameLatencyWaitable = nullptr;
		s_frameLatencySwapChain = nullptr;
		return;
	}
	const long presented = s_presentCount;
	if (s_resyncFrameLatency)
	{
		s_resyncFrameLatency = false;
		while (R_WaitFrameLatencyObject(waitable, 0) == WAIT_OBJECT_0)
			;
		s_waitedPresentCount = presented;
		return;
	}
	const DWORD timeout = R_FrameLatencyTimeout();
	while (s_waitedPresentCount != presented)
	{
		++s_waitedPresentCount;
		if (R_WaitFrameLatencyObject(waitable, timeout) != WAIT_OBJECT_0)
		{
			s_waitedPresentCount = presented;
			s_resyncFrameLatency = true;
			return;
		}
	}
}

// src: 141DAB250. Enhanced: the swap chain comes from R_CreateSwapChain, and its waitable object is taken right after.
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
	hr = R_CreateSwapChain(factory, &swapChainDesc);
	if (hr < 0)
		return hr;
	R_AcquireFrameLatencyWaitable();
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
	rawMouse.hwndTarget = g_hWndInput;
	RegisterRawInputDevices(&rawMouse, 1, sizeof(rawMouse));
	return hr;
}

// src: 141DAD0C0. Enhanced: ResizeBuffers passes the flags the swap chain was made with.
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
	sub_141DA7B50(&wndParms);
	MSG msg;
	while (PeekMessageA(&msg, nullptr, 0, 0, PM_NOREMOVE))
	{
		if (!GetMessageA(&msg, nullptr, 0, 0))
			SetEvent(sys_quitEvent);
		TranslateMessage(&msg);
		DispatchMessageA(&msg);
	}
	ComCall<HRESULT>(dx_swapChain, SWAPCHAIN_ResizeBuffers, swapChainDesc.BufferCount, swapChainDesc.BufferDesc.Width,
	                 swapChainDesc.BufferDesc.Height, swapChainDesc.BufferDesc.Format, r_swapChainFlags);
	ComCall<void>(dx_context, CTX_Flush);
	sub_141DCDA90(vidConfig_sceneWidth, vidConfig_sceneHeight, vidConfig_displayWidth, vidConfig_displayHeight, true,
	              false);
	sub_141DB5010();
	sub_141DEBFA0();
	if (dx_videoChangeCallback)
		dx_videoChangeCallback(sizeChanged);
}
