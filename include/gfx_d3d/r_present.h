// gfx_d3d/r_present.h (reconstructed: only what reconstructed code uses so far)
#pragma once

struct NV_GET_CURRENT_SLI_STATE
{
	unsigned int version;
	unsigned int maxNumAFRGroups;
	unsigned int numAFRGroups;
	unsigned int currentAFRIndex;
	unsigned int nextFrameAFRIndex;
	unsigned int previousFrameAFRIndex;
	unsigned int bIsCurAFRGroupNew;
};
#define NV_GET_CURRENT_SLI_STATE_VER1 0x1001C

// NvAPI, linked statically (nvapi64.lib's wrappers, which resolve each entry with nvapi_QueryInterface by id)
extern "C" int NvAPI_D3D_GetCurrentSLIState(void *pDevice, NV_GET_CURRENT_SLI_STATE *pSliState);  // 0x4B708B54
extern "C" int NvAPI_Stereo_IsActivated(void *stereoHandle, unsigned char *pIsStereoOn);           // 0x1FB0BC30
extern "C" int NvAPI_Stereo_SetConvergence(void *stereoHandle, float newConvergence);             // 0x3DD6B54B

void sub_141D46720();
