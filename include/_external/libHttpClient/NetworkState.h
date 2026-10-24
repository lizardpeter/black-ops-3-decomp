// libHttpClient's NetworkState (reconstructed: only what reconstructed code uses). libHttpClient is Microsoft's
// open-source HTTP/WebSocket layer under the Xbox services API, linked into the Store build with XAL. The names follow
// its public source; there is no symbol build, so the prototypes are this reconstruction's.
#pragma once

typedef long HRESULT;
struct HC_CALL;
typedef struct XTaskQueueObject *XTaskQueueHandle;
struct XAsyncBlock;
typedef void XAsyncCompletionRoutine(XAsyncBlock *asyncBlock);

struct XAsyncBlock
{
	XTaskQueueHandle queue;
	void *context;
	XAsyncCompletionRoutine *callback;
	unsigned char internal[sizeof(void *) * 4];
};

namespace xbox
{
namespace httpclient
{
// libHttpClient's http_internal_string: std::basic_string with its own allocator. The reconstruction is freestanding,
// so the MSVC layout (16-byte small buffer or heap pointer, size, capacity) is spelled out and moves are written as
// the inlined code does them.
struct http_internal_string
{
	union
	{
		char buffer[16];
		char *pointer;
	};
	unsigned long long size;
	unsigned long long capacity;
};

class WebSocket;

// std::shared_ptr's control block: the use and weak counts follow the vtable pointer
struct SharedCount
{
	void **vtable;
	volatile int uses;
	volatile int weaks;
};

// HC_WEBSOCKET_OBSERVER (an HCWebsocketHandle): the shared_ptr<WebSocket> it holds is at +8
struct HC_WEBSOCKET_OBSERVER
{
	void *unknown0;
	WebSocket *websocket;
	SharedCount *websocketCount;
};

class NetworkState
{
public:
	HRESULT HttpCallPerformAsync(HC_CALL *call, XAsyncBlock *async);
	HRESULT WebSocketConnectAsync(http_internal_string &&uri, http_internal_string &&subProtocol,
	                              HC_WEBSOCKET_OBSERVER *handle, XAsyncBlock *async);
};

// What WebSocketConnectAsync hands to XAsyncBegin (0xB0 bytes)
struct WebSocketConnectContext
{
	NetworkState *state;
	http_internal_string uri;
	http_internal_string subProtocol;
	HC_WEBSOCKET_OBSERVER *handle;
	WebSocket *websocket; // a shared_ptr<WebSocket> copied from the handle
	SharedCount *websocketCount;
	XAsyncBlock *clientAsyncBlock;
	XAsyncBlock internalAsyncBlock;
	unsigned char result[16];
};

// What HttpCallPerformAsync hands to XAsyncBegin (0x50 bytes)
struct HttpPerformContext
{
	NetworkState *state;
	HC_CALL *call;
	XAsyncBlock *clientAsyncBlock;
	XAsyncBlock internalAsyncBlock;
};
} // namespace httpclient
} // namespace xbox
