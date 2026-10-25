// The main view's scene. Source path assumed from the engine lineage (IW's CL_RenderScene is in cl_cgame.cpp).
// docs/late-latch.md, "The path", step 5.

#include "client/cl_cgame.h"

#define T7_SOURCE "client/cl_cgame.cpp"
#include <t7_static.h>

// 1413C9540  client/cl_cgame.cpp
// Notes the view's origin and first axis row, then renders the scene (141DE3D80, a tail call in the original): the
// main view, culled from cullParms (the view itself, or the view locked by the lock-view dvar 1486BF618) and drawn
// from viewParms, both made from the refdef by 141DE3D00 in CG_DrawActiveFrame.
void CL_RenderScene(const char *refdef, int a2, const void *viewParms, const void *cullParms, void *a5)
{
	cl_viewOrigin[0] = *(const float *)(refdef + REFDEF_VIEW_ORIGIN);
	cl_viewOrigin[1] = *(const float *)(refdef + REFDEF_VIEW_ORIGIN + 4);
	cl_viewOrigin[2] = *(const float *)(refdef + REFDEF_VIEW_ORIGIN + 8);
	cl_viewForward[0] = *(const float *)(refdef + REFDEF_VIEW_AXIS);
	cl_viewForward[1] = *(const float *)(refdef + REFDEF_VIEW_AXIS + 4);
	cl_viewForward[2] = *(const float *)(refdef + REFDEF_VIEW_AXIS + 8);
	sub_141DE3D80(refdef, a2, viewParms, cullParms, a5);
}
