// DXGI structures, as the Windows SDK lays them out (dxgitype.h, dxgi.h).
//
// Build environment, not game source. Only the plain structures and enum values reconstructed code uses; no COM
// interfaces yet. Add members here as reconstructed code needs them.
#pragma once

#include <windows.h>

typedef enum DXGI_FORMAT
{
	DXGI_FORMAT_UNKNOWN = 0,
	DXGI_FORMAT_R8G8B8A8_UNORM = 28,
} DXGI_FORMAT;

typedef enum DXGI_MODE_SCANLINE_ORDER
{
	DXGI_MODE_SCANLINE_ORDER_UNSPECIFIED = 0,
} DXGI_MODE_SCANLINE_ORDER;

typedef enum DXGI_MODE_SCALING
{
	DXGI_MODE_SCALING_UNSPECIFIED = 0,
} DXGI_MODE_SCALING;

typedef enum DXGI_SWAP_EFFECT
{
	DXGI_SWAP_EFFECT_DISCARD = 0,
} DXGI_SWAP_EFFECT;

typedef struct DXGI_RATIONAL
{
	UINT Numerator;
	UINT Denominator;
} DXGI_RATIONAL;

typedef struct DXGI_MODE_DESC
{
	UINT Width;
	UINT Height;
	DXGI_RATIONAL RefreshRate;
	DXGI_FORMAT Format;
	DXGI_MODE_SCANLINE_ORDER ScanlineOrdering;
	DXGI_MODE_SCALING Scaling;
} DXGI_MODE_DESC;

typedef struct DXGI_SAMPLE_DESC
{
	UINT Count;
	UINT Quality;
} DXGI_SAMPLE_DESC;

typedef UINT DXGI_USAGE;
#define DXGI_USAGE_SHADER_INPUT 0x10
#define DXGI_USAGE_RENDER_TARGET_OUTPUT 0x20

#define DXGI_SWAP_CHAIN_FLAG_ALLOW_MODE_SWITCH 2

typedef struct DXGI_SWAP_CHAIN_DESC
{
	DXGI_MODE_DESC BufferDesc;
	DXGI_SAMPLE_DESC SampleDesc;
	DXGI_USAGE BufferUsage;
	UINT BufferCount;
	HWND OutputWindow;
	BOOL Windowed;
	DXGI_SWAP_EFFECT SwapEffect;
	UINT Flags;
} DXGI_SWAP_CHAIN_DESC;

static_assert(sizeof(DXGI_MODE_DESC) == 0x1C, "DXGI_MODE_DESC");
static_assert(sizeof(DXGI_SWAP_CHAIN_DESC) == 0x48, "DXGI_SWAP_CHAIN_DESC");

// ---- COM basics and the presentation pieces (gfx_d3d/r_init.cpp, gfx_d3d/r_present.cpp) ----

typedef long HRESULT;

typedef struct _GUID
{
	unsigned long Data1;
	unsigned short Data2;
	unsigned short Data3;
	unsigned char Data4[8];
} GUID;

typedef struct HMONITOR__ *HMONITOR;

typedef struct DXGI_OUTPUT_DESC
{
	unsigned short DeviceName[32];
	RECT DesktopCoordinates;
	BOOL AttachedToDesktop;
	UINT Rotation;
	HMONITOR Monitor;
} DXGI_OUTPUT_DESC;
static_assert(sizeof(DXGI_OUTPUT_DESC) == 0x60, "DXGI_OUTPUT_DESC");

#define DXGI_MWA_NO_WINDOW_CHANGES 1
#define DXGI_MWA_NO_ALT_ENTER 2
#define DXGI_MWA_NO_PRINT_SCREEN 4

#define DXGI_ERROR_INVALID_CALL ((HRESULT)0x887A0001)
#define DXGI_ERROR_NOT_FOUND ((HRESULT)0x887A0002)
#define DXGI_ERROR_DEVICE_REMOVED ((HRESULT)0x887A0005)
#define DXGI_ERROR_DEVICE_HUNG ((HRESULT)0x887A0006)
#define DXGI_ERROR_DEVICE_RESET ((HRESULT)0x887A0007)
#define DXGI_ERROR_DRIVER_INTERNAL_ERROR ((HRESULT)0x887A0020)

// DXGI 1.3-1.5: not used by the original, only by the enhanced presentation (the public values)
#define DXGI_SWAP_EFFECT_FLIP_DISCARD ((DXGI_SWAP_EFFECT)4)
#define DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT 0x40
#define DXGI_SWAP_CHAIN_FLAG_ALLOW_TEARING 0x800
#define DXGI_PRESENT_ALLOW_TEARING 0x200
#define DXGI_FEATURE_PRESENT_ALLOW_TEARING 0
