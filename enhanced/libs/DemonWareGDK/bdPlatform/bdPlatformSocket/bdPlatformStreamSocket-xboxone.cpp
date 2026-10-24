// P0005: Demonware's TCP sockets never reach the network.
//
// Demonware's lobby and auth connections (bdLobbyConnection, bdUnicastConnection) go through bdPlatformStreamSocket.
// In the enhanced build no TCP socket is ever created, so no connection is ever made; each method reports what the
// faithful one reports when there is no connection, without calling Winsock or logging. close() stays faithful: it
// only closes handles create() returned, and there are none. docs/network.md section 1.

#include "libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket.h"

// a socket with nothing behind it always has an exception pending
bool bdPlatformStreamSocket::checkSocketException(const int handle)
{
	return true;
}

bdSocketStatusCode bdPlatformStreamSocket::connect(const int handle, const bdSockAddr addr, const unsigned short port)
{
	return BD_NET_ERROR;
}

// socket creation fails, as when socket() returns INVALID_SOCKET
int bdPlatformStreamSocket::create(const unsigned int family, const bool blocking)
{
	return -1;
}

int bdPlatformStreamSocket::create(const bool blocking)
{
	return -1;
}

bool bdPlatformStreamSocket::isWritable(const int handle)
{
	return false;
}

bool bdPlatformStreamSocket::isWritable(const int handle, bdSocketStatusCode &status)
{
	status = BD_NET_NOT_CONNECTED;
	return false;
}

int bdPlatformStreamSocket::receive(const int handle, void *const data, const unsigned int size)
{
	return handle == -1 ? BD_NET_INVALID_HANDLE : BD_NET_NOT_CONNECTED;
}

int bdPlatformStreamSocket::send(const int handle, const void *const data, const unsigned int length)
{
	return handle == -1 ? BD_NET_INVALID_HANDLE : BD_NET_NOT_CONNECTED;
}
