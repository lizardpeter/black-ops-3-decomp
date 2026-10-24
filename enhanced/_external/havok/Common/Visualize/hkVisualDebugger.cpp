// P0008: Havok's Visual Debugger never opens its server (B0004).
//
// The Store build starts the VDB server while loading a level's navigation data and serves on TCP port 25001, bound to
// every interface, for the rest of the session: a listening socket in a game client, speaking a debug protocol never
// meant to face untrusted peers. In the enhanced build serve() does nothing, so m_server stays null and no socket is
// created, bound or listened on; the visual debugger itself is still created, so nothing that holds it changes.
// docs/security.md.

#include "_external/havok/hkVisualDebugger.h"

void hkVisualDebugger::serve(int listenPort)
{
}
