// P0021: the late latch (B0051). The render thread turns the main view by the mouse movement that arrived after the
// frame read the mouse, just before it draws the frame, the way Rust-test's peek_motion() does. docs/late-latch.md.
//
// The render thread draws a frame while the main thread builds the next one, so the view the GPU draws was fixed a
// whole main-thread frame earlier, in CG_DrawActiveFrame. Here:
// - CL_RenderScene (main thread, enhanced/client/cl_cgame.cpp) notes per frontend buffer what the render thread will
//   need: the scene R_RenderScene makes for the main view, the mouse counts the frame took, how far a count turns
//   the view, and the previous view this frame's reprojection used. It hands R_RenderScene a cull view widened by
//   a margin, so a late turn finds nothing culled at the screen's edges.
// - At the start of the frame's scenes (render thread, enhanced/gfx_d3d/rb_backend.cpp) the view is turned by the
//   counts read since the frame's take (at most the margin each way), its view parms made again, the TAA/motion-
//   vector reprojection made again from them, and the previous view the next frame starts from replaced. The
//   counts stay with the game: the next frame takes them as usual, so gameplay sees nothing of this.
// - The gun is placed in the world from the view as the frame made it, so its draw lists keep that view
//   (enhanced/gfx_d3d/r_state.cpp): it stays where the game put it on screen while the world turns.
//
// Nothing happens unless r_lateLatch is on (the default), there is one local client, and this frame's mouse turned
// the view freely (CL_MouseMove: mouse look on, no strafe, no turn cap) and the view followed it (the view turned as
// the client's angles did since the last frame: not a killcam, vehicle or scripted camera).

#include <math.h>
#include <string.h>

#include "universal/dvar.h"
#include "client/client.h"
#include "client/cl_cgame.h"
#include "gfx_d3d/r_state.h"
#include "gfx_d3d/rb_backend.h"
#include "r_late_latch.h"

const dvar_t *r_lateLatch;

extern char *frontEndDataOut;            // 1486C3A78: the frontend data the main thread is filling
extern int dword_14A333F74;              // 14A333F74: R_RenderScene's next scene index, 0 at R_BeginFrame
extern unsigned int dword_1546790B8;     // 1546790B8: which of the two frontend buffers is being filled
extern char r_previousViewParms[];       // 148705570: per local client, the last main view (0x290 each)
extern char *unk_148705550;              // 148705550: the render targets' table (+0x774A, +0x6CC0 + 0x150 each)
int sub_141D634D0();                     // the anti-aliasing mode (3-5 temporal; 4 and 5 jitter the projection)
char sub_141DDC6C0(float *reprojection, void *reprojectionView, char *viewInfo, const char *refdef, void *input,
                   const char *viewParms, const char *previousViewParms);
bool CL_LateLatchTurn(int localClientNum, float *yawPerCount, float *pitchPerCount);
void IN_RawMouseTotals(long long *readX, long long *readY, long long *takenX, long long *takenY);

enum
{
	VIEW_PARMS_SIZE = 0x290,
	VIEW_PARMS_PROJECTION = 0x40,
	VIEW_PARMS_PROJECTION2 = 0x80,
	VIEW_PARMS_VIEW_PROJECTION = 0xC0,
	VIEW_PARMS_VIEW_PROJECTION2 = 0x100,
	VIEW_PARMS_INVERSE_VIEW_PROJECTION = 0x140,
	VIEW_PARMS_UNJITTERED_PROJECTION = 0x180,
	VIEW_PARMS_UNJITTERED_VIEW_PROJECTION = 0x1C0,
	VIEW_PARMS_INVERSE_UNJITTERED = 0x200,
	VIEW_PARMS_ORIGIN = 0x240,
	VIEW_PARMS_AXIS = 0x250,
	VIEW_PARMS_TAN_HALF_FOV = 0x280,
	FRONTEND_REPROJECTION = 0xF9590,
	FRONTEND_REPROJECTION_VIEW = 0xF95A0,
	VIEW_INFO_CODE_INPUT = 0x400,
	CODE_INPUT_REPROJECTION = 0x1D30,
	REFDEF_RENDER_TARGET = 0x24,
	REFDEF_FLAGS = 0x38,
	REFDEF_74 = 0x74,
	REFDEF_EXTRA_CAM = 0x1A681C,
	REFDEF_SIZE = 0x1A6820,
};

