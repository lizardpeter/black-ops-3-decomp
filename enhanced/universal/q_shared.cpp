// Enhanced P0024 / B0001: bounded concatenation of engine strings.
// The faithful src/universal/q_shared.cpp intentionally retains the original
// size_t subtraction underflow. This override only affects reconstructed calls.
// IMPORTANT: the canonical BO3 Store executable is currently byte-identical and
// does not redirect its native I_strcat callsites to this DLL. Do not claim that
// the native original was patched by compiling this replacement.
#include "universal/q_shared.h"

void I_strcat(char *dest, size_t destsize, const char *src)
{
    if (!dest || !destsize) return;

    // Never scan beyond the destination's declared capacity. The original
    // called strlen(dest) unbounded and subtracted it from destsize.
    size_t used = 0;
    while (used < destsize && dest[used]) ++used;
    if (used == destsize)
    {
        // Fail closed: leave an in-bounds terminator for subsequent consumers.
        dest[destsize - 1] = 0;
        return;
    }
    if (!src) return;

    const size_t available = destsize - used - 1;
    size_t written = 0;
    while (written < available && src[written])
    {
        dest[used + written] = src[written];
        ++written;
    }
    dest[used + written] = 0;
}

// P0025 / B0002: the faithful matcher recurses once for each candidate
// position following '*'. An adversarial pattern with many '*' can trigger
// exponential work or exhaust the stack. This bounded, iterative matcher
// preserves wildcard-match results for ordinary, valid NUL-terminated inputs.
// Callers must treat zero as match and nonzero as mismatch (not use sorting
// order: the original returned a signed character difference on mismatch).
namespace
{
constexpr size_t WildcardMaximumLength = 4096;
constexpr size_t WildcardMaximumSteps = 262144;
constexpr size_t NoWildcard = (size_t)-1;
unsigned int LowerAscii(unsigned char c)
{
    return c >= 'A' && c <= 'Z' ? c + ('a' - 'A') : c;
}
bool BoundedLength(const char *s, size_t &length)
{
    if (!s) return false;
    for (length = 0; length < WildcardMaximumLength; ++length)
        if (!s[length]) return true;
    return false; // fail closed for unbounded patterns/strings
}
}

int I_stricmpwild(const char *pattern, const char *str)
{
    size_t plen, slen;
    if (!BoundedLength(pattern, plen) || !BoundedLength(str, slen))
        return 1;

    size_t p = 0, s = 0, lastStar = NoWildcard, retry = 0;
    size_t work = 0;
    while (s < slen)
    {
        if (++work > WildcardMaximumSteps) return 1;
        if (p < plen && (pattern[p] == '?' ||
                         LowerAscii((unsigned char)pattern[p]) ==
                         LowerAscii((unsigned char)str[s])))
        {
            ++p; ++s;
        }
        else if (p < plen && pattern[p] == '*')
        {
            lastStar = p++;
            retry = s;
        }
        else if (lastStar != NoWildcard)
        {
            p = lastStar + 1;
            s = ++retry;
        }
        else
        {
            return 1;
        }
    }
    while (p < plen && pattern[p] == '*') ++p;
    return p == plen ? 0 : 1;
}
