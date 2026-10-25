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
