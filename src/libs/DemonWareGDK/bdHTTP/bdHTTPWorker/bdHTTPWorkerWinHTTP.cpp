// libs/DemonWareGDK/bdHTTP/bdHTTPWorker/bdHTTPWorkerWinHTTP.cpp
//
// Demonware's HTTP worker on WinHTTP: every Demonware HTTPS request (auth, Umbrella, UNO, content streaming) goes
// through the session this file opens. The source path and the names are the library's own strings. Original line
// numbers are unknown; the line numbers passed to bdLogMessage are the original's.

#include <winhttp.h>

#include "libs/DemonWareGDK/bdCore/bdLogMessage.h"
#include "libs/DemonWareGDK/bdHTTP/bdHTTPWorker/bdHTTPWorkerWinHTTP.h"

#define T7_SOURCE "libs/DemonWareGDK/bdHTTP/bdHTTPWorker/bdHTTPWorkerWinHTTP.cpp"
#include <t7_static.h>

#define BD_HTTP_WORKER_FILE "C:\\trees\\outrun\\outrun\\t7\\code\\libs\\DemonWareGDK\\bdHTTP\\bdHTTPWorker\\bdHTTPWorkerWinHTTP.cpp"
#define bdLogWorker(type, channel, line, ...)                                                                        \
	bdLogMessage(type, channel, "bdHTTPWorker(WinHTTP)", BD_HTTP_WORKER_FILE, "bdHTTPWorkerWinHTTPImpl::initializeWinHTTP", \
	             line, __VA_ARGS__)

// Set once the platform reports the network usable (written elsewhere, by the XNetworking connectivity handling).
T7_STATIC bool s_networkReady T7_AT("", "s_networkReady");

extern "C" bool XGameRuntimeIsFeatureAvailable(unsigned int feature);

// HRESULT_FROM_WIN32
static inline long bdHresultFromWin32(DWORD error)
{
	return (int)error <= 0 ? (long)error : (long)((error & 0xFFFF) | 0x80070000);
}

// 142D14BA0  libs/DemonWareGDK/bdHTTP/bdHTTPWorker/bdHTTPWorkerWinHTTP.cpp
// Opens the worker's WinHTTP session once the network is ready. The worker thread (142D151C0) calls it every 50 ms
// until it returns true, and only then takes requests.
bool bdHTTPWorkerWinHTTPImpl::initializeWinHTTP()
{
	bdLogWorker(BD_LOG_INFO, "info/", 188, "bdHTTPWorker(WinHTTP): Checking if network is ready");
	if (!m_initialized && s_networkReady)
	{
		bdLogWorker(BD_LOG_INFO, "info/", 192, "bdHTTPWorker(WinHTTP): Initializing worker");
		// 10: XGameRuntimeFeature for XNetworking (the secure-defaults flag only where it is available)
		DWORD flags = XGameRuntimeIsFeatureAvailable(10) * 0x20000000 + WINHTTP_FLAG_ASYNC;
		m_session = WinHttpOpen(L"DW-HTTP-USER-AGENT WinHTTP (Windows - GDK)", WINHTTP_ACCESS_TYPE_AUTOMATIC_PROXY,
		                        NULL, NULL, flags);
		if (!m_session)
		{
			bdLogWorker(BD_LOG_ERROR, "err/", 225, "bdHTTPWorker(WinHTTP): WinHttpOpen() failed with Error[%08X]",
			            bdHresultFromWin32(GetLastError()));
			return false;
		}
		bdLogWorker(BD_LOG_INFO, "info/", 230, "bdHTTPWorker(WinHTTP): WinHttpOpen() created Session[%p]", m_session);
		DWORD protocols = WINHTTP_FLAG_SECURE_PROTOCOL_TLS1_2 | WINHTTP_FLAG_SECURE_PROTOCOL_TLS1_3;
		WinHttpSetOption(m_session, WINHTTP_OPTION_SECURE_PROTOCOLS, &protocols, sizeof(protocols));
		WINHTTP_STATUS_CALLBACK previous = WinHttpSetStatusCallback(
			m_session, WinHttpStatusCallback, WINHTTP_CALLBACK_FLAG_ALL_NOTIFICATIONS, 0);
		if (previous == WINHTTP_INVALID_STATUS_CALLBACK)
		{
			bdLogWorker(BD_LOG_ERROR, "err/", 251,
			            "bdHTTPWorker(WinHTTP): WinHttpSetStatusCallback() failed with Error[%08X]",
			            bdHresultFromWin32(GetLastError()));
			WinHttpCloseHandle(m_session);
			m_session = NULL;
			return false;
		}
		if (previous)
			bdLogWorker(BD_LOG_WARNING, "warn/", 258,
			            "bdHTTPWorker(WinHTTP): WinHttpSetStatusCallback() found existing callback[%p]", previous);
		m_initialized = true;
		bdLogWorker(BD_LOG_INFO, "info/", 262, "bdHTTPWorker(WinHTTP): Initialized worker");
	}
	return m_initialized;
}
