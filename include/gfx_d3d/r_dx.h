// gfx_d3d/r_dx.h (reconstructed: only what reconstructed code uses so far)
//
// The renderer's Direct3D state. In IW's engines these are members of the `dx` globals struct; the Store build's
// layout of that struct isn't worked out yet, so each member reconstructed code uses is its own symbol, at its
// address in the original (records/names.tsv). Interface pointers are typed void: calls go through
// gfx_d3d/com_call.h.
#pragma once

#include <winuser.h>

#include "win32/win_input.h"  // win_hWnd, win_hRawInputWnd, sys_quitEvent

extern void *dx_device;          // ID3D11Device
extern void *dx_context;         // ID3D11DeviceContext (immediate)
extern void *dx_swapChain;       // IDXGISwapChain, made by the window procedure (message 0x8042)
extern void *dx_backBuffer;      // ID3D11Texture2D, the swap chain's buffer 0 (141DD27B0)
extern void *dx_constantBuffers[12];
extern int dx_vendor;            // 1 NVIDIA, 2 AMD, 3 Intel (141DAA790, from the adapter's VendorId)
extern int dx_gpuCount;          // GPUs rendering alternate frames (NVIDIA SLI / AMD CrossFire), 1 without
extern int dx_remoteScreenUpdateNesting;  // > 0 while the render thread draws a loading screen (141DCD4D0)
extern bool dx_nvapiInitialized;
extern bool dx_afrIndexRepeated;
extern void *dx_stereoHandle;    // NvAPI StereoHandle, or null
extern bool dx_stereoActivated;
extern int dx_desktopWidth;      // GetSystemMetrics(SM_CXSCREEN) when the swap chain was made
extern int dx_desktopHeight;
extern int dx_monitorWidth;      // the size of the monitor the swap chain is on
extern int dx_monitorHeight;
extern bool dx_monitorSizeKnown;
extern bool dx_needVideoChange;  // the next video check (141DAC790) applies the mode: set when fullscreen failed
extern bool dx_needFullscreen;
