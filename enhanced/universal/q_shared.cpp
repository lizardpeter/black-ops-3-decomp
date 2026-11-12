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
