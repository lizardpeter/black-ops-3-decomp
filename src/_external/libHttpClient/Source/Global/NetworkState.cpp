// _external/libHttpClient/Source/Global/NetworkState.cpp
//
// libHttpClient (Microsoft, open source, linked into the Store build with XAL). Every HTTP request the Xbox services
// API makes (presence, social, session directory, title storage...) starts here: HCHttpCallPerformAsync (via HC_CALL)
// hands the call to NetworkState, which begins an XAsync operation whose provider performs it through XCurl.
// The name is the identity string it passes to XAsyncBegin. docs/network.md section 2.

#include "_external/libHttpClient/NetworkState.h"

using namespace xbox::httpclient;

// libHttpClient's allocator hooks (http_memory::mem_alloc / mem_free)
void *sub_142D680C0(unsigned long long size);
void sub_142D680E0(void *pointer);
// HttpPerformContext's completion routine and its XAsync provider
void sub_142D6E140(XAsyncBlock *asyncBlock);
HRESULT sub_142D6DF90(int op, const void *data);
// WebSocketConnectContext's completion routine, its XAsync provider, and the unique_ptr<WebSocketConnectContext>
// destructor that frees it (closing its queue, releasing the shared_ptr and both strings)
void sub_142D6E630(XAsyncBlock *asyncBlock);
HRESULT sub_142D6E520(int op, const void *data);
struct ConnectContextOwner
{
	unsigned char deleter;
	WebSocketConnectContext *context;
};
void sub_142D6DC80(ConnectContextOwner *owner);
// the public HCWebSocketConnectAsync: its address is the operation's identity
HRESULT sub_142D6B670(const char *uri, const char *subProtocol, void *handle, XAsyncBlock *async);
// std::bad_alloc's constructor and its throw info (the allocation failure path of libHttpClient's Make<T>)
void sub_142CAF370(void *exception);
extern "C" const unsigned char badAllocThrowInfo[] __asm__("_TI2?AVbad_alloc@std@@");
extern "C" __declspec(noreturn) void _CxxThrowException(void *exception, const void *throwInfo);

extern "C" HRESULT XAsyncBegin(XAsyncBlock *asyncBlock, void *context, const void *identity, const char *identityName,
                               HRESULT (*provider)(int op, const void *data));
extern "C" void XTaskQueueCloseHandle(XTaskQueueHandle queue);

// 142D6DEB0  _external/libHttpClient/Source/Global/NetworkState.cpp
HRESULT NetworkState::HttpCallPerformAsync(HC_CALL *call, XAsyncBlock *async)
{
	HttpPerformContext *context = (HttpPerformContext *)sub_142D680C0(sizeof(HttpPerformContext));
	if (!context)
	{
		unsigned char exception[32];
		sub_142CAF370(exception);
		_CxxThrowException(exception, badAllocThrowInfo);
	}
	context->state = this;
	context->call = call;
	context->clientAsyncBlock = async;
	context->internalAsyncBlock.queue = 0;
	context->internalAsyncBlock.context = context;
	context->internalAsyncBlock.callback = sub_142D6E140;
	for (int i = 0; i < (int)sizeof(context->internalAsyncBlock.internal); i++)
		context->internalAsyncBlock.internal[i] = 0;
	HRESULT hr = XAsyncBegin(async, context, 0, "xbox::httpclient::NetworkState::HttpCallPerformAsync", sub_142D6DF90);
	if (hr < 0)
	{
		if (context->internalAsyncBlock.queue)
			XTaskQueueCloseHandle(context->internalAsyncBlock.queue);
		sub_142D680E0(context);
		return hr;
	}
	return 0;
}

// Moves a string as the inlined move constructor does: the bytes are taken and the source is left empty.
static inline void moveString(http_internal_string &to, http_internal_string &from)
{
	to.size = 0;
	to.capacity = 0;
	to = from;
	from.size = 0;
	from.capacity = 15;
	from.buffer[0] = 0;
}

// 142D6E3C0  _external/libHttpClient/Source/Global/NetworkState.cpp
// Starts connecting a WebSocket (the only caller is HCWebSocketConnectAsync, 142D6B670).
HRESULT NetworkState::WebSocketConnectAsync(http_internal_string &&uri, http_internal_string &&subProtocol,
                                            HC_WEBSOCKET_OBSERVER *handle, XAsyncBlock *async)
{
	WebSocketConnectContext *context = (WebSocketConnectContext *)sub_142D680C0(sizeof(WebSocketConnectContext));
	if (!context)
	{
		unsigned char exception[32];
		sub_142CAF370(exception);
		_CxxThrowException(exception, badAllocThrowInfo);
	}
	context->state = this;
	moveString(context->uri, uri);
	moveString(context->subProtocol, subProtocol);
	context->handle = handle;
	context->websocket = 0;
	context->websocketCount = 0;
	if (handle->websocketCount)
		__atomic_add_fetch(&handle->websocketCount->uses, 1, __ATOMIC_SEQ_CST);
	context->websocket = handle->websocket;
	context->websocketCount = handle->websocketCount;
	context->clientAsyncBlock = async;
	context->internalAsyncBlock.queue = 0;
	context->internalAsyncBlock.context = context;
	context->internalAsyncBlock.callback = sub_142D6E630;
	for (int i = 0; i < (int)sizeof(context->internalAsyncBlock.internal); i++)
		context->internalAsyncBlock.internal[i] = 0;
	for (int i = 0; i < (int)sizeof(context->result); i++)
		context->result[i] = 0;
	ConnectContextOwner owner;
	owner.context = context;
	HRESULT hr = XAsyncBegin(async, context, (const void *)sub_142D6B670, 0, sub_142D6E520);
	if (hr < 0)
	{
		sub_142D6DC80(&owner);
		return hr;
	}
	return 0;
}
