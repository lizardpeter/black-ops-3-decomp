// universal/q_shared.cpp (string utilities)
//
// Reconstructed from the Microsoft Store build (BlackOps3_MSStore). BO3 has no symbol build, so names come from
// behaviour plus lineage: Ghosts' PS4 server PDB has the same family in universal/q_shared.cpp (I_strncpyz,
// I_strnicmp, I_strncmp, I_stristr, I_stricmp, I_stricmpwild, I_strncat, I_CleanStr, in this order), and the
// BOIII client names I_strcpy, I_stricmp, I_strcat and I_CleanStr in the Steam build. records/names.tsv has the
// evidence for each. The source path is Ghosts'; BO3's own path is unconfirmed, and original line numbers are
// unknown. Functions appear in the Store build's address order, which follows Ghosts' line order.
//
// Differences from Ghosts: sizes are size_t, and the copy functions take (dest, destsize, src).

#include <ctype.h>

#include "universal/q_shared.h"

// 1423B46B0  universal/q_shared.cpp  (Ghosts: I_strncpyz)
void I_strcpy(char *dest, size_t destsize, const char *src)
{
	if (!destsize || !dest)
		return;
	if (!src)
	{
		*dest = 0;
		return;
	}
	char *out = dest;
	size_t left = destsize;
	while ((*out++ = *src++) != 0)
	{
		if (--left == 0)
		{
			dest[destsize - 1] = 0;
			return;
		}
	}
}

// 1423B4750  universal/q_shared.cpp
int I_strnicmp(const char *s0, const char *s1, size_t n)
{
	if (!s0 || !s1)
		return (int)(s1 - s0);
	unsigned int c0, c1;
	do
	{
		c0 = (unsigned char)*s0++;
		c1 = (unsigned char)*s1++;
		if (!n--)
			return 0;
		if (c0 != c1)
		{
			if (c0 - 'A' <= 'Z' - 'A')
				c0 += 'a' - 'A';
			if (c1 - 'A' <= 'Z' - 'A')
				c1 += 'a' - 'A';
			if (c0 != c1)
				return c0 < c1 ? -1 : 1;
		}
	} while (c0);
	return 0;
}

// 1423B47D0  universal/q_shared.cpp
int I_strncmp(const char *s0, const char *s1, size_t n)
{
	if (!s0 || !s1)
		return (int)(s1 - s0);
	char c0, c1;
	do
	{
		c0 = *s0++;
		c1 = *s1++;
		if (!n--)
			return 0;
		if (c0 != c1)
			return c0 < c1 ? -1 : 1;
	} while (c0);
	return 0;
}

// 1423B4830  universal/q_shared.cpp
const char *I_stristr(const char *s0, const char *substr)
{
	if (!s0 || !substr)
		return 0;
	for (int i = 0; s0[i]; i++)
	{
		for (int j = 0;; j++)
		{
			if (!substr[j])
				return s0 + i;
			if (tolower(s0[i + j]) != tolower(substr[j]))
				break;
		}
	}
	return 0;
}

// 1423B48E0  universal/q_shared.cpp  (I_strnicmp inlined in the Store build)
int I_stricmp(const char *s0, const char *s1)
{
	return I_strnicmp(s0, s1, 0x7FFFFFFF);
}

// 1423B4960  universal/q_shared.cpp
int I_stricmpwild(const char *wild, const char *s)
{
	char cWild, cString;
	int charDiff;
	for (;;)
	{
		cWild = *wild++;
		if (cWild == '*')
		{
			if (!*wild)
				return 0;
			if (*s && !I_stricmpwild(wild - 1, s + 1))
				return 0;
			continue;
		}
		cString = *s++;
		if (cWild != cString)
		{
			if (cWild == '?')
				continue;
			charDiff = tolower(cWild) - tolower(cString);
			if (charDiff)
				return charDiff < 0 ? -1 : 1;
		}
		if (!cWild)
			return 0;
	}
}

// 1423B4B30  universal/q_shared.cpp  (Ghosts: I_strncat; I_strcpy inlined in the Store build)
void I_strcat(char *dest, size_t destsize, const char *src)
{
	int len = 0;
	while (dest[len])
		len++;
	I_strcpy(dest + len, destsize - len, src);
}

// 1423B4BA0  universal/q_shared.cpp
char *I_CleanStr(char *string)
{
	bool hadColor;
	do
	{
		hadColor = false;
		char *s = string;
		char *d = string;
		char c;
		while ((c = *s) != 0)
		{
			if (c == '^' && (unsigned char)(s[1] - '0') < 10)
			{
				s++;
				hadColor = true;
			}
			else if ((unsigned char)(c - ' ') < 0x5F)
			{
				*d++ = c;
			}
			s++;
		}
		*d = 0;
	} while (hadColor);
	return string;
}
