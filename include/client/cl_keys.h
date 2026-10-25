// client/cl_keys.h (reconstructed: only what reconstructed code uses so far)
#pragma once

enum { MAX_LOCAL_CLIENTS = 2 };

// Per local client (stride 0x1940 bytes, the client's key state block): set to 1 when the client's key bindings
// changed and must be written out.
extern int key_bindingsModified[];  // 1440AE91C, stride 0x650 ints

const char *va(const char *format, ...);
void sub_1423B4570(char *path, int size);
void sub_1413ECF90(int localClientNum, const char *name);
void sub_1413ED0D0();
