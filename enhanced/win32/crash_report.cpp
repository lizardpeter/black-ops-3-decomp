// P0003: the Store port's crash reporter never reports.
//
// sub_1423B9DE0 is the reporter's only entry (its sole caller is the minidump writer, 1423F1F80) and the only caller
// of both senders: sub_1423B87C0 (Google Analytics event, with the machine GUID from
// HKLM\SOFTWARE\Activision\HardwareSurvey) and sub_1423B8BA0 (crash_reports/*.gltn with the machine GUID and volume
// id, then `start CrashUploader.exe`). Replacing it here cuts all of that; the minidump itself is still written
// locally by the original writer. Nothing is read, written or called: the signature, the rate limit and the dvars
// are left as they are. docs/network.md section 3; records/bugs.tsv B0006.

#include "win32/crash_report.h"

bool sub_1423B9DE0(const char *dumpPath, const char *logPath, const char *platform)
{
	return false;
}
