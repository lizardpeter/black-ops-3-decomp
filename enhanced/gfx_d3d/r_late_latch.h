// enhanced/gfx_d3d/r_late_latch.h: the late latch (P0021), shared by its overrides of CL_RenderScene
// (enhanced/client/cl_cgame.cpp), the render thread's scenes (enhanced/gfx_d3d/rb_backend.cpp) and the code
// matrices (enhanced/gfx_d3d/r_state.cpp). docs/late-latch.md.
#pragma once

struct dvar_t;
extern const dvar_t *r_lateLatch;  // registered by the enhanced 141D976E0 (enhanced/gfx_d3d/r_dvars.cpp)

// Main thread, around the main view's R_RenderScene: notes what the render thread needs to turn this frame's view
// later; returns the view parms to cull with (a copy widened by the latch's margin, or cullParms).
const void *R_LateLatchBeginScene(const char *refdef, const void *viewParms, const void *cullParms);
void R_LateLatchEndScene(const char *refdef, const void *viewParms);

// Render thread, before the frame's scenes are drawn: turns the main view by the mouse movement since the frame
// read the mouse.
void RB_LateLatch(char *frontEnd);

// For a source state drawing the latched view's gun lists: the view parms as the frame made them, else null.
const char *RB_LateLatchGunParms(const char *source);

// Helpers, exported for tests/enhanced/test_late_latch.py.
void R_LateLatchTurnAxis(float (*axis)[3], float yawDegrees, float pitchDegrees);
void R_LateLatchRebuildViewParms(char *parms);
void R_LateLatchWidenParms(char *parms, float marginDegrees);
