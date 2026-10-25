// gfx_d3d/com_call.h: calling Direct3D 11 / DXGI COM methods from reconstructed code.
//
// Build environment, not game source: the reconstruction is built without the Windows SDK, so instead of d3d11.h
// it calls methods through the object's vtable by slot number. The behaviour is the original's
// `obj->lpVtbl->Method(obj, ...)`: load the vtable from the object, call the slot with the object as the first
// argument. Ported from ghosts-decomp. Each slot below is checked against a call in the Store build (the address
// given), or is a public position the original never uses (marked "public").
#pragma once

template <typename R, typename... A>
inline R ComCall(const void *object, unsigned int slot, A... args)
{
	typedef R (*Method)(const void *, A...);
	return ((Method)(*(void *const *const *)object)[slot])(object, args...);
}

// IUnknown
enum IUnknownSlot : unsigned int
{
	UNK_QueryInterface = 0,  // 141DAB2AF `call [rax]`
	UNK_AddRef = 1,
	UNK_Release = 2,         // 141DAB36D `call [rax+0x10]`
};

// IDXGIObject
enum DXGIObjectSlot : unsigned int
{
	OBJECT_GetParent = 6,  // 141DAB2CD `call [rax+0x30]`
};

// IDXGIFactory
enum DXGIFactorySlot : unsigned int
{
	FACTORY_MakeWindowAssociation = 8,  // 141DAB362 `call [rax+0x40]`
	FACTORY_CreateSwapChain = 10,       // 1423F3CE0 (window procedure, message 0x8042) `call [rax+0x50]`
	FACTORY5_CheckFeatureSupport = 28,  // public (IDXGIFactory5)
};

// IDXGIOutput
enum DXGIOutputSlot : unsigned int
{
	OUTPUT_GetDesc = 7,  // 141DAB3AE `call [rax+0x38]`
};

// IDXGISwapChain (0-17), IDXGISwapChain2 (29-35)
enum DXGISwapChainSlot : unsigned int
{
	SWAPCHAIN_Present = 8,                     // 1423F3CE0 (message 0x8043) `call [rax+0x40]`
	SWAPCHAIN_GetBuffer = 9,                   // 141DD27B0 `call [rax+0x48]`
	SWAPCHAIN_SetFullscreenState = 10,         // 1423F3CE0 (message 0x8044) `call [rax+0x50]`
	SWAPCHAIN_GetFullscreenState = 11,         // 141DAB447 `call [rax+0x58]`
	SWAPCHAIN_ResizeBuffers = 13,              // 141DAD29B `call [r10+0x68]`
	SWAPCHAIN_ResizeTarget = 14,               // 141DAC790 `call [rax+0x70]`
	SWAPCHAIN_GetContainingOutput = 15,        // 141DAB39A `call [rax+0x78]`
	SWAPCHAIN2_SetMaximumFrameLatency = 31,    // public
	SWAPCHAIN2_GetFrameLatencyWaitableObject = 33,  // public
};

// ID3D11Device
enum D3D11DeviceSlot : unsigned int
{
	DEV_CreateBuffer = 3,                // 141DAB4F9 `call [r10+0x18]`
	DEV_GetDeviceRemovedReason = 39,     // 141D4689C `call [rdx+0x138]`
};

// ID3D11DeviceContext
enum D3D11ContextSlot : unsigned int
{
	CTX_OMSetRenderTargets = 33,  // public
	CTX_OMGetRenderTargets = 89,  // public
	CTX_Flush = 111,              // 141DAD2A9 `call [rax+0x378]`
};
