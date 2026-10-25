// P0016: the gameplay view shows exactly the field of view the player set (B0020).
//
// BO3's FOV setting (cg_fov_default, config.ini "FOV") is already the horizontal FOV at 16:9, MW2019's unit: it is
// turned into a lens of focal length f = 7 / (tan(FOV/2) * 9/16) mm. But CG_CalcFOVfromLens (1405AFA30) then focuses
// that lens at 500 mm whenever depth of field is off (cg+0x131D28 & 0x30000 == 0, all of normal play), and a lens
// focused that close sees a narrower picture: tan(vertical/2) = 7/f - 7/500. At FOV 80 the screen shows 78.31 at
// 16:9; at 120, 119.28 (docs/fov.md has the table). The enhanced build adds the 7/500 back in proportion to how far
// the weapon is from aimed down sights, so hip fire shows the set FOV exactly (focus at infinity) and a fully aimed
// weapon keeps the original's zoom; every other case (depth of field on, the cg_drawMinimap lens, a fixed FOV from a
// scripted camera) is the original. The horizontal FOV follows (tanX keeps its ratio to tanY, the aspect), and the
// stored FOV in degrees moves by the same amount as the vertical FOV it is derived from.

#include <math.h>
#include <t7_exe_call.h>

#include "cgame/cg_view.h"
#include "universal/dvar.h"

static const float LENS_SENSOR_HALF_HEIGHT = 7.0f;   // mm: tan(vertical/2) = 7 / f at infinity focus
static const float LENS_NEAR_FOCUS = 500.0f;         // mm: the focus CG_CalcFOVfromLens uses without depth of field

void sub_1405B6690(int localClientNum, float fov)
{
	char *cgArray = T7ExeCall(sub_141406ED0);
	char *cg = cgArray && localClientNum < dword_1440A99A4 ? cgArray + (long long)localClientNum * CG_SIZE : 0;
	float requested = fov;
	float tanHalfFov, tanHalfFovX, tanHalfFovY;
	T7ExeCall(CG_CalcFOVfromLens, localClientNum, &fov, &tanHalfFov, &tanHalfFovX, &tanHalfFovY);
	if (requested < 0.0f && cg && !(*(unsigned int *)(cg + CG_LENS_FLAGS) & 0x30000) && tanHalfFovY > 0.0f &&
	    !T7ExeCall(Dvar_GetBool, cg_drawMinimap))
	{
		float ads = *(float *)(cg + CG_PS_WEAPON_POS_FRAC);
		ads = ads < 0.0f ? 0.0f : ads > 1.0f ? 1.0f : ads;
		float exact = tanHalfFovY + (1.0f - ads) * (LENS_SENSOR_HALF_HEIGHT / LENS_NEAR_FOCUS);
		tanHalfFovX *= exact / tanHalfFovY;
		fov += (atanf(exact / 0.75f) - atanf(tanHalfFovY / 0.75f)) * (2.0f * 57.295776f);
		tanHalfFovY = exact;
	}
	*(float *)(cg + CG_TAN_HALF_FOV_X) = tanHalfFovX;
	*(float *)(cg + CG_TAN_HALF_FOV_Y) = tanHalfFovY;
	*(float *)(cg + CG_TAN_HALF_FOV_Y_2) = tanHalfFovY;
	*(float *)(cg + CG_FOV) = fov;
}
