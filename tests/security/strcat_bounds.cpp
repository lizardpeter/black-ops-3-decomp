// Portable adversarial regression for BO3 enhanced B0001.
// Tests the same file that --enhanced compiles; *not* the untouched Store EXE.
#include <array>
#include <cassert>
#include <cstddef>
#include <cstring>

#include "universal/q_shared.h"

static void check(unsigned used, unsigned cap, unsigned sourceLength)
{
    std::array<char, 128> data;
    data.fill('!');
    char *dst = data.data() + 8;
    for (unsigned i = 0; i < used; ++i) dst[i] = 'A';
    dst[used] = '\0';

    std::array<char, 96> source;
    source.fill('s');
    source[sourceLength] = '\0';
    auto expected = data;
    char *target = expected.data() + 8;

    if (cap)
    {
        if (used >= cap)
            target[cap - 1] = '\0';
        else
        {
            const unsigned count = sourceLength < cap - used - 1
                                       ? sourceLength : cap - used - 1;
            for (unsigned i = 0; i < count; ++i) target[used + i] = 's';
            target[used + count] = '\0';
        }
    }

    I_strcat(dst, cap, source.data());
    assert(data == expected); // includes the 8-byte prefix and all suffix guards
}

int main()
{
    for (unsigned cap = 0; cap < 65; ++cap)
        for (unsigned used = 0; used < 70; ++used)
            for (unsigned sourceLength : {0u, 1u, 5u, 32u, 80u})
                check(used, cap, sourceLength);

    std::array<char, 16> a;
    a.fill('!');
    a[0] = 'X'; a[1] = '\0';
    I_strcat(a.data(), 16, nullptr);
    assert(a[0] == 'X' && a[1] == '\0' && a[15] == '!');
    I_strcat(nullptr, 100, "no-op");
    I_strcat(a.data(), 0, "no-op");
    assert(a[0] == 'X' && a[1] == '\0');
}
