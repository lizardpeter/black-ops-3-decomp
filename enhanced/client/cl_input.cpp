// P0011: mouse aim in MW2019 units, the same at any field of view (B0016-B0019). P0012: CL_MouseMove turns the
// view in double precision (B0050).
//
// One device count turns the view by m_mouseSensitivity * 0.0066 degrees horizontally, MW2019's sensitivity unit,
// in hip fire and aiming down sights alike, at any FOV and any speed. The original's scale (src/client/cl_input.cpp)
// adds acceleration by speed (m_mouseAcceleration), a weapon's ADS sensitivity, and tan(current vertical FOV / 2) /
// tan(65-at-4:3 / 2), and can halve (m_filter) or average eight frames (m_mouseFilter); none of that applies here.
//
// CL_MouseMove (1413AE730, unchanged) multiplies the scaled movement by m_yaw (yaw) and m_pitch (pitch), so the
// movement handed to it is counts * m_mouseSensitivity * 0.0066 / 0.022: at the defaults (0.022) the view turns
// exactly m_mouseSensitivity * 0.0066 degrees a count; the settings menu's vertical sensitivity (m_pitch) stays a
// vertical multiplier relative to 0.022 and its sign still inverts the mouse. m_mouseSensitivity, which the menu and
// config.ini set, is now in MW2019 units: default 1.5 (about 29 cm per 360 degrees at 3200 DPI), 0.01-100. The other
// dvars stay registered so the menu and config.ini keep working, but filter and acceleration are ignored.
// docs/input-sensitivity.md.

#include <math.h>

#include "universal/dvar.h"
#include "client/client.h"

#define T7_SOURCE "client/cl_input.cpp"
#include <t7_static.h>

T7_STATIC float s_lastMouseX T7_AT("", "s_lastMouseX");
T7_STATIC float s_lastMouseY T7_AT("", "s_lastMouseY");

// MW2019: one count turns the view by sensitivity * 0.0066 degrees. CL_MouseMove multiplies by m_yaw / m_pitch
// (default 0.022), so the scale handed to it is sensitivity * 0.0066 / 0.022.
static const float MW2019_DEGREES_PER_COUNT = 0.0066f;
static const float M_YAW_DEFAULT = 0.022f;

// The movement of this frame in plain counts: no m_filter halving, no m_mouseFilter averaging.
void CL_GetMouseMovement(int localClientNum, float *mx, float *my, bool consume)
{
	if (!consume)
	{
		*mx = s_lastMouseX;
		*my = s_lastMouseY;
		return;
	}
	*mx = (float)cl_mouseDx[cl_mouseIndex];
	*my = (float)cl_mouseDy[cl_mouseIndex];
	cl_mouseIndex ^= 1;
	s_lastMouseX = *mx;
	s_lastMouseY = *my;
	cl_mouseDx[cl_mouseIndex] = 0;
	cl_mouseDy[cl_mouseIndex] = 0;
}

// The last movement scaled to MW2019 units; nothing depends on the FOV, the weapon, ADS or the speed.
void sub_1413ACDF0(int localClientNum, float *mx, float *my)
{
	float scale = Dvar_GetFloat(m_mouseSensitivity) * (MW2019_DEGREES_PER_COUNT / M_YAW_DEFAULT);
	*my = scale * s_lastMouseY;
	*mx = scale * s_lastMouseX;
}

