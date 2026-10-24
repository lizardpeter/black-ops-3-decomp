// libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket-xboxone.cpp
//
// Demonware's TCP socket layer: the connections to Demonware's lobby and auth servers (bdLobbyConnection,
// bdUnicastConnection) go through these. The source path and close's name are in the library's own strings
// ("bdPlatformStreamSocket::close"); the other names, prototypes and the statistics are from Ghosts' Xbox One server
// PDB (bdPlatformStreamSocket.h), matched by what each function does. Original line numbers are unknown; the line
// numbers passed to bdLogMessage are the original's. Functions are in the Store build's address order.

#include <winsock2.h>

#include "libs/DemonWareGDK/bdCore/bdLogMessage.h"
#include "libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket.h"

#define BD_STREAM_FILE "C:\\trees\\outrun\\outrun\\t7\\code\\libs\\DemonWareGDK\\bdPlatform\\bdPlatformSocket\\bdPlatformStreamSocket-xboxone.cpp"

// 142D16EC0  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket-xboxone.cpp
// Whether the socket has a pending exception (or select itself failed).
bool bdPlatformStreamSocket::checkSocketException(const int handle)
{
	timeval timeout = {0, 0};
	fd_set exceptions;
	exceptions.fd_count = 1;
	exceptions.fd_array[0] = handle;
	if (select(0, NULL, NULL, &exceptions, &timeout) == SOCKET_ERROR)
		return true;
	return __WSAFDIsSet(handle, &exceptions) != 0;
}

// 142D16F40  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket-xboxone.cpp
bool bdPlatformStreamSocket::close(const int handle)
{
	if (handle == -1)
		return true;
	int result = closesocket(handle);
	if (result == 0)
		return true;
	if (result == SOCKET_ERROR)
		bdLogMessage(BD_LOG_WARNING, "warn/", "bdPlatformStreamSocket", BD_STREAM_FILE, "bdPlatformStreamSocket::close",
		             423, "Failed to close socket Error %i.", WSAGetLastError());
	else
		bdLogMessage(BD_LOG_WARNING, "warn/", "bdPlatformStreamSocket", BD_STREAM_FILE, "bdPlatformStreamSocket::close",
		             428, "Failed to close socket. Unknown Error Code %i.", result);
	return false;
}

// 142D17050  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket-xboxone.cpp
// IPv4 only: the address family is not looked at.
bdSocketStatusCode bdPlatformStreamSocket::connect(const int handle, const bdSockAddr addr, const unsigned short port)
{
	sockaddr_in to;
	*(unsigned long long *)to.sin_zero = 0;
	to.sin_family = AF_INET;
	to.sin_addr.s_addr = addr.inUn.m_iaddr;
	to.sin_port = htons(port);
	if (::connect(handle, (sockaddr *)&to, sizeof(to)) >= 0)
		return BD_NET_SUCCESS;
	switch (WSAGetLastError())
	{
	case 6: // WSA_INVALID_HANDLE
		return BD_NET_INVALID_HANDLE;
	case 10004: // WSAEINTR
		return BD_NET_BLOCKING_CALL_CANCELED;
	case 10022: // WSAEINVAL
		return BD_NET_NOT_BOUND;
	case 10035: // WSAEWOULDBLOCK
		return BD_NET_WOULD_BLOCK;
	case 10040: // WSAEMSGSIZE
		return BD_NET_MSG_SIZE;
	case 10050: // WSAENETDOWN
	case 10051: // WSAENETUNREACH
	case 10053: // WSAECONNABORTED
	case 10054: // WSAECONNRESET
	case 10060: // WSAETIMEDOUT
	case 10065: // WSAEHOSTUNREACH
		return BD_NET_CONNECTION_RESET;
	}
	return BD_NET_ERROR;
}

// 142D171E0  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket-xboxone.cpp
int bdPlatformStreamSocket::create(const unsigned int family, const bool blocking)
{
	int handle = -1;
	if (family == AF_INET)
		handle = (int)socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
	else if (family == AF_INET6)
		handle = (int)socket(AF_INET6, SOCK_STREAM, IPPROTO_TCP);
	if (handle != -1)
	{
		u_long nonBlocking = blocking ^ 1;
		if (ioctlsocket(handle, FIONBIO, &nonBlocking) != 0)
			handle = -1;
	}
	return handle;
}

// 142D172C0  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket-xboxone.cpp
int bdPlatformStreamSocket::create(const bool blocking)
{
	return create(AF_INET, blocking);
}

