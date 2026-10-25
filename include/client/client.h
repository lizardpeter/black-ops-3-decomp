// client/client.h (reconstructed: only what reconstructed code uses so far)
#pragma once

#include "universal/dvar.h"

struct dvar_t;
struct playerState_s;

enum { MAX_MOUSE_HISTORY = 8 };

// Mouse movement in device counts, double-buffered: the input side (CL_MouseEvent, 1413AC9E0) stores this frame's
// counts at cl_mouseIndex; CL_GetMouseMovement reads them, flips the index and clears the other slot. Globals here
// (members of clientActive_t in Ghosts).
extern int cl_mouseDx[2];
extern int cl_mouseDy[2];
extern int cl_mouseIndex;
extern int cls_frametime;  // milliseconds this client frame

extern const dvar_t *m_pitch;
extern const dvar_t *m_yaw;
extern const dvar_t *m_forward;
extern const dvar_t *m_side;
extern const dvar_t *m_filter;
extern const dvar_t *m_mouseFilter;
extern const dvar_t *m_mouseAcceleration;
extern const dvar_t *m_mouseSensitivity;
extern const dvar_t *cl_freelook;
extern const dvar_t *cl_ingame;
extern const dvar_t *cl_userTestBuild;
extern const dvar_t *player_name;
extern const dvar_t *cl_voice;
extern const dvar_t *maxVoicePacketsPerFrame;
extern const dvar_t *cl_timeout;
extern const dvar_t *cl_connectTimeout;
extern const dvar_t *cl_connectionAttempts;
extern const dvar_t *splitscreen;
extern const dvar_t *splitscreen_playerCount;
extern const dvar_t *splitscreen_horizontal;
extern const dvar_t *cl_disableHeroRenders;

// The cgame's per-local-client globals (cg_t, 0x342720 bytes each) are reached through an encrypted pointer
// (docs/obfuscation.md). The exe inlines the decode at every use; it also has out-of-line copies, all the same
// algorithm, and reconstructed code calls one of them.
extern unsigned long long cg_arrayEncoded;
extern int cg_localClientCount;
unsigned long long sub_141406ED0();  // decodes cg_arrayEncoded
enum { CG_SIZE = 0x342720 };

const playerState_s *CG_GetPredictedPlayerState(int localClientNum);
float sub_1427D0FC0(unsigned long long weapon);  // the weapon's ADS sensitivity multiplier (attachments override)

// Aim assist's input and output for one command (layout from CL_MouseMove's use; Ghosts' AimInput/AimOutput have the
// same roles). Padding is left as the original leaves it: unwritten.
struct AimInput
{
	float deltaTime;        // cls_frametime in seconds
	float deltaTimeScaled;  // 149BB4714 (ms) in seconds
	float pitch;
	float pitchAxis;        // mouse Y in the mouse-direction path
	float pitchMax;
	float yaw;
	float yawAxis;          // mouse X in the mouse-direction path
	float yawMax;
	float forwardAxis;
	float rightAxis;
	unsigned short mouseInput;  // always 1 here
	unsigned short pad2A;
	unsigned int buttons[3];
	int localClientNum;
	unsigned int pad3C;
	const playerState_s *ps;
	float adsFraction;
	unsigned short ps99C;
	unsigned short ps994;
};
static_assert(sizeof(AimInput) == 0x50, "AimInput");

struct AimOutput
{
	float pitch;
	float yaw;
	unsigned short ps99C;
	unsigned short ps994;
};

struct usercmd_s;
struct kbutton_t;
enum { KB_STRIDE = 0x498 };
extern unsigned char kb_strafeActive[];  // kbutton_t active flags per local client (stride KB_STRIDE)
extern unsigned char kb_mlookActive[];
extern int cls_aimFrametime;             // 149BB4714
extern int unk_1494B2DC8;               // meaning unknown; CL_MouseMove skips its movement lock when it is 2
extern int cl_localClientActive[];       // 148DEE268, stride 9 ints
extern const dvar_t *aim_mouseDirection; // 14E418348: a vec2 dvar CL_MouseMove writes the mouse direction to

char *CL_GetLocalClientGlobals(int localClientNum);
bool sub_142756F90(const playerState_s *ps);
bool sub_1408A5010(int localClientNum);
void AimAssist_UpdateMouseInput(const AimInput *input, AimOutput *output);
void sub_140104EA0(unsigned long long direction, const AimInput *input, AimOutput *output);
void Dvar_SetVec2(const dvar_t *dvar, float x, float y);
const dvar_t *sub_142396BB0(const dvar_t *dvar, int sessionMode);
extern unsigned int com_sessionModeState;  // 158AE65C4; the low 4 bits, sign-extended, are the session mode

void CL_MouseMove(int localClientNum, usercmd_s *cmd);
void CL_GetMouseMovement(int localClientNum, float *mx, float *my, bool consume);
void sub_1413ACDF0(int localClientNum, float *mx, float *my);
void sub_141405E50();
void sub_141410080();