// The original registrations, with m_mouseSensitivity in MW2019 units.
void sub_141405E50()
{
	sub_141410080();
	m_pitch = Dvar_RegisterFloat(0x48063E85, "", 0.022f, -1.0f, 1.0f, 0x0, "", false);
	m_yaw = Dvar_RegisterFloat(0xF7BDFE42, "", 0.022f, -1.0f, 1.0f, 0x0, "", false);
	m_forward = Dvar_RegisterFloat(0x431D5220, "", 0.25f, -1.0f, 1.0f, 0x0, "", false);
	m_side = Dvar_RegisterFloat(0x058BEAA0, "", 0.25f, -1.0f, 1.0f, 0x0, "", false);
	m_filter = Dvar_RegisterBool(0xE1BDECFF, "", false, 0x0, "", false);
	m_mouseFilter = Dvar_RegisterFloat(0x95476D28, "", 0.0f, 0.0f, 10.0f, 0x0, "", false);
	m_mouseAcceleration = Dvar_RegisterFloat(0xA87F084A, "", 0.0f, 0.0f, 1.0f, 0x0, "", false);
	m_mouseSensitivity = Dvar_RegisterFloat(0x247B172F, "", 1.5f, 0.01f, 100.0f, 0x0, "", false);  // P0011: MW2019 units
	Dvar_RegisterFloat(0xFA89035C, "", 0.0f, 0.0f, 100.0f, 0x0, "", false);  // cl_mouseAccel
	cl_freelook = Dvar_RegisterBool(0xA30619D8, "", true, 0x0, "", false);
	Dvar_RegisterString(0xBD8A89B8, "", "", 0x20, "", false);  // cl_motdString
	cl_ingame = Dvar_RegisterBool(0xD9428E7C, "", false, 0x20, "", false);
	cl_userTestBuild = Dvar_RegisterBool(0xB756FDBE, "", false, 0x100, "", false);
	Dvar_RegisterInt(0x703D51B4, "", 0, 0, 3, 0x0, "", false);  // mortarStrikesLeft
	player_name = Dvar_RegisterString(0xE2075DD8, "", "Unknown Soldier", 0x20, "", false);
	Dvar_RegisterBool(0x91CD4E52, "", false, 0x0, "", false);  // systemlink
	cl_voice = Dvar_RegisterBool(0xA55D0A3B, "", true, 0x0, "", false);
	maxVoicePacketsPerFrame = Dvar_RegisterInt(0x40714298, "", 10, 0, 500, 0x0, "", false);
	cl_timeout = Dvar_RegisterFloat(0xF5FB9F58, "", 20.0f, 0.0f, 3600.0f, 0x0, "", false);
	cl_connectTimeout = Dvar_RegisterFloat(0x201D7CBC, "", 120.0f, 0.0f, 3600.0f, 0x0, "", false);
	cl_connectionAttempts = Dvar_RegisterInt(0xDBE2D1E9, "", 40, 0, 2147483647, 0x0, "", false);
	Dvar_RegisterBool(0x59BEE1FA, "", false, 0x0, "", false);  // doublescreen
	splitscreen = Dvar_RegisterBool(0x2016892B, "", false, 0x0, "", false);
	splitscreen_playerCount = Dvar_RegisterInt(0xE84000BE, "", 1, 1, 2, 0x0, "", false);
	splitscreen_horizontal = Dvar_RegisterBool(0x2FAFEC8A, "", false, 0x10, "", false);
	Dvar_RegisterFloat(0xE7BC727D, "", 0.25f, 0.0f, 10.0f, 0x1000, "", false);  // cl_profileWriteLimiter
	cl_disableHeroRenders = Dvar_RegisterBool(0xF6E7B260, "", true, 0x0, "", false);
}

static inline signed char ClampChar(int i)
{
	if (i < -128)
		return (signed char)-128;
	return (signed char)(i > 127 ? 127 : i);
}

#define CL_FIELD(type, cl, offset) (*(type *)((cl) + (offset)))
#define CMD_FIELD(type, cmd, offset) (*(type *)((char *)(cmd) + (offset)))

// The cgame's limit for one turn, scaled to this frame: max(-cap, min(delta, cap)), cap = limit * frame seconds.
// With `limited` (cl +0xB8 == 1 and not cl +0x790 bit 0) a limit outside (0, 360] means 360 degrees a second.
static inline double CL_CapTurn(double delta, float limit, bool limited, float frameSeconds)
{
	if (limited ? !(limit > 0.0f) || !(360.0f - limit >= 0.0f) : false)
		limit = 360.0f;
	else if (!(limit > 0.0f))
		return delta;
	double cap = (double)(limit * frameSeconds);
	double upper = delta - cap >= 0.0 ? cap : delta;
	double lower = -cap;
	return lower - upper >= 0.0 ? lower : upper;
}

// The view angles as CL_MouseMove last left them, in double precision, per local client (0 pitch, 1 yaw). Anything
// else that changes the float angles (spawning, the cgame's limits, aim assist) is picked up the next time.
static double s_viewAngles[2][2];
static float s_viewAnglesWritten[2][2];

static inline float &CL_ViewAngleField(char *cl, int axis)
{
	return CL_FIELD(float, cl, axis ? 0xB8CC : 0xB8C8);
}

