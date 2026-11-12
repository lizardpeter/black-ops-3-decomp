#pragma once
// Independent custom packet API. NOT the game's netadr_t ABI or Xbox identity.
enum { T7_ADDR_IP = 1, T7_ADDR_LOOPBACK = 2, T7_ADDR_BOT = 3 };
struct T7DirectAddress {
    int type;
    unsigned char ip[4];
    unsigned short port; // network byte order
    unsigned int addrHandleIndex;
};
struct T7DirectMessage {
    unsigned char *data;
    int capacity;
    int size;
};

// Startup-only direct transport. These APIs never resolve DNS or vendor handles.
extern "C" int T7DirectWireVersion();
extern "C" int T7DirectOpen(const char *bindEndpoint, int server);
extern "C" void T7DirectClose();
extern "C" int T7DirectSelectPeer(const char *endpoint);
extern "C" int T7DirectPeer(T7DirectAddress *address);
extern "C" unsigned short T7DirectPort();
extern "C" int T7DirectParse(const char *text, T7DirectAddress *address, int allowZeroPort);
extern "C" int T7DirectSend(int length, const void *data, const T7DirectAddress *to);
extern "C" int T7DirectReceive(T7DirectAddress *from, T7DirectMessage *message);
extern "C" int T7DirectSameAddress(const T7DirectAddress *a, const T7DirectAddress *b, int comparePort);
