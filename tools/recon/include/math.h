// VC11 (VS2012) x64 CRT math, as the original binary links it.
//
// Build environment, not game source. Declarations only: in the hybrid build each one resolves to the
// original binary's CRT routine (by its MAP name, e.g. floorf at the address in analysis/<build>/map), so the
// reconstruction runs the very same math library as the original. Add functions here as reconstructed code
// needs them.
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

float floorf(float);
double floor(double);
float sqrtf(float);
double sqrt(double);
float sinf(float);
float cosf(float);
float acosf(float);
float atanf(float);
float atan2f(float, float);
double tan(double);

// fabs is a compiler intrinsic in VC11 x64 (andpd with a sign mask on the double), never a CRT call.
static inline double fabs(double x) { return __builtin_fabs(x); }

#ifdef __cplusplus
}

// VC11's <math.h> C++ float overload goes through double: inline float fabs(float _X) { return (float)fabs((double)_X); }
inline float fabs(float x)
{
	return (float)__builtin_fabs((double)x);
}
#endif
