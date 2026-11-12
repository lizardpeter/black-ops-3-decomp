// Portable adversarial regression for BO3 enhanced B0001.
// Tests the same file that --enhanced compiles; *not* the untouched Store EXE.
#include <array>
#include <cassert>
#include <cstddef>
#include <cstring>
#include <algorithm>
#include <random>
#include <string>
#include <vector>
#include <utility>

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


static char asciiLower(char c)
{
    return c >= 'A' && c <= 'Z' ? (char)(c + 32) : c;
}

// Independent dynamic-programming oracle for normal wildcard semantics.
// Compare match/non-match only; the faithful implementation's ordering of
// non-matches is not a reliable contract.
static bool referenceWildcard(const std::string &pattern, const std::string &text)
{
    std::vector<unsigned char> prev(text.size() + 1), next(text.size() + 1);
    prev[0] = 1;
    for (char c : pattern)
    {
        std::fill(next.begin(), next.end(), 0);
        if (c == '*')
        {
            next[0] = prev[0];
            for (size_t j = 1; j <= text.size(); ++j)
                next[j] = prev[j] || next[j - 1];
        }
        else
        {
            for (size_t j = 1; j <= text.size(); ++j)
                next[j] = prev[j - 1] && (c == '?' || asciiLower(c) == asciiLower(text[j - 1]));
        }
        prev.swap(next);
    }
    return prev[text.size()] != 0;
}

static void checkWildcard()
{
    for (const auto &item : {std::pair<const char *, const char *>{"a*", "Abc"},
                             {"*", ""}, {"?a", "ba"}, {"a?", "a"},
                             {"*a*b", "axxxb"}, {"*z", "aaaaaaaa"},
                             {"", ""}, {"**", ""}})
        assert((I_stricmpwild(item.first, item.second) == 0) ==
               referenceWildcard(item.first, item.second));

    std::minstd_rand random(371);
    const char patterns[] = "aAbB*?";
    const char letters[] = "aAbB";
    for (int n = 0; n < 6000; ++n)
    {
        std::string p, s;
        for (unsigned k = random() % 20; k; --k) p += patterns[random() % 6];
        for (unsigned k = random() % 20; k; --k) s += letters[random() % 4];
        assert((I_stricmpwild(p.c_str(), s.c_str()) == 0) == referenceWildcard(p, s));
    }

    std::string pattern;
    for (int i = 0; i < 300; ++i) pattern += "*a";
    pattern += "z";
    assert(I_stricmpwild(pattern.c_str(), std::string(4095, 'a').c_str()) != 0);
    assert(I_stricmpwild(std::string(4096, 'a').c_str(), "small") != 0);
    assert(I_stricmpwild("*", nullptr) != 0);
}

int main()
{
    checkWildcard();
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
