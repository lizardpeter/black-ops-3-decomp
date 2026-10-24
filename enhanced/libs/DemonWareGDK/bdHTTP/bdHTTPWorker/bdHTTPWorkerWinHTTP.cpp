// P0006: Demonware's HTTP worker never opens a WinHTTP session.
//
// The worker thread (bdHTTPWorkerWinHTTPImpl::run, 142D151C0) calls initializeWinHTTP every 50 ms and takes no request
// until it returns true; every request (BeginHttpRequest, 142D12CF0) goes through the session it opens. Returning false
// is what the faithful method does while the network is not ready, so the enhanced build behaves as a machine whose
// network never comes up: no session, no request, nothing sent. It also skips the faithful "Checking if network is
// ready" log line, which would otherwise repeat every 50 ms for the whole session. docs/network.md section 1.

#include "libs/DemonWareGDK/bdHTTP/bdHTTPWorker/bdHTTPWorkerWinHTTP.h"

bool bdHTTPWorkerWinHTTPImpl::initializeWinHTTP()
{
	return false;
}
