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
class NetworkState
{
public:
	HRESULT HttpCallPerformAsync(HC_CALL *call, XAsyncBlock *async);
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
