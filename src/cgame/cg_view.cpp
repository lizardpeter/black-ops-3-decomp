// The view's field of view. Original function name unknown (IW's CG_CalcFov plays this part); source path assumed
// from the engine lineage. docs/fov.md has how BO3 turns the FOV setting into a lens and back.

#include <t7_exe_call.h>

#include "cgame/cg_view.h"

// 1405B6690  cgame/cg_view.cpp
// Computes the view's field of view for localClientNum (fov < 0: from the current lens, the normal case; fov >= 0:
// that horizontal-at-4:3 FOV, for scripted cameras) and stores tanHalfFovX, tanHalfFovY (twice) and the FOV in its
// cg_t. The original decodes the cg array pointer inline; the decoding is the same function of the encoded value
// and the PEB as the standalone copy called here, through the exe so that it returns (t7_exe_call.h).
void sub_1405B6690(int localClientNum, float fov)
{
	char *cgArray = T7ExeCall(sub_141406ED0);
	char *cg = cgArray && localClientNum < cg_localClientCount ? cgArray + (long long)localClientNum * CG_SIZE : 0;
	float tanHalfFov, tanHalfFovX, tanHalfFovY;
	T7ExeCall(CG_CalcFOVfromLens, localClientNum, &fov, &tanHalfFov, &tanHalfFovX, &tanHalfFovY);
	*(float *)(cg + CG_TAN_HALF_FOV_X) = tanHalfFovX;
	*(float *)(cg + CG_TAN_HALF_FOV_Y) = tanHalfFovY;
	*(float *)(cg + CG_TAN_HALF_FOV_Y_2) = tanHalfFovY;
	*(float *)(cg + CG_FOV) = fov;
}
