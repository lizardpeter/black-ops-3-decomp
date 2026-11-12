#pragma once
// Custom-session identity, never a vendor account or proof of authentication.
extern "C" int T7DirectPlayerConfigure(const char *hexId, const char *name);
extern "C" unsigned long long T7DirectPlayerId(int controller);
extern "C" const char *T7DirectPlayerIdText(int controller);
extern "C" const char *T7DirectPlayerName(int controller);
