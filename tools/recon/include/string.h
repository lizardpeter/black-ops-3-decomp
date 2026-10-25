// VC11 (VS2012) x64 CRT <string.h>, as the original binary uses it.
//
// Build environment, not game source. VC11 expands strcpy as an intrinsic (the original binary links no
// out-of-line strcpy: a literal source becomes a few moves), so strcpy is defined inline here. The rest resolve to
// the original's CRT routines by MAP name in the hybrid build.
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

typedef unsigned long long size_t;

void *memcpy(void *dst, const void *src, size_t n);
void *memmove(void *dst, const void *src, size_t n);
void *memset(void *dst, int value, size_t n);
int memcmp(const void *a, const void *b, size_t n);
size_t strlen(const char *s);
char *strrchr(const char *s, int c);
char *strncpy(char *dst, const char *src, size_t n);
char *_strdup(const char *s);

static inline char *t7_strcpy_intrinsic(char *dst, const char *src)
{
	char *out = dst;
	while ((*dst++ = *src++) != 0)
		;
	return out;
}
#define strcpy t7_strcpy_intrinsic

#ifdef __cplusplus
}
#endif
