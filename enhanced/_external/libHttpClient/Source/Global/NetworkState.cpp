// P0007: the Xbox services API's HTTP requests and WebSocket connections are never made.
//
// Every HTTP request libHttpClient makes (for the Xbox services API: presence, social, session directory, title
// storage...) begins here, before any XAsync operation or XCurl handle exists. The enhanced build refuses it at once
// with HRESULT_FROM_WIN32(ERROR_NETWORK_UNREACHABLE), the failure a machine without a network would give, without
// allocating or starting anything; HCHttpCallPerformAsync returns that to its caller. WebSocket connections (the Xbox
// Live real-time activity socket, wss://rta.xboxlive.com/connect) all begin in WebSocketConnectAsync and are refused
// the same way; the strings stay with the caller, which destroys them. docs/network.md section 2.

#include "_external/libHttpClient/NetworkState.h"

using namespace xbox::httpclient;

HRESULT NetworkState::HttpCallPerformAsync(HC_CALL *call, XAsyncBlock *async)
{
	return (HRESULT)0x800704CF; // HRESULT_FROM_WIN32(ERROR_NETWORK_UNREACHABLE)
}

HRESULT NetworkState::WebSocketConnectAsync(http_internal_string &&uri, http_internal_string &&subProtocol,
                                            HC_WEBSOCKET_OBSERVER *handle, XAsyncBlock *async)
{
	return (HRESULT)0x800704CF; // HRESULT_FROM_WIN32(ERROR_NETWORK_UNREACHABLE)
}