static const float DEGREES = 57.29577951308232f;
static const float RADIANS = 0.017453292519943295f;
static const float PITCH_LIMIT = 85.0f;
static const float MARGIN_MIN = 1.0f;
static const float MARGIN_MAX = 8.0f;

struct LateLatchFrame
{
	char *frontEnd;
	char *viewInfo;
	char *viewSlot;
	int scene;
	int localClientNum;
	bool valid;
	long long takenX;
	long long takenY;
	float yawPerCount;
	float pitchPerCount;
	float margin;
	int refdefRenderTarget;
	unsigned int refdefFlags;
	float refdef74;
	int refdefExtraCam;
	char previous[VIEW_PARMS_SIZE];
	char cull[VIEW_PARMS_SIZE];
};

static LateLatchFrame s_frames[2];   // per frontend buffer
static bool s_follows;               // the view turned with the client's angles when they last moved
static float s_lastViewYaw, s_lastViewPitch, s_lastClientYaw, s_lastClientPitch;
static float s_lastTurn;             // the largest turn of the last latch, degrees (render thread -> main thread)
static char *s_gunViewInfo;          // the viewInfo turned this frame (render thread, read by the draw jobs)
static char s_unlatched[VIEW_PARMS_SIZE];
static char s_fakeRefdef[REFDEF_SIZE];

// a - b in (-180, 180]
static float AngleDelta(float a, float b)
{
	float d = a - b;
	return d - 360.0f * floorf((d + 180.0f) / 360.0f);
}

static float Clamp(float v, float lo, float hi)
{
	return v < lo ? lo : v > hi ? hi : v;
}

// Yaw and pitch (degrees, pitch positive down) of a forward vector.
static void ForwardAngles(const float *forward, float *yaw, float *pitch)
{
	*yaw = atan2f(forward[1], forward[0]) * DEGREES;
	*pitch = -asinf(Clamp(forward[2], -1.0f, 1.0f)) * DEGREES;
}

// The view turned by yaw (positive to the left, about the world's up) and pitch (positive down), its roll kept; the
// pitch stops at 85 degrees either way (or where it already is, if beyond).
void R_LateLatchTurnAxis(float (*axis)[3], float yawDegrees, float pitchDegrees)
{
	float yaw, pitch;
	ForwardAngles(axis[0], &yaw, &pitch);
	float roll = atan2f(axis[1][2], axis[2][2]) * DEGREES;
	float lo = pitch < -PITCH_LIMIT ? pitch : -PITCH_LIMIT;
	float hi = pitch > PITCH_LIMIT ? pitch : PITCH_LIMIT;
	pitch = Clamp(pitch + pitchDegrees, lo, hi);
	yaw += yawDegrees;
	float sy = sinf(yaw * RADIANS), cy = cosf(yaw * RADIANS);
	float sp = sinf(pitch * RADIANS), cp = cosf(pitch * RADIANS);
	float sr = sinf(roll * RADIANS), cr = cosf(roll * RADIANS);
	// AnglesToAxis: forward, left (the negated AngleVectors right), up
	axis[0][0] = cp * cy;
	axis[0][1] = cp * sy;
	axis[0][2] = -sp;
	axis[1][0] = sr * sp * cy - cr * sy;
	axis[1][1] = sr * sp * sy + cr * cy;
	axis[1][2] = sr * cp;
	axis[2][0] = cr * sp * cy + sr * sy;
	axis[2][1] = cr * sp * sy - sr * cy;
	axis[2][2] = cr * cp;
}

