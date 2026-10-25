// P0021: the late latch's gun. The gun is placed in the world from the view as the frame made it, so while the
// render thread draws a latched view's gun lists (the view-model mode, +0x22B8 == 1) the code matrices come from
// that view's parms, kept by RB_LateLatch, instead of the turned ones R_Set3D copied: the gun stays where the game
// put it on screen while the world turns. The view matrix's version doesn't change when the view-model mode does
// (only the projection's and view-projection's are bumped), so for those lists it is told apart by its top bit.
// Otherwise the original (src/gfx_d3d/r_state.cpp). docs/late-latch.md.

#include "gfx_d3d/r_state.h"
#include "r_late_latch.h"

#define SOURCE_MATRIX(source, u) ((float *)((source) + (unsigned long long)(u) * 0x40))
#define SOURCE_STAMP(source, index) (*(unsigned short *)((source) + SOURCE_STAMPS + (unsigned long long)(index) * 2))
#define SOURCE_VERSION(source, group) \
	(*(unsigned short *)((source) + SOURCE_VERSIONS + (unsigned long long)(group) * 2))
#define SOURCE_INT(source, offset) (*(const int *)((source) + (offset)))

// The view's version for these lists: the group's, with the top bit flipped for a latched view's gun.
static unsigned short ViewVersion(const char *source, unsigned int group, const char *gun)
{
	unsigned short version = SOURCE_VERSION(source, group);
	return group == 0 && gun ? (unsigned short)(version ^ 0x8000) : version;
}

// The original adds a vec4 of -0.0 (14C752EE0, set once by 140080310) after each first product: x + -0.0 is x for
// every x, so the literal stands in for the global.
static const float NEGATIVE_ZERO = -0.0f;

static void CopyMatrix44(const float *in, float *out)
{
	for (int i = 0; i < 16; i++)
		out[i] = in[i];
}

static void TransposeMatrix44(const float *in, float *out)
{
	for (int row = 0; row < 4; row++)
		for (int column = 0; column < 4; column++)
			out[row * 4 + column] = in[column * 4 + row];
}

// The translation row moved by the eye offset e: row3 = ((e.x * row0 + -0) + e.z * row2) + ((e.y * row1 + -0) +
// e.w * row3), lane by lane, in the order the view matrix's derivation adds them.
static void TranslateByEyeXFirst(float *m, const float *e)
{
	for (int i = 0; i < 4; i++)
	{
		float xz = (e[0] * m[i] + NEGATIVE_ZERO) + e[2] * m[8 + i];
		float yw = (e[1] * m[4 + i] + NEGATIVE_ZERO) + e[3] * m[12 + i];
		m[12 + i] = xz + yw;
	}
}

// The same with the other order of the view-projection and the group-12 matrix:
// row3 = ((e.y * row1 + -0) + e.w * row3) + ((e.x * row0 + -0) + e.z * row2).
static void TranslateByEyeYFirst(float *m, const float *e)
{
	for (int i = 0; i < 4; i++)
	{
		float xz = (e[0] * m[i] + NEGATIVE_ZERO) + e[2] * m[8 + i];
		float yw = (e[1] * m[4 + i] + NEGATIVE_ZERO) + e[3] * m[12 + i];
		m[12 + i] = yw + xz;
	}
}

