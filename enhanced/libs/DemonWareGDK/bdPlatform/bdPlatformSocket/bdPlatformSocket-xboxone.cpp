// P0004: Demonware's UDP sockets never reach the network.
//
// Every Demonware datagram (lobby, matchmaking, NAT traversal, QoS probes, TURN relays) and every Demonware DNS
// lookup goes through bdPlatformSocket. In the enhanced build no socket is ever created and no name is ever looked
// up, so nothing leaves the machine; each method reports what the faithful one reports for a network that is not
// there, without calling Winsock or logging. close() stays faithful: it only closes handles create() returned, and
// there are none. docs/network.md section 1.

#include "libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket.h"

// socket creation fails, as when socket() returns INVALID_SOCKET
int bdPlatformSocket::create(const unsigned int family, const bool blocking, const bool broadcast)
{
	return -1;
}

int bdPlatformSocket::create(const bool blocking, const bool broadcast)
{
	return -1;
}

bdSocketStatusCode bdPlatformSocket::bind(int &handle, const bdSockAddr addr, const unsigned short port)
{
	return handle == -1 ? BD_NET_INVALID_HANDLE : BD_NET_ERROR;
}

// no address is found: Demonware's hosts never resolve
unsigned int bdPlatformSocket::getHostByName(const char *const hostName, bdSockAddr *addrs, unsigned int maxAddrs,
                                             const int handle)
{
	return 0;
}

// nothing ever arrives
int bdPlatformSocket::receiveFrom(const int handle, bdSockAddr &addr, unsigned short &port, void *data,
                                  const unsigned int size)
{
	return handle == -1 ? BD_NET_INVALID_HANDLE : BD_NET_WOULD_BLOCK;
}

int bdPlatformSocket::sendTo(const int handle, const bdSockAddr addr, const unsigned short port, const void *data,
                             const unsigned int length)
{
	return handle == -1 ? BD_NET_INVALID_HANDLE : BD_NET_ERROR;
}
