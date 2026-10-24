// universal/q_shared.h (reconstructed: the declarations src/universal/q_shared.cpp defines)
#pragma once

#include <string.h>

void I_strcpy(char *dest, size_t destsize, const char *src);
int I_strnicmp(const char *s0, const char *s1, size_t n);
int I_strncmp(const char *s0, const char *s1, size_t n);
const char *I_stristr(const char *s0, const char *substr);
int I_stricmp(const char *s0, const char *s1);
int I_stricmpwild(const char *wild, const char *s);
void I_strcat(char *dest, size_t destsize, const char *src);
char *I_CleanStr(char *string);
