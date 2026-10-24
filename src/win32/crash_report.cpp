// The Store port's crash reporter. Original names and source path unknown.
//
// Added by the Microsoft Store port (it is not in the 2015 PC builds' lineage: no community name, no Ghosts
// counterpart found). After the minidump writer (1423F1F80) has written a dump, it calls sub_1423B9DE0 to report
// the crash: an Analytics event (sub_1423B87C0) and a .gltn report that CrashUploader.exe uploads (sub_1423B8BA0).
// docs/network.md section 3 has the whole module; records/names.tsv has the evidence for each address.

#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "universal/dvar.h"
#include "win32/crash_report.h"

#define T7_SOURCE "win32/crash_report.cpp"
#include <t7_static.h>

T7_STATIC char s_crashSignature[34] T7_AT("", "s_crashSignature");
T7_STATIC __time64_t s_lastCrashReportTime T7_AT("", "s_lastCrashReportTime");
T7_STATIC const dvar_t *s_crashReportEnable T7_AT("", "s_crashReportEnable");
T7_STATIC const dvar_t *s_crashReportUploadLog T7_AT("", "s_crashReportUploadLog");
T7_STATIC const dvar_t *s_crashReportSampleRate T7_AT("", "s_crashReportSampleRate");

// 1423B9DE0  win32/crash_report.cpp
// Reports a crash whose dump is at dumpPath, at most once every 600 seconds and only while a signature is set.
// Returns whether the report (and, if enabled, the log) was written.
bool sub_1423B9DE0(const char *dumpPath, const char *logPath, const char *platform)
{
	if (!s_crashSignature[0])
		return false;
	__time64_t now;
	_time64(&now);
	if (now - s_lastCrashReportTime < 600)
		return false;
	_time64(&s_lastCrashReportTime);
	sub_1423B87C0(platform);
	if (s_crashReportEnable && !Dvar_GetBool(s_crashReportEnable))
		return false;
	float sampleRate = s_crashReportSampleRate ? Dvar_GetFloat(s_crashReportSampleRate) : 0.05f;
	if ((float)rand() * (1.0f / 32768.0f) > sampleRate)
		return false;
	const char *slash = strrchr(dumpPath, '\\');
	char *name = _strdup(slash ? slash + 1 : dumpPath);
	char *hash = strrchr(name, '#');
	if (hash)
		strncpy(hash, "_", 1);
	if (!sub_1423B8BA0(dumpPath, name, platform))
		return false;
	if (!s_crashReportUploadLog || !Dvar_GetBool(s_crashReportUploadLog))
		return true;
	size_t len = 0;
	while (name[len])
		len++;
	strncpy(name + len - 4, ".log", 4);
	return sub_1423B8BA0(logPath, name, platform);
}