// 142D172D0  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket-xboxone.cpp
bool bdPlatformStreamSocket::isWritable(const int handle)
{
	timeval timeout = {0, 0};
	fd_set writable;
	writable.fd_count = 1;
	writable.fd_array[0] = handle;
	fd_set exceptions;
	exceptions.fd_count = 1;
	exceptions.fd_array[0] = handle;
	int result = select(0, NULL, &writable, &exceptions, &timeout);
	bool isWritable = __WSAFDIsSet(handle, &writable) && result != SOCKET_ERROR;
	if (__WSAFDIsSet(handle, &exceptions))
		WSAGetLastError();
	return isWritable;
}

// 142D173A0  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket-xboxone.cpp
bool bdPlatformStreamSocket::isWritable(const int handle, bdSocketStatusCode &status)
{
	status = BD_NET_SUCCESS;
	timeval timeout = {0, 0};
	fd_set writable;
	writable.fd_count = 1;
	writable.fd_array[0] = handle;
	fd_set exceptions;
	exceptions.fd_count = 1;
	exceptions.fd_array[0] = handle;
	int result = select(0, NULL, &writable, &exceptions, &timeout);
	bool isWritable = __WSAFDIsSet(handle, &writable) && result != SOCKET_ERROR;
	if (__WSAFDIsSet(handle, &exceptions))
	{
		switch (WSAGetLastError())
		{
		case 10004: // WSAEINTR
			status = BD_NET_BLOCKING_CALL_CANCELED;
			break;
		case 10022: // WSAEINVAL
			status = BD_NET_INVALID_HANDLE;
			break;
		case 10050: // WSAENETDOWN
		case 10053: // WSAECONNABORTED
		case 10054: // WSAECONNRESET
		case 10060: // WSAETIMEDOUT
			status = BD_NET_CONNECTION_RESET;
			break;
		case 10051: // WSAENETUNREACH
		case 10065: // WSAEHOSTUNREACH
			status = BD_NET_HOST_UNREACH;
			break;
		case 10057: // WSAENOTCONN
			status = BD_NET_NOT_CONNECTED;
			break;
		default:
			status = BD_NET_ERROR;
			break;
		}
	}
	return isWritable;
}

// 142D17530  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket-xboxone.cpp
int bdPlatformStreamSocket::receive(const int handle, void *const data, const unsigned int size)
{
	if (handle == -1)
		return BD_NET_INVALID_HANDLE;
	int received = recv(handle, (char *)data, size, 0);
	if (received >= 0)
	{
		m_totalBytesRecvd += received;
		return received;
	}
	switch (WSAGetLastError())
	{
	case 6:
		return BD_NET_INVALID_HANDLE;
	case 10004:
		return BD_NET_BLOCKING_CALL_CANCELED;
	case 10022:
		return BD_NET_NOT_BOUND;
	case 10035:
		return BD_NET_WOULD_BLOCK;
	case 10050:
	case 10051:
	case 10053:
	case 10054:
	case 10060:
	case 10065:
		return BD_NET_CONNECTION_RESET;
	case 10057: // WSAENOTCONN: the result is dropped and it falls through (records/bugs.tsv)
		checkSocketException(handle);
	case 10040:
		return BD_NET_MSG_SIZE;
	}
	return BD_NET_ERROR;
}

// 142D176F0  libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformStreamSocket-xboxone.cpp
int bdPlatformStreamSocket::send(const int handle, const void *const data, const unsigned int length)
{
	if (handle == -1)
		return BD_NET_INVALID_HANDLE;
	int sent = ::send(handle, (const char *)data, length, 0);
	if (sent >= 0)
	{
		m_totalBytesSent += sent;
		return sent;
	}
	switch (WSAGetLastError())
	{
	case 6:
		return BD_NET_INVALID_HANDLE;
	case 10004:
		return BD_NET_BLOCKING_CALL_CANCELED;
	case 10022: // WSAEINVAL
	case 10039: // WSAEDESTADDRREQ
	case 10047: // WSAEAFNOSUPPORT
	case 10049: // WSAEADDRNOTAVAIL
		return BD_NET_ADDRESS_INVALID;
	case 10035:
		return BD_NET_WOULD_BLOCK;
	case 10040:
		return BD_NET_MSG_SIZE;
	case 10050:
	case 10051:
	case 10053:
	case 10054:
	case 10060:
	case 10061: // WSAECONNREFUSED
	case 10065:
		return BD_NET_CONNECTION_RESET;
	case 10057: // WSAENOTCONN
		return checkSocketException(handle) ? BD_NET_CONNECTION_RESET : BD_NET_NOT_CONNECTED;
	}
	return BD_NET_ERROR;
}