// The view matrix from the origin and axis, and every product of it, as R_SetupViewParms and 141DD52B0 make them;
// the projections (jittered and not) are left as they are.
void R_LateLatchRebuildViewParms(char *parms)
{
	float *view = (float *)parms;
	MatrixForViewer((const float *)(parms + VIEW_PARMS_ORIGIN), (const float(*)[3])(parms + VIEW_PARMS_AXIS), view);
	MatrixMultiply44(view, (const float *)(parms + VIEW_PARMS_PROJECTION), (float *)(parms + VIEW_PARMS_VIEW_PROJECTION));
	MatrixMultiply44(view, (const float *)(parms + VIEW_PARMS_PROJECTION2),
	                 (float *)(parms + VIEW_PARMS_VIEW_PROJECTION2));
	MatrixInverse44((const float *)(parms + VIEW_PARMS_VIEW_PROJECTION),
	                (float *)(parms + VIEW_PARMS_INVERSE_VIEW_PROJECTION));
	MatrixMultiply44(view, (const float *)(parms + VIEW_PARMS_UNJITTERED_PROJECTION),
	                 (float *)(parms + VIEW_PARMS_UNJITTERED_VIEW_PROJECTION));
	MatrixInverse44((const float *)(parms + VIEW_PARMS_UNJITTERED_VIEW_PROJECTION),
	                (float *)(parms + VIEW_PARMS_INVERSE_UNJITTERED));
}

// The view's field of view widened by marginDegrees at each edge (tanHalfFov and the projections' scale), with its
// products made again: the frustum 141E069A0 culls with.
void R_LateLatchWidenParms(char *parms, float marginDegrees)
{
	float *tanHalfFov = (float *)(parms + VIEW_PARMS_TAN_HALF_FOV);
	float scale[2];
	for (int i = 0; i < 2; i++)
	{
		float half = atanf(tanHalfFov[i]) + marginDegrees * RADIANS;
		if (half > 89.0f * RADIANS)
			half = 89.0f * RADIANS;
		float widened = tanf(half);
		scale[i] = tanHalfFov[i] / widened;
		tanHalfFov[i] = widened;
	}
	static const int projections[] = {VIEW_PARMS_PROJECTION, VIEW_PARMS_PROJECTION2, VIEW_PARMS_UNJITTERED_PROJECTION};
	for (int p : projections)
	{
		float *m = (float *)(parms + p);
		m[0] *= scale[0];
		m[5] *= scale[1];
	}
	R_LateLatchRebuildViewParms(parms);
}

static bool R_LateLatchEnabled()
{
	return r_lateLatch && Dvar_GetBool(r_lateLatch);
}

