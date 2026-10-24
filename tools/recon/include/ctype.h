// VC11 (VS2012) x64 CRT <ctype.h>, as the original binary links it.
//
// Build environment, not game source. Declarations only: in the hybrid build each one resolves to the
// original binary's CRT routine by its MAP name (toupper, tolower), so the locale tables are the original's.
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

int toupper(int);
int tolower(int);
int isalpha(int);

#ifdef __cplusplus
}
#endif