static double CL_ViewAngle(char *cl, int localClientNum, int axis)
{
	float current = CL_ViewAngleField(cl, axis);
	if (current != s_viewAnglesWritten[localClientNum & 1][axis] || current != current)
		s_viewAngles[localClientNum & 1][axis] = current;
	return s_viewAngles[localClientNum & 1][axis];
}

static void CL_SetViewAngle(char *cl, int localClientNum, int axis, double angle)
{
	s_viewAngles[localClientNum & 1][axis] = angle;
	s_viewAnglesWritten[localClientNum & 1][axis] = (float)angle;
	CL_ViewAngleField(cl, axis) = (float)angle;
}

// For tests/enhanced: where the double-precision angles live.
double *CL_EnhancedViewAngles()
{
	return &s_viewAngles[0][0];
}

// 1413AE730 CL_MouseMove, with the view angles turned in double precision (P0012): the same movement split over
// more frames ends at the same angle, and a far-turned yaw keeps its resolution. Otherwise the original: yaw by m_yaw, pitch by m_pitch (or forward/back with m_forward when mouse look is
// off), strafe with m_side while +strafe is held, each turn capped by the cgame's speed limits for this frame; the
// clamped mouse amounts go into the command (+0x3B pitch, +0x3C yaw), then aim assist corrects the view.
void CL_MouseMove(int localClientNum, usercmd_s *cmd)
{
	char *cl = CL_GetLocalClientGlobals(localClientNum);
	if (!cls_frametime)
		return;
	if (CL_FIELD(unsigned long long, cl, 0xC0) & 0x400000010000000ULL)
		return;
	if (CL_FIELD(int, cl, 0x10C) == 0x3F)
		return;
	if (CL_FIELD(unsigned char, cl, 0xA34) & 8)
		return;
	float frameSeconds = (float)cls_frametime * 0.001f;
	float my;
	float mx;
	sub_1413ACDF0(localClientNum, &mx, &my);
	if (!sub_142756F90(CG_GetPredictedPlayerState(localClientNum)))
	{
		bool lockMove = false;
		if ((CL_FIELD(unsigned int, cl, 0xD0) & 0x200) && unk_1494B2DC8 != 2)
		{
			lockMove = true;
			CMD_FIELD(unsigned short, cmd, 0x38) = 0;
		}
		if (mx != 0.0f || my != 0.0f)
		{
			int yawAmount = 0;
			int pitchAmount = 0;
			bool limited = CL_FIELD(int, cl, 0xB8) == 1 && !(CL_FIELD(unsigned char, cl, 0x790) & 1);
			long long kb = (long long)localClientNum * KB_STRIDE;
			if (kb_strafeActive[kb])
			{
				if (!lockMove)
				{
					float side = Dvar_GetFloat(m_side);
					int moved = (int)floorf(side * mx + 0.5f);
					CMD_FIELD(signed char, cmd, 0x39) = ClampChar(CMD_FIELD(signed char, cmd, 0x39) + moved);
				}
			}
			else
			{
				float yawSpeed = Dvar_GetFloat(m_yaw);
				double delta = CL_CapTurn((double)yawSpeed * mx, CL_FIELD(float, cl, 0xB7D4), limited, frameSeconds);
				CL_SetViewAngle(cl, localClientNum, 1, CL_ViewAngle(cl, localClientNum, 1) - delta);
				float amount = 127.0f - mx >= 0.0f ? mx : 127.0f;
				yawAmount = -(int)amount;
			}
			if ((kb_mlookActive[kb] || Dvar_GetBool(cl_freelook)) && !kb_strafeActive[kb])
			{
				float pitchSpeed = Dvar_GetFloat(m_pitch);
				double delta = CL_CapTurn((double)pitchSpeed * my, CL_FIELD(float, cl, 0xB7D0), limited, frameSeconds);
				CL_SetViewAngle(cl, localClientNum, 0, CL_ViewAngle(cl, localClientNum, 0) + delta);
				float amount = 127.0f - my >= 0.0f ? my : 127.0f;
				pitchAmount = (int)((float)(Dvar_GetFloat(m_pitch) > 0.0f ? 1 : -1) * amount);
			}
			else if (!lockMove)
			{
				float forward = Dvar_GetFloat(m_forward);
				int moved = (int)floorf(forward * my + 0.5f);
				CMD_FIELD(signed char, cmd, 0x38) = ClampChar(CMD_FIELD(signed char, cmd, 0x38) - moved);
			}
			CMD_FIELD(signed char, cmd, 0x3B) = ClampChar(CMD_FIELD(signed char, cmd, 0x3B) + pitchAmount);
			CMD_FIELD(signed char, cmd, 0x3C) = ClampChar(CMD_FIELD(signed char, cmd, 0x3C) + yawAmount);
		}
	}
	if (!cl_localClientActive[localClientNum * 9] || !sub_1408A5010(localClientNum))
		return;
	AimInput input;
	input.deltaTime = frameSeconds;
	input.deltaTimeScaled = (float)cls_aimFrametime * 0.001f;
	input.pitch = CL_FIELD(float, cl, 0xB8C8);
	input.pitchAxis = 0.0f;
	input.pitchMax = 0.0f;
	input.yaw = CL_FIELD(float, cl, 0xB8CC);
	input.yawAxis = 0.0f;
	input.yawMax = 0.0f;
	input.forwardAxis = 0.0f;
	input.rightAxis = 0.0f;
	input.mouseInput = 1;
	input.buttons[0] = CL_FIELD(unsigned int, cl, 0xB8B8) | CMD_FIELD(unsigned int, cmd, 4);
	input.buttons[1] = CL_FIELD(unsigned int, cl, 0xB8BC) | CMD_FIELD(unsigned int, cmd, 8);
	input.buttons[2] = CL_FIELD(unsigned int, cl, 0xB8C0) | CMD_FIELD(unsigned int, cmd, 0xC);
	input.localClientNum = localClientNum;
	const char *ps = (const char *)CG_GetPredictedPlayerState(localClientNum);
	input.ps = (const playerState_s *)ps;
	input.ps994 = *(const unsigned short *)(ps + 0x994);
	input.ps99C = *(const unsigned short *)(ps + 0x99C);
	input.adsFraction = *(const float *)(ps + 0x2FC);
	AimOutput output;
	if (!(*(const unsigned long long *)(ps + 0x10) & 0x20000000000000ULL) || CL_FIELD(int, cl, 0xB8) - 2U <= 1)
	{
		AimAssist_UpdateMouseInput(&input, &output);
	}
	else
	{
		input.pitchAxis = my;
		input.yawAxis = mx;
		if (CMD_FIELD(int, cmd, 4) < 0)
			CMD_FIELD(unsigned int, cmd, 8) |= 0x30000000;
		output.ps994 = input.ps994;
		output.ps99C = input.ps99C;
		output.pitch = input.pitch;
		output.yaw = input.yaw;
		if (my != 0.0f || mx != 0.0f)
		{
			float baseX;
			float baseY;
			const dvar_t *direction = aim_mouseDirection;
			if (!direction)
			{
				baseX = 0.0f;
				baseY = 0.0f;
			}
			else
			{
				const dvar_t *variant = direction;
				if (*(const int *)((const char *)direction + 0x1C) == 0xF)
				{
					variant = sub_142396BB0(direction, (int)(com_sessionModeState << 28) >> 28);
					direction = aim_mouseDirection;
				}
				baseX = *(const float *)((const char *)variant + 0x28);
				baseY = *(const float *)((const char *)variant + 0x2C);
			}
			float x = mx + baseX;
			float y = my + baseY;
			float length = sqrtf(y * y + x * x);
			float one = 1.0f;
			if (-length >= 0.0f)
				length = one;
			float inverse = one / length;
			x = x * inverse;
			y = y * inverse;
			Dvar_SetVec2(direction, x * 250.0f, y * 250.0f);
			unsigned long long packed = (unsigned long long)*(unsigned int *)&y
			                            | (unsigned long long)*(unsigned int *)&x << 32;
			sub_140104EA0(packed, &input, &output);
		}
	}
	CL_FIELD(float, cl, 0xB8C8) = output.pitch;
	CL_FIELD(float, cl, 0xB8CC) = output.yaw;
	CMD_FIELD(unsigned short, cmd, 0x3E) = output.ps99C;
	CMD_FIELD(unsigned short, cmd, 0x40) = output.ps994;
}
