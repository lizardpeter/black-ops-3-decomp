// Demonware platform sockets (reconstructed). Class layout, enum values and prototypes are from Ghosts' Xbox One
// server PDB (lizardpeter/ghosts-decomp, iw6_ds_xb3: bdSockAddr is 0x84 bytes, the family at 0x80), whose Demonware
// has the same IPv4/IPv6 platform socket. BO3's Store build adds create(family, blocking, broadcast).
#pragma once

enum bdSocketStatusCode
{
	BD_NET_SUCCESS = 1,
	BD_NET_CONNECTION_CLOSED = 0,
	BD_NET_ERROR = -1,
	BD_NET_WOULD_BLOCK = -2,
	BD_NET_SUBSYTEM_ERROR = -3,
	BD_NET_ADDRESS_IN_USE = -4,
	BD_NET_CONNECTION_RESET = -5,
	BD_NET_MSG_SIZE = -6,
	BD_NET_ADDRESS_INVALID = -7,
	BD_NET_BLOCKING_CALL_CANCELED = -8,
	BD_NET_NOT_BOUND = -9,
	BD_NET_INVALID_HANDLE = -10,
	BD_NET_NOT_CONNECTED = -11,
	BD_NET_CONNECTION_REFUSED = -12,
	BD_NET_HOST_UNREACH = -13,
};

class bdSockAddr
{
public:
	union
	{
		unsigned int m_iaddr;
		unsigned char m_iaddr6[16];
		unsigned char m_sockaddr_storage[128];
	} inUn;
	unsigned short m_family;
};

class bdPlatformSocket
{
public:
	static int create(const unsigned int family, const bool blocking, const bool broadcast);
	static int create(const bool blocking, const bool broadcast);
	static bdSocketStatusCode bind(int &handle, const bdSockAddr addr, const unsigned short port);
	static int sendTo(const int handle, const bdSockAddr addr, const unsigned short port, const void *data,
	                  const unsigned int length);
	static int receiveFrom(const int handle, bdSockAddr &addr, unsigned short &port, void *data,
	                       const unsigned int size);
	static bool close(int &handle);
	static unsigned int getHostByName(const char *const hostName, bdSockAddr *addrs, unsigned int maxAddrs,
	                                  const int handle);

private:
	static unsigned long long m_totalBytesSent;
	static unsigned long long m_totalPacketsSent;
	static unsigned long long m_totalBytesRecvd;
	static unsigned long long m_totalPacketsRecvd;
};
