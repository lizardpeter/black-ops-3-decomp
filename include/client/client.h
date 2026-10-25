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

void CL_GetMouseMovement(int localClientNum, float *mx, float *my, bool consume);
void sub_1413ACDF0(int localClientNum, float *mx, float *my);
void sub_141405E50();
void sub_141410080();
