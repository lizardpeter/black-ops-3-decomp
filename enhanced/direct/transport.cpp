// T7 local transport, adapted from the audited Ghosts direct transport.
// Isolated wire protocol for local development; no engine hooks yet. No DNS or vendor service calls.
#include "transport.h"
#ifdef _WIN32
#define IW6_PRIVATE_WINSOCK
#include <winsock2.h>
extern "C" __declspec(dllimport) int getsockname(SOCKET, sockaddr *, int *);
extern "C" __declspec(dllimport) int WSACleanup();
extern "C" __declspec(dllimport) void AcquireSRWLockExclusive(void *);
extern "C" __declspec(dllimport) void ReleaseSRWLockExclusive(void *);
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <fcntl.h>
#include <unistd.h>
#include <pthread.h>
using SOCKET = int;
#define INVALID_SOCKET (-1)
#define SOCKET_ERROR (-1)
#define closesocket close
#endif

namespace
{
constexpr int MaxPayload = 1262;
constexpr int HeaderSize = 8;
constexpr int MaxWire = HeaderSize + MaxPayload + 2;
constexpr unsigned int MaxPeers = 64;
SOCKET udp = INVALID_SOCKET;
bool initialized;
bool hosting;
unsigned short boundPort;
T7DirectAddress selected;
T7DirectAddress peers[MaxPeers];
unsigned int peerCount;
#ifdef _WIN32
unsigned long long lockStorage;
struct Lock
{
    Lock() { AcquireSRWLockExclusive(&lockStorage); }
    ~Lock() { ReleaseSRWLockExclusive(&lockStorage); }
};
#else
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
struct Lock
{
    Lock() { pthread_mutex_lock(&mutex); }
    ~Lock() { pthread_mutex_unlock(&mutex); }
};
#endif
unsigned short Swap(unsigned short port) { return (unsigned short)((port >> 8) | (port << 8)); }
bool Unicast(const unsigned char *ip) { return ip[0] > 0 && ip[0] < 224; }
bool Same(const T7DirectAddress &a, const T7DirectAddress &b, bool port)
{
    if (a.type != b.type) return false;
    if (a.type == T7_ADDR_LOOPBACK || a.type == T7_ADDR_BOT) return !port || a.port == b.port;
    if (a.type != T7_ADDR_IP) return false;
    for (int i = 0; i < 4; ++i) if (a.ip[i] != b.ip[i]) return false;
    return !port || a.port == b.port;
}
unsigned short Checksum(const unsigned char *data, int length)
{
    unsigned int sum = 0;
    while (length > 1) { sum += (data[0] << 8) | data[1]; data += 2; length -= 2; }
    if (length) sum += *data;
    while (sum >> 16) sum = (sum & 0xFFFF) + (sum >> 16);
    return (unsigned short)~sum;
}
sockaddr_in Sockaddr(const T7DirectAddress &a)
{
    sockaddr_in result = {};
    result.sin_family = AF_INET;
    result.sin_port = a.port;
    unsigned char *ip = (unsigned char *)&result.sin_addr;
    for (int i = 0; i < 4; ++i) ip[i] = a.ip[i];
    return result;
}
void Close()
{
    if (udp != INVALID_SOCKET) closesocket(udp);
    udp = INVALID_SOCKET;
#ifdef _WIN32
    if (initialized) WSACleanup();
#endif
    initialized = false;
    hosting = false;
    boundPort = 0;
    selected = {};
    peerCount = 0;
}
bool Permitted(const T7DirectAddress &a)
{
    if (!Unicast(a.ip) || a.type != T7_ADDR_IP || !a.port) return false;
    if (!hosting) return Same(selected, a, true);
    // A listener may reply only to peers from which a checksum-valid packet arrived.
    for (unsigned int i = 0; i < peerCount; ++i) if (Same(peers[i], a, true)) return true;
    return false;
}
}

extern "C" int T7DirectWireVersion() { return 1; }

