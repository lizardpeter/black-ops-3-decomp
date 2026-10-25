// P0011: mouse aim in MW2019 units, the same at any field of view (B0016-B0019).
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
