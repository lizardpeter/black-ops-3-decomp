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

// The interface ids the swap chain's creation asks for (the original's own copies)
extern const GUID IID_IDXGIDevice1;
extern const GUID IID_IDXGIAdapter1;
extern const GUID IID_IDXGIFactory1;

typedef struct D3D11_BUFFER_DESC
{
	UINT ByteWidth;
	UINT Usage;
	UINT BindFlags;
	UINT CPUAccessFlags;
	UINT MiscFlags;
	UINT StructureByteStride;
} D3D11_BUFFER_DESC;
#define D3D11_USAGE_DYNAMIC 2
#define D3D11_BIND_CONSTANT_BUFFER 4
#define D3D11_CPU_ACCESS_WRITE 0x10000

// The current video mode (set by 141DCDA90 when the render targets are made)
extern int vidConfig_sceneWidth;
extern int vidConfig_sceneHeight;
extern int vidConfig_displayWidth;
extern int vidConfig_displayHeight;

extern HWND dx_windowHwnd;  // the game window, copied from g_hWnd by 141DAB970 once it is shown
extern void (*dx_videoChangeCallback)(bool sizeChanged);
extern void *gfx_renderTargetState;  // 0x6E views of 0xAE0 bytes; +0x20E8 the frame's first view
extern void *sys_quitEvent;          // set when a message pump sees WM_QUIT

HRESULT sub_141DAB250(const GfxWindowParms *wndParms);
void sub_141DAD0C0();
void sub_141DAC020();
void sub_141DABB90(GfxWindowParms *wndParms);
void sub_141DAB810(const GfxWindowParms *wndParms);
void sub_141DAC3E0();
void sub_141DAB1C0(void *context);
void sub_141DA7B50(const GfxWindowParms *wndParms);
void sub_141DD3730(void *view, int unbind);
void sub_141DD2C80(void *view, unsigned int slot);
void sub_141DCA670();
void sub_141DCDA90(int sceneWidth, int sceneHeight, int displayWidth, int displayHeight, bool unknown, bool unknown2);
void sub_141DB5010();
void sub_141DEBFA0();