extern "C" int T7DirectParse(const char *text, T7DirectAddress *address, int allowZeroPort)
{
    if (!address) return 0;
    *address = {};
    if (!text) return 0;
    T7DirectAddress result = {};
    for (int i = 0; i < 4; ++i)
    {
        unsigned int value = 0, digits = 0;
        while (*text >= '0' && *text <= '9')
        {
            value = value * 10 + (unsigned int)(*text++ - '0');
            if (++digits > 3 || value > 255) return 0;
        }
        if (!digits) return 0;
        result.ip[i] = (unsigned char)value;
        if (*text++ != (i == 3 ? ':' : '.')) return 0;
    }
    unsigned int port = 0, digits = 0;
    while (*text >= '0' && *text <= '9')
    {
        port = port * 10 + (unsigned int)(*text++ - '0');
        if (++digits > 5 || port > 65535) return 0;
    }
    const bool wildcard = allowZeroPort && !(result.ip[0] | result.ip[1] | result.ip[2] | result.ip[3]);
    if (*text || !digits || (!port && !allowZeroPort) || (!Unicast(result.ip) && !wildcard)) return 0;
    result.type = T7_ADDR_IP;
    result.port = Swap((unsigned short)port);
    result.addrHandleIndex = 0xFFFFFFFF;
    *address = result;
    return 1;
}
extern "C" int T7DirectOpen(const char *bindEndpoint, int server)
{
    Lock guard;
    // A failed reconfiguration must not leave a prior peer/socket live.
    Close();
    T7DirectAddress address;
    if (!T7DirectParse(bindEndpoint, &address, 1)) return 0;
#ifdef _WIN32
    WSADATA data;
    if (WSAStartup(0x202, &data)) return 0;
#endif
    initialized = true;
    udp = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (udp == INVALID_SOCKET) { Close(); return 0; }
#ifdef _WIN32
    u_long nonblocking = 1;
    if (ioctlsocket(udp, FIONBIO, &nonblocking) == SOCKET_ERROR) { Close(); return 0; }
#else
    if (fcntl(udp, F_SETFL, O_NONBLOCK) == -1) { Close(); return 0; }
#endif
    sockaddr_in local = Sockaddr(address);
    if (bind(udp, (sockaddr *)&local, sizeof(local)) == SOCKET_ERROR) { Close(); return 0; }
#ifdef _WIN32
    int size = sizeof(local);
#else
    socklen_t size = sizeof(local);
#endif
    if (getsockname(udp, (sockaddr *)&local, &size) == SOCKET_ERROR) { Close(); return 0; }
    boundPort = Swap(local.sin_port);
    hosting = server != 0;
    return 1;
}
extern "C" void T7DirectClose() { Lock guard; Close(); }
extern "C" unsigned short T7DirectPort() { Lock guard; return boundPort; }
extern "C" int T7DirectSelectPeer(const char *endpoint)
{
    T7DirectAddress address;
    const bool valid = T7DirectParse(endpoint, &address, 0) != 0;
    Lock guard;
    selected = {}; // Failed selection revokes the old destination.
    if (!valid || udp == INVALID_SOCKET || hosting) return 0;
    selected = address;
    return 1;
}
extern "C" int T7DirectPeer(T7DirectAddress *address)
{
    Lock guard;
    if (!address) return 0;
    *address = selected;
    return udp != INVALID_SOCKET && selected.type == T7_ADDR_IP && !hosting;
}
extern "C" int T7DirectSameAddress(const T7DirectAddress *a, const T7DirectAddress *b, int comparePort)
{
    return a && b && Same(*a, *b, comparePort != 0);
}
extern "C" int T7DirectSend(int length, const void *data, const T7DirectAddress *to)
{
    if (!to || length < 0 || length > MaxPayload || (length && !data)) return 0;
    Lock guard;
    if (udp == INVALID_SOCKET || !Permitted(*to)) return 0;
    unsigned char packet[MaxWire];
    packet[0] = 'T'; packet[1] = '7'; packet[2] = 'D'; packet[3] = 'P';
    packet[4] = 1; packet[5] = 0; // version and reserved flags
    packet[6] = (unsigned char)(length >> 8); packet[7] = (unsigned char)length;
    for (int i = 0; i < length; ++i) packet[HeaderSize + i] = ((const unsigned char *)data)[i];
    const unsigned short checksum = Checksum(packet + HeaderSize, length);
    packet[HeaderSize + length] = (unsigned char)(checksum >> 8);
    packet[HeaderSize + length + 1] = (unsigned char)checksum;
    sockaddr_in destination = Sockaddr(*to);
    return sendto(udp, (const char *)packet, HeaderSize + length + 2, 0,
                  (const sockaddr *)&destination, sizeof(destination)) == HeaderSize + length + 2;
}
extern "C" int T7DirectReceive(T7DirectAddress *from, T7DirectMessage *message)
{
    if (!from || !message) return 0;
    message->size = 0;
    if (!message->data || message->capacity < 1) return 0;
    Lock guard;
    if (udp == INVALID_SOCKET) return 0;
    // Bounded drain: malformed traffic cannot keep one game frame spinning forever.
    for (int count = 0; count < 64; ++count)
    {
        unsigned char packet[MaxWire + 1];
        sockaddr_in source = {};
#ifdef _WIN32
        int size = sizeof(source);
#else
        socklen_t size = sizeof(source);
#endif
        const int received = (int)recvfrom(udp, (char *)packet, sizeof(packet), 0,
                                          (sockaddr *)&source, &size);
        if (received == SOCKET_ERROR) return 0;
        if (size != sizeof(source) || source.sin_family != AF_INET || received < HeaderSize + 2 || received > MaxWire) continue;
        if (packet[0] != 'T' || packet[1] != '7' || packet[2] != 'D' || packet[3] != 'P' ||
            packet[4] != 1 || packet[5] != 0) continue;
        const int length = received - HeaderSize - 2;
        if (length != ((packet[6] << 8) | packet[7]) || length > message->capacity ||
            Checksum(packet + HeaderSize, length) != ((packet[HeaderSize + length] << 8) | packet[HeaderSize + length + 1])) continue;
        T7DirectAddress address = {};
        address.type = T7_ADDR_IP;
        address.port = source.sin_port;
        address.addrHandleIndex = 0xFFFFFFFF;
        for (int i = 0; i < 4; ++i) address.ip[i] = ((const unsigned char *)&source.sin_addr)[i];
        if (!Unicast(address.ip) || !address.port) continue;
        if (hosting)
        {
            unsigned int index = 0;
            for (; index < peerCount; ++index) if (Same(peers[index], address, true)) break;
            if (index == peerCount)
            {
                if (peerCount == MaxPeers) continue;
                peers[peerCount++] = address;
            }
        }
        else if (!Same(address, selected, true)) continue;
        *from = address;
        for (int i = 0; i < length; ++i) message->data[i] = packet[HeaderSize + i];
        message->size = length;
        return 1;
    }
    return 0;
}
