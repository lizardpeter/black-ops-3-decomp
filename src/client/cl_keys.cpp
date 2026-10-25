// Key bindings. Source path assumed from the engine lineage (IW's client/cl_keys.cpp writes the bindings).

#include "client/cl_keys.h"

// 1413ED0D0  client/cl_keys.cpp
// Once a frame (from Com_Frame, between the client frame and the second event loop) and at shutdown: for each
// local client whose bindings changed, writes them out as "bindings_<n>" (the name copied into a 260-byte buffer,
// cut at 259 characters; an empty name if va fails).
void sub_1413ED0D0()
{
	int *modified = key_bindingsModified;
	for (int localClientNum = 0; localClientNum < MAX_LOCAL_CLIENTS; localClientNum++, modified += 0x650)
	{
		if (*modified != 1)
			continue;
		*modified = 0;
		char name[0x104];
		const char *formatted = va("%s_%d", "bindings", localClientNum);
		if (!formatted)
		{
			name[0] = 0;
		}
		else
		{
			unsigned long long i = 0;
			for (;;)
			{
				char c = formatted[i];
				name[i] = c;
				if (!c)
					break;
				if (++i == sizeof(name))
				{
					name[sizeof(name) - 1] = 0;
					break;
				}
			}
		}
		sub_1423B4570(name, sizeof(name));
		sub_1413ECF90(localClientNum, name);
	}
}