const void *R_LateLatchBeginScene(const char *refdef, const void *viewParms, const void *cullParms)
{
	LateLatchFrame *frame = &s_frames[dword_1546790B8 & 1];
	frame->valid = false;
	frame->viewInfo = nullptr;
	int localClientNum = *(const int *)(refdef + REFDEF_LOCAL_CLIENT);

	// does the view follow the client's angles? decided whenever they move
	char *cl = CL_GetLocalClientGlobals(0);
	float viewYaw, viewPitch;
	ForwardAngles((const float *)(refdef + REFDEF_VIEW_AXIS), &viewYaw, &viewPitch);
	float clientPitch = *(const float *)(cl + 0xB8C8);
	float clientYaw = *(const float *)(cl + 0xB8CC);
	float clientTurn[2] = {AngleDelta(clientYaw, s_lastClientYaw), AngleDelta(clientPitch, s_lastClientPitch)};
	float viewTurn[2] = {AngleDelta(viewYaw, s_lastViewYaw), viewPitch - s_lastViewPitch};
	float moved = fabsf(clientTurn[0]) + fabsf(clientTurn[1]);
	if (moved > 0.05f)
		s_follows = fabsf(viewTurn[0] - clientTurn[0]) + fabsf(viewTurn[1] - clientTurn[1]) <= 0.2f + 0.25f * moved;
	s_lastViewYaw = viewYaw;
	s_lastViewPitch = viewPitch;
	s_lastClientYaw = clientYaw;
	s_lastClientPitch = clientPitch;

	if (!R_LateLatchEnabled() || localClientNum != 0 || Dvar_GetBool(splitscreen) || !s_follows)
		return cullParms;
	if (!CL_LateLatchTurn(0, &frame->yawPerCount, &frame->pitchPerCount))
		return cullParms;
	long long readX, readY;
	IN_RawMouseTotals(&readX, &readY, &frame->takenX, &frame->takenY);
	frame->frontEnd = frontEndDataOut;
	frame->scene = dword_14A333F74;
	frame->localClientNum = localClientNum;
	frame->margin = Clamp(MARGIN_MIN + 1.5f * s_lastTurn, MARGIN_MIN, MARGIN_MAX);
	frame->refdefRenderTarget = *(const int *)(refdef + REFDEF_RENDER_TARGET);
	frame->refdefFlags = *(const unsigned int *)(refdef + REFDEF_FLAGS);
	frame->refdef74 = *(const float *)(refdef + REFDEF_74);
	frame->refdefExtraCam = *(const int *)(refdef + REFDEF_EXTRA_CAM);
	memcpy(frame->previous, r_previousViewParms + (long long)localClientNum * VIEW_PARMS_SIZE, VIEW_PARMS_SIZE);
	memcpy(frame->cull, cullParms, VIEW_PARMS_SIZE);
	R_LateLatchWidenParms(frame->cull, frame->margin);
	frame->valid = true;
	return frame->cull;
}

void R_LateLatchEndScene(const char *refdef, const void *viewParms)
{
	LateLatchFrame *frame = &s_frames[dword_1546790B8 & 1];
	if (!frame->valid)
		return;
	char *frontEnd = frame->frontEnd;
	// R_RenderScene may skip the scene (a dvar): only a scene it made at the index noted is turned
	if (frontEnd != frontEndDataOut || *(int *)(frontEnd + FRONTEND_LAST_SCENE) != frame->scene ||
	    *(int *)(frontEnd + FRONTEND_SCENE_COUNT) != frame->scene + 1)
	{
		frame->valid = false;
		return;
	}
	frame->viewInfo = *(char **)(frontEnd + FRONTEND_SCENES) + (long long)frame->scene * VIEW_INFO_SIZE;
	frame->viewSlot = (char *)viewParms;
}

// 141DDC6C0 jitters the reprojection (anti-aliasing modes 4 and 5) by 141DDC5A0's subpixel offset, which takes the
// frame's parity from the frontend data the main thread is filling: on the render thread that is the next frame's,
// so the offset comes out mirrored. The jitter is a translation applied last (M * J), so the frame's own is put
// back by moving each matrix's first two columns by its fourth times the difference: the parity flip moves the
// offset by half a pixel's worth both ways (141DDC5A0: -0.25/+0.25 on even frames, +0.25/-0.25 on odd ones, the same
// extra quarter either way).
static void RB_LateLatchFixJitter(char *frontEnd, int renderTarget)
{
	int mode = sub_141D634D0();
	if (mode != 4 && mode != 5)
		return;
	unsigned int frameParity = *(unsigned int *)(frontEnd + 0x8A364) & 1;
	unsigned int callParity = *(unsigned int *)(frontEndDataOut + 0x8A364) & 1;
	if (frameParity == callParity)
		return;
	char *targets = unk_148705550;
	unsigned long long target = *(char *)(targets + 0x774A) ? (unsigned int)renderTarget : 0;
	float width = (float)*(unsigned short *)(targets + target * 0x150 + 0x6CC0);
	float height = (float)*(unsigned short *)(targets + target * 0x150 + 0x6CC2);
	float dx = (frameParity ? 0.5f : -0.5f) * (2.0f / width);
	float dy = (frameParity ? -0.5f : 0.5f) * (2.0f / height);
	float *blocks[] = {*(float **)(frontEnd + FRONTEND_REPROJECTION), *(float **)(frontEnd + FRONTEND_REPROJECTION_VIEW)};
	for (float *block : blocks)
		for (int m = 0; m < 2; m++)
			for (int row = 0; row < 4; row++)
			{
				float *r = block + m * 16 + row * 4;
				r[0] += r[3] * dx;
				r[1] += r[3] * dy;
			}
}

