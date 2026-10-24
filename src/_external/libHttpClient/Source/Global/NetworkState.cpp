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
