// gfx_d3d/r_init.h (reconstructed: only what reconstructed code uses so far)
#pragma once

#include <dxgi.h>

// The window and video mode the renderer asks for. Filled by 141DABB90 from r_fullscreen, r_monitor, r_mode,
// r_refreshRate, the window position and r_sceneResolutionMultiplier. IW's GfxWindowParms, with the monitor added
// and the refresh rate a float (r_refreshRate is a float dvar here).
struct GfxWindowParms
{
	HWND hwnd;
	float hz;           // r_refreshRate; 0 leaves the refresh rate to DXGI
	bool fullscreen;    // r_fullscreen == 1 (exclusive); windowed and borderless are 0
	int monitor;        // r_monitor, 1-based
	int x;
	int y;
	int sceneWidth;
	int sceneHeight;
	int displayWidth;   // from r_mode "WxH"
	int displayHeight;
	int unknown2C;
};
static_assert(sizeof(GfxWindowParms) == 0x30, "GfxWindowParms");

// Display modes, per monitor (DXGI output) of the adapter in use. Filled at startup by 141DAA790:
// IDXGIOutput::GetDisplayModeList(DXGI_FORMAT_R8G8B8A8_UNORM, DXGI_ENUM_MODES_SCALING), then modes under 800x600
// dropped, the rest sorted by sub_141DAA730 and duplicates (same size and rate) merged. Very likely members of IW's
// `dx` globals (the device, context and window are next to them); kept as separate symbols until that struct is laid out.
enum { DX_MAX_MONITORS = 8 };
extern int dx_monitorCount;
extern unsigned int dx_modeCount[DX_MAX_MONITORS];
extern DXGI_MODE_DESC *dx_modes[DX_MAX_MONITORS];

int sub_141DAA730(const void *a, const void *b);
void sub_141DA7A00(DXGI_SWAP_CHAIN_DESC *desc, const GfxWindowParms *wndParms);
