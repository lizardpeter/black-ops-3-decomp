// _external/havok/Common/Visualize/hkVisualDebugger.cpp
//
// Havok's Visual Debugger: a TCP server that streams physics and AI debug data to Havok's VDB client. The Store build
// starts it while loading a level's navigation data (141EBC350, from 141EBE450) and serves on port 25001, bound to
// every interface: records/bugs.tsv B0004, docs/security.md. The file name and line numbers are the ones Havok's own
// error reports pass (hkVisualDebugger.cpp, lines 111, 122, 127).

#include "_external/havok/hkVisualDebugger.h"

#define T7_SOURCE "_external/havok/Common/Visualize/hkVisualDebugger.cpp"
#include <t7_static.h>

// Havok's timer sink: vtable slot 0x50 begins a named timer, 0x58 ends it
struct hkTimerSink
{
	void **vtable;
};
T7_STATIC hkTimerSink *s_hkTimers T7_AT("", "s_hkTimers");
// hkSocket::s_create, the platform socket factory (hkBsdSocket on Windows)
extern hkSocket *(*hkSocketCreate)() __asm__("?s_create@hkSocket@@2P6APEAU1@XZEA");

// hkOstream over a caller's buffer, its two operator<< used here, and its destructor
struct hkOstream
{
	unsigned char opaque[0x18];
};
void sub_142A289C0(hkOstream *stream, char *buffer, int size);
hkOstream *sub_142A22450(hkOstream *stream, const char *text);
hkOstream *sub_142A22520(hkOstream *stream, int value);
void sub_142A28A80(hkOstream *stream);
// hkError's report (id, message, file, line)
void sub_142A3A300(int id, const char *message, const char *file, int line);

typedef void (*TimerBegin)(hkTimerSink *, unsigned int, const char *);
typedef void (*TimerEnd)(hkTimerSink *);
typedef hkResult *(*SocketListen)(hkSocket *, hkResult *, int);
typedef void (*DeleteThis)(hkSocket *);

// hkReferencedObject::removeReference, inlined: only objects with a memory size are reference counted
static inline void hkRemoveReference(hkSocket *object)
{
	if (((volatile unsigned short *)&object->header.memSizeAndRefCount)[1] == 0)
		return;
	unsigned int old, now;
	do
	{
		old = object->header.memSizeAndRefCount;
		now = (((old - 1) ^ old) & 0xFFFF) ^ old; // the low word decremented, the high word kept
	} while (!__atomic_compare_exchange_n(&object->header.memSizeAndRefCount, &old, now, false, __ATOMIC_SEQ_CST,
	                                      __ATOMIC_SEQ_CST));
	if ((unsigned short)now == 0)
		((DeleteThis)object->header.vtable[0x18 / 8])(object);
}

// 142AE2740  _external/havok/Common/Visualize/hkVisualDebugger.cpp
void hkVisualDebugger::serve(int listenPort)
{
	((TimerBegin)s_hkTimers->vtable[0x50 / 8])(s_hkTimers, 0x1293ADE8, "Serving");
	hkOstream stream;
	if (!m_server)
	{
		m_server = hkSocketCreate();
		if (m_server)
		{
			hkResult result;
			if (((SocketListen)m_server->header.vtable[0x48 / 8])(m_server, &result, listenPort)->m_enum == 0)
			{
				char text[512];
				sub_142A289C0(&stream, text, sizeof(text));
				sub_142A22450(sub_142A22520(sub_142A22450(&stream, "Server created and will poll for new client(s) on port "),
				                            listenPort),
				              " every frame");
				sub_142A3A300(-1, text, "hkVisualDebugger.cpp", 111);
				sub_142A28A80(&stream);
				((TimerEnd)s_hkTimers->vtable[0x58 / 8])(s_hkTimers);
				return;
			}
			hkRemoveReference(m_server);
			m_server = 0;
		}
		char text[512];
		sub_142A289C0(&stream, text, sizeof(text));
		sub_142A22450(sub_142A22520(sub_142A22450(&stream, "Server could not create connection, usually this means "
		                                                   "something is already listening on port "),
		                            listenPort),
		              ", or a permissions or hardware error is preventing a socket from being created.");
		sub_142A3A300(-1, text, "hkVisualDebugger.cpp", 122);
	}
	else
	{
		char text[512];
		sub_142A289C0(&stream, text, sizeof(text));
		sub_142A22450(&stream, "Server has already been created, only one server allowed per visual debugger instance");
		sub_142A3A300(-1, text, "hkVisualDebugger.cpp", 127);
	}
	sub_142A28A80(&stream);
	((TimerEnd)s_hkTimers->vtable[0x58 / 8])(s_hkTimers);
}
