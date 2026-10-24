// libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket-xboxone.cpp
//
// Demonware's UDP socket layer: every Demonware datagram (lobby, NAT traversal, QoS, relays) goes through these.
// The source path is the library's own __FILE__ string; the method names are in its log strings
// ("bdPlatformSocket::bind"); prototypes and class layout come from Ghosts' Xbox One server PDB (see
// bdPlatformSocket.h). Original line numbers are unknown; the line numbers passed to bdLogMessage are the original's
// (from the binary). Functions are in the Store build's address order.

#include <ctype.h>
#include <string.h>
#include <winsock2.h>

#include "libs/DemonWareGDK/bdCore/bdLogMessage.h"
#include "libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket.h"

#define BD_SOCKET_FILE "C:\\trees\\outrun\\outrun\\t7\\code\\libs\\DemonWareGDK\\bdPlatform\\bdPlatformSocket\\bdPlatformSocket-xboxone.cpp"
#define bdLog(type, channel, function, line, ...) \
	bdLogMessage(type, channel, "bdPlatformSocket", BD_SOCKET_FILE, function, line, __VA_ARGS__)

// 1429C3F60  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket-xboxone.cpp
bdSocketStatusCode bdPlatformSocket::bind(int &handle, const bdSockAddr addr, const unsigned short port)
{
	if (handle == -1)
		return BD_NET_INVALID_HANDLE;
	int error;
	if (addr.m_family == AF_INET)
	{
		sockaddr_in local;
		*(unsigned long long *)local.sin_zero = 0;
		local.sin_family = AF_INET;
		local.sin_addr.s_addr = addr.inUn.m_iaddr;
		local.sin_port = htons(port);
		if (::bind(handle, (sockaddr *)&local, sizeof(local)) != SOCKET_ERROR)
			return BD_NET_SUCCESS;
		error = WSAGetLastError();
		bdLog(BD_LOG_WARNING, "warn/", "bdPlatformSocket::bind", 177, "Call to bind() failed, WSAGetLastError [%d]",
		      error);
		if (error == 6) // WSA_INVALID_HANDLE
			return BD_NET_INVALID_HANDLE;
		if (error == 10013) // WSAEACCES
			return BD_NET_ADDRESS_IN_USE;
		if (error == 10014) // WSAEFAULT
		{
			bdLog(BD_LOG_WARNING, "warn/", "bdPlatformSocket::bind", 191, "Bad pointer ", 10014);
			return BD_NET_ERROR;
		}
	}
	else if (addr.m_family == AF_INET6)
	{
		// the address is not used: an IPv6 socket is always bound to the unspecified address
		unsigned char storage[128];
		memset(storage, 0, sizeof(storage));
		sockaddr_in6 *local = (sockaddr_in6 *)storage;
		local->sin6_family = AF_INET6;
		local->sin6_port = htons(port);
		if (::bind(handle, (sockaddr *)storage, sizeof(storage)) == 0)
			return BD_NET_SUCCESS;
		error = WSAGetLastError();
		bdLog(BD_LOG_WARNING, "warn/", "bdPlatformSocket::bind", 234, "Call to bind() failed, WSAGetLastError [%d]",
		      error);
		if (error == 6)
			return BD_NET_INVALID_HANDLE;
		if (error == 10013)
			return BD_NET_ADDRESS_IN_USE;
	}
	else
	{
		return BD_NET_ERROR;
	}
	if (error == 10048 || error == 10049) // WSAEADDRINUSE, WSAEADDRNOTAVAIL
		return BD_NET_ADDRESS_IN_USE;
	return BD_NET_ERROR;
}

// 1429C4290  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket-xboxone.cpp
bool bdPlatformSocket::close(int &handle)
{
	if (handle == -1)
		return true;
	bool closed = closesocket(handle) == 0;
	handle = -1;
	return closed;
}

