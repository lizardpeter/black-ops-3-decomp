// universal/dvar.h (reconstructed: only what reconstructed code uses so far)
#pragma once

struct dvar_t;

// Dvar flags seen so far (meanings from use, not from symbols).
enum
{
	DVAR_LATCH = 0x10,  // a change waits for a restart (Dvar_SetVariant: "will be changed upon restarting")
};

// Registration. Names are hashed (Dvar_GenerateHash, 1413DF170): the Store build passes the hash and an empty
// name and description. The last parameter is 0 at every call reconstructed so far; when set,
// Dvar_RegisterVariant (1423A6AE0) takes its session-mode path (type-15 base dvars), hence the name.
const dvar_t *Dvar_RegisterBool(unsigned int hash, const char *dvarName, bool value, unsigned int flags,
                                const char *description, bool sessionModeBased);
const dvar_t *Dvar_RegisterFloat(unsigned int hash, const char *dvarName, float value, float min, float max,
                                 unsigned int flags, const char *description, bool sessionModeBased);
const dvar_t *Dvar_RegisterInt(unsigned int hash, const char *dvarName, int value, int min, int max,
                               unsigned int flags, const char *description, bool sessionModeBased);
const dvar_t *Dvar_RegisterString(unsigned int hash, const char *dvarName, const char *value, unsigned int flags,
                                  const char *description, bool sessionModeBased);
const dvar_t *Dvar_RegisterVec3(unsigned int hash, const char *dvarName, float x, float y, float z, float min,
                                float max, unsigned int flags, const char *description, bool sessionModeBased);
const dvar_t *Dvar_RegisterEnum(unsigned int hash, const char *dvarName, const char **valueList, int defaultIndex,
                                unsigned int flags, const char *description, bool sessionModeBased);

// Who set a value (Dvar_SetVariant's last argument)
enum DvarSetSource
{
	DVAR_SOURCE_INTERNAL = 0,
	DVAR_SOURCE_EXTERNAL = 1,
};

void Dvar_SetInt(const dvar_t *dvar, int value, DvarSetSource source);

bool Dvar_GetBool(const dvar_t *dvar);
int Dvar_GetInt(const dvar_t *dvar);
float Dvar_GetFloat(const dvar_t *dvar);
