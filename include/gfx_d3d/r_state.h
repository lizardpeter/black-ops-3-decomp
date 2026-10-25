// gfx_d3d/r_state.h (reconstructed: only what reconstructed code uses so far)
#pragma once

// The render thread's source state (IW's GfxCmdBufSourceState, here one struct with the command-buffer state): the
// layout is known by offset only, so it is passed as bytes.
//
// +0x0000  code matrices, 0x40 bytes each, indexed by code constant - 0xD5: groups of four from a base (0 view,
//          4 projection, 8 view-projection, 12 the one from +0x2080), each base followed by its inverse, transpose
//          and inverse-transpose
// +0x1DF0  the view parms copied from the viewInfo by R_Set3D (0x290 bytes: view +0x000, projection +0x040,
//          view-projection +0x0C0, origin +0x240, axis +0x250)
// +0x2080  the matrix behind code matrix 12
// +0x20C0  per code constant, the version its value was made at (u16)
// +0x228A  per matrix group, the current version (u16): view, projection, view-projection, group 12
// +0x22A0  the eye offset (vec4) camera-relative drawing subtracts
// +0x22B0  the viewInfo being drawn
// +0x22B8  the view-model mode: 1 while the gun's draw lists are drawn (depth range [0.984375, 1])
// +0x8100  the camera-relative mode: 0 world, 1 eye-relative (no view translation)
enum
{
	CODE_MATRIX_FIRST = 0xD5,
	SOURCE_VIEW_PARMS = 0x1DF0,
	SOURCE_MATRIX12_SOURCE = 0x2080,
	SOURCE_STAMPS = 0x20C0,
	SOURCE_VERSIONS = 0x228A,
	SOURCE_EYE_OFFSET = 0x22A0,
	SOURCE_VIEW_INFO = 0x22B0,
	SOURCE_VIEW_MODEL_MODE = 0x22B8,
	SOURCE_CAMERA_MODE = 0x8100,
};

void MatrixMultiply44(const float *in1, const float *in2, float *out);
void MatrixInverse44(const float *in, float *out);
void MatrixForViewer(const float *origin, const float (*axis)[3], float *out);

void sub_141DECF80(char *source);
void R_DeriveCodeMatrix(char *source, unsigned int sourceIndex, unsigned int baseIndex);
const float *R_GetCodeMatrix(char *source, unsigned int sourceIndex, unsigned int firstRow);
