// P0021: CL_RenderScene notes the main view for the late latch and has it culled with a wider view
// (enhanced/gfx_d3d/r_late_latch.cpp, docs/late-latch.md). Otherwise the original (src/client/cl_cgame.cpp).

#include "client/cl_cgame.h"
#include "../gfx_d3d/r_late_latch.h"

// 1413C9540 CL_RenderScene
void CL_RenderScene(const char *refdef, int a2, const void *viewParms, const void *cullParms, void *a5)
{
	cl_viewOrigin[0] = *(const float *)(refdef + REFDEF_VIEW_ORIGIN);
	cl_viewOrigin[1] = *(const float *)(refdef + REFDEF_VIEW_ORIGIN + 4);
	cl_viewOrigin[2] = *(const float *)(refdef + REFDEF_VIEW_ORIGIN + 8);
	cl_viewForward[0] = *(const float *)(refdef + REFDEF_VIEW_AXIS);
	cl_viewForward[1] = *(const float *)(refdef + REFDEF_VIEW_AXIS + 4);
	cl_viewForward[2] = *(const float *)(refdef + REFDEF_VIEW_AXIS + 8);
	const void *cull = R_LateLatchBeginScene(refdef, viewParms, cullParms);
	sub_141DE3D80(refdef, a2, viewParms, cull, a5);
	R_LateLatchEndScene(refdef, viewParms);
}
