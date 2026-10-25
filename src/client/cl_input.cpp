// Mouse input: from device counts to the scaled movement CL_MouseMove (1413AE730) turns into view angles. Original
// names partly from the engine lineage (Ghosts' client_mp/cl_input.cpp has the same three steps); source path
// assumed. docs/input-sensitivity.md.
//
// One count turns the view by m_yaw (0.022) degrees times the scale computed here:
//   (m_mouseSensitivity + m_mouseAcceleration * speed) * ADS blend * tan(vertical FOV / 2) / tan(65-at-4:3 / 2)
// so sensitivity follows the field of view in hip fire too (B0016), changes with speed when acceleration is on,
// and can be smoothed over eight frames (m_mouseFilter) or halved (m_filter).

#include <math.h>
#include <string.h>

#include "universal/dvar.h"
#include "client/client.h"

#define T7_SOURCE "client/cl_input.cpp"
#include <t7_static.h>

T7_STATIC float s_lastMouseX T7_AT("", "s_lastMouseX");
T7_STATIC float s_lastMouseY T7_AT("", "s_lastMouseY");
T7_STATIC float s_mouseHistoryX[][MAX_MOUSE_HISTORY] T7_AT("", "s_mouseHistoryX");
T7_STATIC float s_mouseHistoryY[][MAX_MOUSE_HISTORY] T7_AT("", "s_mouseHistoryY");

// 1413ACBD0  client/cl_input.cpp
// The mouse movement of this frame, in counts. With consume false it only repeats the last result. m_filter halves
// it (the original's averaging with the other buffer survives only as the halving); m_mouseFilter > 0 replaces it
// by a weighted average of the last eight frames, weights (m_mouseFilter / 20)^i.
void CL_GetMouseMovement(int localClientNum, float *mx, float *my, bool consume)
{
	if (!consume)
	{
		*mx = s_lastMouseX;
		*my = s_lastMouseY;
		return;
	}
	bool halve = Dvar_GetBool(m_filter);
	float y = (float)cl_mouseDy[cl_mouseIndex];
	float x = (float)cl_mouseDx[cl_mouseIndex];
	if (halve)
	{
		y = y * 0.5f;
		x = x * 0.5f;
	}
	*mx = x;
	*my = y;
	float filter = Dvar_GetFloat(m_mouseFilter);
	if (filter > 0.0f)
	{
		memmove(&s_mouseHistoryX[localClientNum][1], &s_mouseHistoryX[localClientNum][0],
		        (MAX_MOUSE_HISTORY - 1) * sizeof(float));
		memmove(&s_mouseHistoryY[localClientNum][1], &s_mouseHistoryY[localClientNum][0],
		        (MAX_MOUSE_HISTORY - 1) * sizeof(float));
		float decay = filter / 20.0f;
		s_mouseHistoryX[localClientNum][0] = *mx;
		s_mouseHistoryY[localClientNum][0] = *my;
		float weight = 1.0f;
		float total = 0.0f;
		float sumX = 0.0f;
		float sumY = 0.0f;
		for (unsigned int i = 0; i != MAX_MOUSE_HISTORY; i++)
		{
			total += weight;
			sumX += weight * s_mouseHistoryX[localClientNum][i];
			sumY += weight * s_mouseHistoryY[localClientNum][i];
			weight *= decay;
		}
		*mx = sumX / total;
		*my = sumY / total;
	}
	cl_mouseIndex ^= 1;
	s_lastMouseX = *mx;
	s_lastMouseY = *my;
	cl_mouseDx[cl_mouseIndex] = 0;
	cl_mouseDy[cl_mouseIndex] = 0;
}

// 1413ACDF0  client/cl_input.cpp
// The last movement (s_lastMouse*) scaled for CL_MouseMove: sensitivity plus acceleration by speed (counts per
// millisecond), times the weapon's ADS sensitivity blended in by the ADS fraction, times the current vertical
// FOV's tangent over that of the default 65 (0.47780272 = tan(32.5 deg) * 3/4). With no cgame the tangent is read
// from address 0x131D6C (a null cg_t): the original has the same read.
void sub_1413ACDF0(int localClientNum, float *mx, float *my)
{
	float x = s_lastMouseX;
	float y = s_lastMouseY;
	float speed = sqrtf(x * x + y * y);
	speed = speed / (float)cls_frametime;
	float accel = Dvar_GetFloat(m_mouseAcceleration);
	float sens = Dvar_GetFloat(m_mouseSensitivity);
	sens = sens + accel * speed;
	const char *ps = (const char *)CG_GetPredictedPlayerState(localClientNum);
	float adsFraction = *(const float *)(ps + 0x2FC);
	float adsSens = sub_1427D0FC0(*(const unsigned long long *)(ps + 0x2C0));
	sens = sens * (adsSens * adsFraction + (1.0f - adsFraction));
	unsigned long long cgArray = sub_141406ED0();
	unsigned long long cg = cgArray && localClientNum < cg_localClientCount
	                            ? cgArray + (unsigned long long)(long long)localClientNum * CG_SIZE
	                            : 0;
	sens = sens * (*(const float *)(cg + 0x131D6C) / 0.47780272f);
	*my = sens * y;
	*mx = sens * x;
}

// 141405E50  client/cl_input.cpp
// Registers the client's input and connection dvars, after 141410080's. All take flags 0 or session-only flags:
// none is archived; the PC options file (config.ini) saves the ones the settings menu shows (MouseSensitivity ->
// m_mouseSensitivity, MouseVerticalSensitivity -> m_pitch, ...).
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
	m_mouseSensitivity = Dvar_RegisterFloat(0x247B172F, "", 2.0f, 0.1f, 30.0f, 0x0, "", false);
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
static inline float CL_CapTurn(float delta, float limit, bool limited, float frameSeconds)
{
	if (limited ? !(limit > 0.0f) || !(360.0f - limit >= 0.0f) : false)
		limit = 360.0f;
	else if (!(limit > 0.0f))
		return delta;
	float cap = limit * frameSeconds;
	float upper = delta - cap >= 0.0f ? cap : delta;
	float lower = -cap;
	return lower - upper >= 0.0f ? lower : upper;
}

// 1413AE730  client/cl_input.cpp
// The mouse into this command: yaw by m_yaw, pitch by m_pitch (or forward/back with m_forward when mouse look is
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
		if ((CL_FIELD(unsigned int, cl, 0xD0) & 0x200) && cl_demoPlaying != 2)
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
				float delta = CL_CapTurn(yawSpeed * mx, CL_FIELD(float, cl, 0xB7D4), limited, frameSeconds);
				CL_FIELD(float, cl, 0xB8CC) = CL_FIELD(float, cl, 0xB8CC) - delta;
				float amount = 127.0f - mx >= 0.0f ? mx : 127.0f;
				yawAmount = -(int)amount;
			}
			if ((kb_mlookActive[kb] || Dvar_GetBool(cl_freelook)) && !kb_strafeActive[kb])
			{
				float pitchSpeed = Dvar_GetFloat(m_pitch);
				float delta = CL_CapTurn(pitchSpeed * my, CL_FIELD(float, cl, 0xB7D0), limited, frameSeconds);
				CL_FIELD(float, cl, 0xB8C8) = delta + CL_FIELD(float, cl, 0xB8C8);
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
					variant = sub_142396BB0(direction, (int)(com_sessionModeBits << 28) >> 28);
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
