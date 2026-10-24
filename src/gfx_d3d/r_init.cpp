// Renderer start-up: display modes and the swap chain description. Original function names unknown; source path
// assumed from the engine lineage (IW's gfx_d3d/r_init.cpp creates the device and swap chain).
//
// How BO3 picks its refresh rate (docs/refresh-rate.md): r_refreshRate is a number the player chooses, not "whatever
// Windows is set to". In exclusive fullscreen the swap chain asks DXGI for an exact display mode, and
// sub_141DA7A00 picks, among the enumerated modes of the chosen monitor at the chosen resolution, the one whose rate
// is closest to r_refreshRate. Windowed and borderless never get a mode: the desktop's own rate applies.

#include <dxgi.h>
#include <math.h>

#include "universal/dvar.h"
#include "gfx_d3d/r_dvars.h"
#include "gfx_d3d/r_init.h"

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