// 1429C4320  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket-xboxone.cpp
int bdPlatformSocket::create(const unsigned int family, const bool blocking, const bool broadcast)
{
	int handle = -1;
	if (family == AF_INET)
	{
		handle = (int)socket(family, SOCK_DGRAM, IPPROTO_UDP);
		if (broadcast)
		{
			u_long enable = 1;
			if (setsockopt(handle, SOL_SOCKET, SO_BROADCAST, (const char *)&enable, sizeof(enable)) != 0)
				return -1;
		}
	}
	else if (family == AF_INET6)
	{
		handle = (int)WSASocketA(family, SOCK_DGRAM, IPPROTO_UDP, NULL, 0, WSA_FLAG_OVERLAPPED);
		if (handle == -1)
		{
			bdLog(BD_LOG_ERROR, "err/", "bdPlatformSocket::create", 66,
			      "Call to WSASocket() failed, WSAGetLastError [%d]", WSAGetLastError());
			handle = -1;
		}
		u_long v6only = 0;
		if (setsockopt(handle, IPPROTO_IPV6, IPV6_V6ONLY, (const char *)&v6only, sizeof(v6only)) != 0)
		{
			bdLog(BD_LOG_WARNING, "warn/", "bdPlatformSocket::create", 99,
			      "Call to setsockopt() failed, WSAGetLastError [%d]", WSAGetLastError());
			return -1;
		}
	}
	if (handle != -1)
	{
		u_long nonBlocking = blocking ^ 1;
		if (ioctlsocket(handle, FIONBIO, &nonBlocking) != 0)
			handle = -1;
	}
	return handle;
}

// 1429C4600  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket-xboxone.cpp
int bdPlatformSocket::create(const bool blocking, const bool broadcast)
{
	return create(AF_INET, blocking, broadcast);
}

// 1429C4620  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket-xboxone.cpp
unsigned int bdPlatformSocket::getHostByName(const char *const hostName, bdSockAddr *addrs, unsigned int maxAddrs,
                                             const int handle)
{
	unsigned int found = 0;
	addrinfo hints;
	memset(&hints, 0, sizeof(hints));
	hints.ai_family = AF_INET;
	hints.ai_socktype = SOCK_DGRAM;
	addrinfo *result = NULL;
	if (!isalpha(hostName[0]))
		hints.ai_flags |= AI_NUMERICHOST;
	if (getaddrinfo(hostName, NULL, &hints, &result) == 0 && result)
	{
		for (addrinfo *ai = result; found < maxAddrs && ai; ai = ai->ai_next)
		{
			sockaddr_in in;
			memset(&in, 0, sizeof(in));
			memcpy(&in, ai->ai_addr, ai->ai_addrlen);
			found++;
			addrs->inUn.m_iaddr = in.sin_addr.s_addr;
			addrs++;
		}
		freeaddrinfo(result);
		return found;
	}
	int error = WSAGetLastError();
	if (error == 11001) // WSAHOST_NOT_FOUND
		bdLog(BD_LOG_WARNING, "warn/", "bdPlatformSocket::getHostByName", 649, "Host Not Found [%s]", hostName);
	else
		bdLog(BD_LOG_WARNING, "warn/", "bdPlatformSocket::getHostByName", 653, "getHostByName: Error [%d]", error);
	return found;
}

// The WinSock errors receiveFrom and sendTo report as a reset connection (WSAENETDOWN, WSAENETUNREACH,
// WSAECONNABORTED, WSAECONNRESET, WSAETIMEDOUT, WSAEHOSTUNREACH)
static inline bool bdIsResetError(int error)
{
	switch (error)
	{
	case 10050:
	case 10051:
	case 10053:
	case 10054:
	case 10060:
	case 10065:
		return true;
	}
	return false;
}

// 1429C4790  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket-xboxone.cpp
int bdPlatformSocket::receiveFrom(const int handle, bdSockAddr &addr, unsigned short &port, void *data,
                                  const unsigned int size)
{
	if (handle == -1)
		return BD_NET_INVALID_HANDLE;
	WSABUF buffer;
	buffer.len = size;
	buffer.buf = (char *)data;
	unsigned long received = 0;
	unsigned long flags = 0;
	memset(addr.inUn.m_sockaddr_storage, 0, sizeof(addr.inUn.m_sockaddr_storage));
	int fromLength = sizeof(addr.inUn.m_sockaddr_storage);
	sockaddr *from = (sockaddr *)addr.inUn.m_sockaddr_storage;
	if (WSARecvFrom(handle, &buffer, 1, &received, &flags, from, &fromLength, NULL, NULL) == SOCKET_ERROR)
	{
		int error = WSAGetLastError();
		if (error == 10004) // WSAEINTR
			return BD_NET_BLOCKING_CALL_CANCELED;
		if (error == 6)
			return BD_NET_INVALID_HANDLE;
		if (error == 10022) // WSAEINVAL
			return BD_NET_NOT_BOUND;
		if (error == 10035) // WSAEWOULDBLOCK
			return BD_NET_WOULD_BLOCK;
		if (error == 10040) // WSAEMSGSIZE
			return BD_NET_MSG_SIZE;
		if (!bdIsResetError(error))
			return BD_NET_ERROR;
		// the family checked here is the caller's, not the received one
		if (addr.m_family == AF_INET)
		{
			bdLog(BD_LOG_INFO, "info/", "bdPlatformSocket::receiveFrom", 511,
			      "recv: Received connection reset: error[%d]", error);
			port = ntohs(((sockaddr_in *)from)->sin_port);
			addr.inUn.m_iaddr = ((sockaddr_in *)from)->sin_addr.s_addr;
			return BD_NET_CONNECTION_RESET;
		}
		if (addr.m_family == AF_INET6)
		{
			bdLog(BD_LOG_INFO, "info/", "bdPlatformSocket::receiveFrom", 520,
			      "recv: Received connection reset: error[%d]", error);
			port = ntohs(((sockaddr_in6 *)from)->sin6_port);
			memcpy(addr.inUn.m_iaddr6, &((sockaddr_in6 *)from)->sin6_addr, 16);
			return BD_NET_CONNECTION_RESET;
		}
		return BD_NET_ERROR;
	}
	if (from->sa_family == AF_INET)
	{
		port = ntohs(((sockaddr_in *)from)->sin_port);
		addr.inUn.m_iaddr = ((sockaddr_in *)from)->sin_addr.s_addr;
		m_totalBytesRecvd += (unsigned int)(received + 28);
		m_totalPacketsRecvd++;
		return received;
	}
	if (from->sa_family == AF_INET6)
	{
		// the address is left where WSARecvFrom put it (records/bugs.tsv)
		port = ntohs(((sockaddr_in6 *)from)->sin6_port);
		m_totalBytesRecvd += (unsigned int)(received + 48);
		m_totalPacketsRecvd++;
		return received;
	}
	return BD_NET_ERROR;
}

