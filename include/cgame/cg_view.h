// cgame/cg_view.h (reconstructed: only what reconstructed code uses so far)
#pragma once

// cg_t is reached through an encoded pointer (149B25A20): one cg_t per local client, 0x342720 bytes apart.
enum
{
	CG_SIZE = 0x342720,
	CG_PREDICTED_PLAYER_STATE = 0x11A8B0,       // playerState_t, as 140961D00 returns it
	CG_PS_WEAPON_POS_FRAC = 0x11A8B0 + 0x2FC,   // fWeaponPosFrac: 0 hip fire, 1 fully aimed down sights
	CG_LENS_FLAGS = 0x131D28,                   // low byte: lens preset; 0x30000: depth-of-field mode (docs/fov.md)
	CG_TAN_HALF_FOV_X = 0x131D68,
	CG_TAN_HALF_FOV_Y = 0x131D6C,
	CG_TAN_HALF_FOV_Y_2 = 0x131D70,             // a second copy of tanHalfFovY
	CG_FOV = 0x131D74,                          // degrees, horizontal at 4:3 (Hor+)
};

struct dvar_t;
extern const dvar_t *cg_drawMinimap;  // when set, CG_CalcFOVfromLens keeps the lens's own focus (docs/fov.md)
extern int cg_localClientCount;  // number of cg_t slots: a local client at or past it has none

// Standalone decoder of the cg array pointer (149B25A20); the game inlines the same decoding everywhere else.
char *sub_141406ED0();
void CG_CalcFOVfromLens(int localClientNum, float *fov, float *tanHalfFov, float *tanHalfFovX, float *tanHalfFovY);
void sub_1405B6690(int localClientNum, float fov);
