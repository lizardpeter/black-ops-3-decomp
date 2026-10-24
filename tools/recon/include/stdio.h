// CRT stdio, as the Store build links it.
//
// Build environment, not game source. Declarations only: each resolves to the original binary's copy by name
// (records/names.tsv). The Store build (VS2019 UCRT) has sprintf expanded from the UCRT's inline definition into a
// small function over __stdio_common_vsprintf (140096E70), which is what the hybrid link reaches.
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

int sprintf(char *buffer, const char *format, ...);

#ifdef __cplusplus
}
#endif
