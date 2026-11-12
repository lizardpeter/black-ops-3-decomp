// P0019: local profile strings used by our custom-session packet path.
#include "profile.h"
namespace
{
unsigned long long playerId;
char idText[17];
char playerName[32];
}
extern "C" int T7DirectPlayerConfigure(const char *hexId, const char *name)
{
    // Startup/command-thread only. A rejected configuration revokes the old ID.
    playerId = 0;
    idText[0] = 0;
    playerName[0] = 0;
    if (!hexId || !name) return 0;
    unsigned long long value = 0;
    for (unsigned int i = 0; i < 16; ++i)
    {
        const unsigned char c = (unsigned char)hexId[i];
        unsigned int digit;
        if (c >= '0' && c <= '9') digit = c - '0';
        else if (c >= 'a' && c <= 'f') digit = c - 'a' + 10;
        else if (c >= 'A' && c <= 'F') digit = c - 'A' + 10;
        else return 0;
        value = (value << 4) | digit;
    }
    if (hexId[16] || !value) return 0;
    unsigned int count = 0;
    for (; name[count]; ++count)
    {
        const unsigned char c = (unsigned char)name[count];
        if (count >= 31 || !((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
            (c >= '0' && c <= '9') || c == ' ' || c == '_' || c == '-')) return 0;
    }
    if (!count || name[0] == ' ' || name[count - 1] == ' ') return 0;
    for (unsigned int i = 0; i < 16; ++i)
    {
        const char c = hexId[i];
        idText[i] = c >= 'A' && c <= 'F' ? c + ('a' - 'A') : c;
    }
    idText[16] = 0;
    for (unsigned int i = 0; i <= count; ++i) playerName[i] = name[i];
    playerId = value;
    return 1;
}
extern "C" unsigned long long T7DirectPlayerId(int controller) { return controller == 0 ? playerId : 0; }
extern "C" const char *T7DirectPlayerIdText(int controller) { return controller == 0 ? idText : ""; }
extern "C" const char *T7DirectPlayerName(int controller) { return controller == 0 ? playerName : ""; }
