// Demonware platform TCP sockets (reconstructed). Prototypes from Ghosts' Xbox One server PDB (lizardpeter/ghosts-decomp,
// iw6_ds_xb3); only the methods the Store build links are declared.
#pragma once

#include "libs/DemonWareGDK/bdPlatform/bdPlatformSocket/bdPlatformSocket.h"

class bdPlatformStreamSocket
{
public:
	static int create(const unsigned int family, const bool blocking);
	static int create(const bool blocking);
	static bdSocketStatusCode connect(const int handle, const bdSockAddr addr, const unsigned short port);
	static int send(const int handle, const void *const data, const unsigned int length);
	static int receive(const int handle, void *const data, const unsigned int size);
	static bool close(const int handle);
	static bool checkSocketException(const int handle);
	static bool isWritable(const int handle, bdSocketStatusCode &status);
	static bool isWritable(const int handle);

private:
	static unsigned long long m_totalBytesSent;
	static unsigned long long m_totalBytesRecvd;
};
