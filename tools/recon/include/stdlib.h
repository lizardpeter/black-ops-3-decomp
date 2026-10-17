// VC11 (VS2012) x64 CRT, as the original binary links it.
//
// Build environment, not game source. Declarations only: in the hybrid build each one resolves to the
// original binary's CRT routine by its MAP name (see math.h). Add functions here as reconstructed code needs them.
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

int rand(void);

#ifdef __cplusplus
}
#endif