void RB_LateLatch(char *frontEnd)
{
	s_gunViewInfo = nullptr;
	LateLatchFrame *frame = nullptr;
	for (LateLatchFrame &f : s_frames)
		if (f.valid && f.frontEnd == frontEnd && f.viewInfo)
			frame = &f;
	if (!frame)
		return;
	frame->valid = false;
	if (!R_LateLatchEnabled())
		return;

	long long readX, readY, takenX, takenY;
	IN_RawMouseTotals(&readX, &readY, &takenX, &takenY);
	float yaw = Clamp((float)(readX - frame->takenX) * frame->yawPerCount, -frame->margin, frame->margin);
	float pitch = Clamp((float)(readY - frame->takenY) * frame->pitchPerCount, -frame->margin, frame->margin);
	float turn = fabsf(yaw) > fabsf(pitch) ? fabsf(yaw) : fabsf(pitch);
	__atomic_store_n((int *)&s_lastTurn, *(int *)&turn, __ATOMIC_RELAXED);
	if (yaw == 0.0f && pitch == 0.0f)
		return;

	char *parms = frame->viewInfo;  // the viewInfo starts with its view parms
	memcpy(s_unlatched, parms, VIEW_PARMS_SIZE);
	R_LateLatchTurnAxis((float(*)[3])(parms + VIEW_PARMS_AXIS), yaw, pitch);
	R_LateLatchRebuildViewParms(parms);
	memcpy(frame->viewSlot, parms, VIEW_PARMS_SIZE);

	// the reprojection (TAA, motion vectors) from the turned view, as 141DDDC20 made it from the frame's
	// only these fields are read (141DDC6C0, 141DDC5A0); the rest stays zero
	*(int *)(s_fakeRefdef + REFDEF_RENDER_TARGET) = frame->refdefRenderTarget;
	*(unsigned int *)(s_fakeRefdef + REFDEF_FLAGS) = frame->refdefFlags;
	*(float *)(s_fakeRefdef + REFDEF_74) = frame->refdef74;
	*(int *)(s_fakeRefdef + REFDEF_EXTRA_CAM) = frame->refdefExtraCam;
	char reprojected = sub_141DDC6C0(*(float **)(frontEnd + FRONTEND_REPROJECTION), *(void **)(frontEnd + FRONTEND_REPROJECTION_VIEW),
	              frame->viewInfo, s_fakeRefdef, *(char **)(frame->viewInfo + VIEW_INFO_CODE_INPUT) + CODE_INPUT_REPROJECTION,
	              parms, frame->previous);
	if (reprojected)
		RB_LateLatchFixJitter(frontEnd, frame->refdefRenderTarget);

	// the next frame reprojects from the view shown, if the main thread hasn't moved on past this one
	char *previous = r_previousViewParms + (long long)frame->localClientNum * VIEW_PARMS_SIZE;
	if (!memcmp(previous, s_unlatched, VIEW_PARMS_SIZE))
		memcpy(previous, parms, VIEW_PARMS_SIZE);

	s_gunViewInfo = frame->viewInfo;
}

const char *RB_LateLatchGunParms(const char *source)
{
	char *viewInfo = s_gunViewInfo;
	if (!viewInfo || *(char *const *)(source + SOURCE_VIEW_INFO) != viewInfo ||
	    *(const int *)(source + SOURCE_VIEW_MODEL_MODE) != 1)
		return nullptr;
	return s_unlatched;
}