// 1429C4AC0  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket-xboxone.cpp
int bdPlatformSocket::sendTo(const int handle, const bdSockAddr addr, const unsigned short port, const void *data,
                             const unsigned int length)
{
	if (handle == -1)
		return BD_NET_INVALID_HANDLE;
	int error;
	if (addr.m_family == AF_INET)
	{
		sockaddr_in to;
		*(unsigned long long *)to.sin_zero = 0;
		to.sin_family = AF_INET;
		to.sin_addr.s_addr = addr.inUn.m_iaddr;
		to.sin_port = htons(port);
		int sent = sendto(handle, (const char *)data, length, 0, (sockaddr *)&to, sizeof(to));
		if (sent >= 0)
		{
			m_totalBytesSent += (long long)(sent + 28);
			m_totalPacketsSent++;
			return sent;
		}
		error = WSAGetLastError();
		if (error == 10004)
			return BD_NET_BLOCKING_CALL_CANCELED;
		if (error == 6)
			return BD_NET_INVALID_HANDLE;
		if (bdIsResetError(error))
		{
			bdLog(BD_LOG_INFO, "info/", "bdPlatformSocket::sendTo", 332, "send: Received connection reset: error[%d]",
			      error);
			return BD_NET_CONNECTION_RESET;
		}
	}
	else if (addr.m_family == AF_INET6)
	{
		unsigned char storage[128];
		memset(storage, 0, sizeof(storage));
		sockaddr_in6 *to = (sockaddr_in6 *)storage;
		memcpy(&to->sin6_addr, addr.inUn.m_iaddr6, 16);
		to->sin6_family = AF_INET6;
		to->sin6_port = htons(port);
		unsigned long sent = 0;
		WSABUF buffer;
		buffer.len = length;
		buffer.buf = (char *)data;
		if (WSASendTo(handle, &buffer, 1, &sent, 0, (sockaddr *)storage, sizeof(storage), NULL, NULL) >= 0)
		{
			m_totalBytesSent += (unsigned int)(sent + 48);
			m_totalPacketsSent++;
			return sent;
		}
		error = WSAGetLastError();
		if (error == 10004)
			return BD_NET_BLOCKING_CALL_CANCELED;
		if (error == 6)
			return BD_NET_INVALID_HANDLE;
		if (bdIsResetError(error))
		{
			bdLog(BD_LOG_INFO, "info/", "bdPlatformSocket::sendTo", 420, "Send: Received connection reset: error[%d]",
			      error);
			return BD_NET_CONNECTION_RESET;
		}
	}
	else
	{
		return BD_NET_ERROR;
	}
	switch (error)
	{
	case 10022: // WSAEINVAL
	case 10039: // WSAEDESTADDRREQ
	case 10047: // WSAEAFNOSUPPORT
	case 10049: // WSAEADDRNOTAVAIL
		return BD_NET_ADDRESS_INVALID;
	case 10035:
		return BD_NET_WOULD_BLOCK;
	case 10040:
		return BD_NET_MSG_SIZE;
	}
	return BD_NET_ERROR;
}
