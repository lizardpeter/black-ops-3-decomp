// Havok's Visual Debugger server (reconstructed: only what reconstructed code uses). Havok is linked into the game as
// a library; there is no symbol build, so names follow Havok's own strings ("hkVisualDebugger.cpp", the messages)
// and the layout is only what the reconstructed methods use.
#pragma once

// hkReferencedObject's header: a vtable, then the memory size (high word) and reference count (low word)
struct hkReferencedObjectHeader
{
	void **vtable;
	volatile unsigned int memSizeAndRefCount;
};

struct hkResult
{
	int m_enum; // 0: HK_SUCCESS
};

// hkSocket: vtable slot 0x48 is listen(hkResult *result, int port), slot 0x18 deleteThis()
struct hkSocket
{
	hkReferencedObjectHeader header;
};

class hkVisualDebugger
{
public:
	void serve(int listenPort);

	unsigned char m_unknown0[0x10];
	hkSocket *m_server; // 0x10
};
