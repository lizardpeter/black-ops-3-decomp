// client/cl_cgame.h (reconstructed: only what reconstructed code uses so far)
#pragma once

// The refdef (cg +0x131CF0) by offset: tanHalfFovX/Y +0x78/+0x7C, vieworg +0x88, viewaxis +0xA4 (3x3, forward
// first), the local client +0x1A680C.
enum
{
	REFDEF_VIEW_ORIGIN = 0x88,
	REFDEF_VIEW_AXIS = 0xA4,
	REFDEF_LOCAL_CLIENT = 0x1A680C,
};

extern float cl_viewOrigin[3];   // 149E736B4
extern float cl_viewForward[3];  // 149E736A8

// (refdef, a2, viewParms, cullParms, a5): the main scene's R_RenderScene wrapper
void sub_141DE3D80(const char *refdef, int a2, const void *viewParms, const void *cullParms, void *a5);
void CL_RenderScene(const char *refdef, int a2, const void *viewParms, const void *cullParms, void *a5);