// 141DED140  gfx_d3d/r_state.cpp
// Makes the base matrix of a group from the source's view parms: the view (0), the projection (4, by sub_141DECF80),
// the view-projection (8) or the matrix at +0x2080 (12), and stamps it with its group's version. The second
// parameter (the constant asked for) is not used.
void R_DeriveCodeMatrix(char *source, unsigned int sourceIndex, unsigned int baseIndex)
{
	const char *gun = RB_LateLatchGunParms(source);
	const char *parms = gun ? gun : source + SOURCE_VIEW_PARMS;
	const float *eye = (const float *)(source + SOURCE_EYE_OFFSET);
	if (baseIndex == 0)
	{
		float *view = SOURCE_MATRIX(source, 0);
		CopyMatrix44((const float *)parms, view);
		int mode = SOURCE_INT(source, SOURCE_CAMERA_MODE);
		if (mode == 0)
		{
			TranslateByEyeXFirst(view, eye);
		}
		else if (mode == 1)
		{
			view[12] = 0.0f;
			view[13] = 0.0f;
			view[14] = 0.0f;
		}
		SOURCE_STAMP(source, CODE_MATRIX_FIRST + 0) = ViewVersion(source, 0, gun);
		return;
	}
	if (baseIndex == 4)
	{
		sub_141DECF80(source);
		return;
	}
	if (baseIndex == 8)
	{
		float *viewProjection = SOURCE_MATRIX(source, 8);
		if (SOURCE_INT(source, SOURCE_VIEW_MODEL_MODE) == 0x40000000)
		{
			if (SOURCE_STAMP(source, CODE_MATRIX_FIRST + 4) != SOURCE_VERSION(source, 1))
				sub_141DECF80(source);
			MatrixMultiply44((const float *)parms, SOURCE_MATRIX(source, 4), viewProjection);
		}
		else
		{
			int mode = SOURCE_INT(source, SOURCE_CAMERA_MODE);
			if (mode == 0)
			{
				CopyMatrix44((const float *)(parms + 0xC0), viewProjection);
				TranslateByEyeYFirst(viewProjection, eye);
			}
			else if (mode == 1)
			{
				float view[16];
				CopyMatrix44((const float *)parms, view);
				view[12] = 0.0f;
				view[13] = 0.0f;
				view[14] = 0.0f;
				MatrixMultiply44(view, (const float *)(parms + 0x40), viewProjection);
			}
			else
			{
				CopyMatrix44((const float *)(parms + 0xC0), viewProjection);
			}
		}
		SOURCE_STAMP(source, CODE_MATRIX_FIRST + 8) = SOURCE_VERSION(source, 2);
		return;
	}
	if (baseIndex == 12)
	{
		float *m = SOURCE_MATRIX(source, 12);
		CopyMatrix44((const float *)(source + SOURCE_MATRIX12_SOURCE), m);
		TranslateByEyeYFirst(m, eye);
		SOURCE_STAMP(source, CODE_MATRIX_FIRST + 12) = SOURCE_VERSION(source, 3);
	}
}

// 141DED4D0  gfx_d3d/r_state.cpp
// The code matrix for a code constant (0xD5 and up), from row firstRow: made again if its version is behind its
// group's. The base comes from R_DeriveCodeMatrix; of the others, the transpose of a matrix whose transpose partner is
// current is a copy, otherwise the inverse of the transpose partner (made first if needed).
const float *R_GetCodeMatrix(char *source, unsigned int sourceIndex, unsigned int firstRow)
{
	unsigned int u = sourceIndex - CODE_MATRIX_FIRST;
	unsigned short version = ViewVersion(source, u >> 2, RB_LateLatchGunParms(source));
	if (SOURCE_STAMP(source, sourceIndex) != version)
	{
		unsigned int base = u & ~3u;
		if (SOURCE_STAMP(source, base + CODE_MATRIX_FIRST) != version)
		{
			R_DeriveCodeMatrix(source, sourceIndex, base);
			if (u == base)
				return (const float *)(source + ((unsigned long long)firstRow + (unsigned long long)u * 4) * 0x10);
		}
		float *out = SOURCE_MATRIX(source, u);
		SOURCE_STAMP(source, sourceIndex) = version;
		unsigned int transposed = u ^ 2;
		if (SOURCE_STAMP(source, transposed + CODE_MATRIX_FIRST) == version)
		{
			TransposeMatrix44(SOURCE_MATRIX(source, transposed), out);
		}
		else
		{
			unsigned int partner = u ^ 1;
			float *partnerMatrix = SOURCE_MATRIX(source, partner);
			if (SOURCE_STAMP(source, partner + CODE_MATRIX_FIRST) != version)
			{
				TransposeMatrix44(SOURCE_MATRIX(source, base), partnerMatrix);
				SOURCE_STAMP(source, partner + CODE_MATRIX_FIRST) = version;
			}
			MatrixInverse44(partnerMatrix, out);
		}
	}
	return (const float *)(source + ((unsigned long long)firstRow + (unsigned long long)u * 4) * 0x10);
}
