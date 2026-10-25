// enhanced/gfx_d3d/r_flip.h: the enhanced build's presentation state, shared by its overrides of the swap chain's
// creation and resize (enhanced/gfx_d3d/r_init.cpp), the present (enhanced/gfx_d3d/r_present.cpp) and IN_Frame
// (enhanced/win32/win_input.cpp). records/patches.tsv P0017, P0018, P0019; docs/presentation.md.
#pragma once

#include <dxgi.h>

extern bool r_flipModel;                   // dx_swapChain is DXGI_SWAP_EFFECT_FLIP_DISCARD
extern bool r_flipAllowTearing;            // and was made with DXGI_SWAP_CHAIN_FLAG_ALLOW_TEARING
extern unsigned int r_swapChainFlags;      // the Flags dx_swapChain was made with: ResizeBuffers must pass the same

HRESULT R_CreateSwapChain(void *factory, const DXGI_SWAP_CHAIN_DESC *originalDesc);
void R_AcquireFrameLatencyWaitable();
void R_CountPresent();
void R_WaitForFrameLatency();
HRESULT R_PresentFlip(bool vsync);
