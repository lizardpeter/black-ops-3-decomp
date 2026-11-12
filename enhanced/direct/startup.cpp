// T7 local bootstrap: prepare the independent, self-asserted offline profile from
// the launcher's command line, never an Xbox account. Bootstrap is not yet wired to engine startup.
// Original Ghosts P0029: bootstrap the independent local profile from the same command line
// used by LaunchDirect.ps1. This does not touch vendor user/license state, game
// dvars, networking, client connection state, or the engine command buffer.
#include "profile.h"

#ifdef _WIN32
extern "C" __declspec(dllimport) char *GetCommandLineA();
#else
extern "C" char *GetCommandLineA();
#endif
extern "C" __declspec(dllimport) void OutputDebugStringA(const char *);
extern "C" void T7DirectStartupMilestone(const char *s) { OutputDebugStringA(s); }

namespace
{
// The launcher emits ASCII commands, including a quoted player name. Parse
// tokens (not substrings) to avoid mistaking +direct_player within a path or
// quoted argument for a command. Quoted arguments must be terminated.
int NextToken(const char *&cursor, const char *end, char *out, unsigned capacity)
{
    while (cursor < end && (*cursor == ' ' || *cursor == '\t')) ++cursor;
    if (cursor == end || !*cursor) return 0;
    bool quoted = false;
    unsigned count = 0;
    while (cursor < end && *cursor)
    {
        const char c = *cursor;
        if (c == '"') { quoted = !quoted; ++cursor; continue; }
        if (!quoted && (c == ' ' || c == '\t')) break;
        if (count + 1 >= capacity) return -1;
        out[count++] = c;
        ++cursor;
    }
    if (quoted || !count) return -1;
    out[count] = 0;
    return 1;
}
bool Same(const char *a, const char *b)
{
    while (*a && *b && *a == *b) { ++a; ++b; }
    return *a == *b;
}
}

extern "C" int T7DirectLoadStartupProfile()
{
    // A malformed subsequent invocation must never retain an earlier local ID.
    T7DirectPlayerConfigure(nullptr, nullptr);
    const char *command = GetCommandLineA();
    if (!command) return 0;
    const char *end = command;
    // A bounded command-line scan prevents unexpected unlimited reads.
    for (unsigned length = 0; length < 8192; ++length)
    {
        if (!*end) break;
        ++end;
    }
    if (end == command || *end) return 0;
    const char *cursor = command;
    char token[1024];
    char id[32] = {};
    char name[64] = {};
    unsigned matches = 0;
    for (unsigned tokens = 0; tokens < 256; ++tokens)
    {
        const int found = NextToken(cursor, end, token, sizeof(token));
        if (!found) break;
        if (found < 0) return 0;
        if (!Same(token, "+direct_player")) continue;
        if (++matches != 1) return 0;
        if (NextToken(cursor, end, id, sizeof(id)) != 1) return 0;
        if (NextToken(cursor, end, name, sizeof(name)) != 1) return 0;
    }
    if (cursor < end && *cursor) return 0; // too many tokens or incomplete scan
    if (matches != 1 || !T7DirectPlayerConfigure(id, name)) return 0;
    // The engine may not yet have registered its own name dvar. Its normal
    // direct_player command can synchronise those later without affecting us.
    T7DirectStartupMilestone("T7D:LOCAL_PROFILE_PREPARED");
    return 1;
}
