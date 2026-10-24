// x64 CRT <time.h>, as the original binary links it.
//
// Build environment, not game source. Declarations only: in the hybrid build each one resolves to the original's
// routine (the Store build imports the CRT, so through its import table). Add functions as reconstructed code needs them.
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

typedef long long __time64_t;

__time64_t _time64(__time64_t *t);

#ifdef __cplusplus
}
#endif
