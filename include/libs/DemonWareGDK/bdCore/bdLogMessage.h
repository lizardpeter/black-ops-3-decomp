// Demonware logging (reconstructed: only what reconstructed code uses so far). Names and the prototype are from
// Ghosts' Xbox One server PDB (lizardpeter/ghosts-decomp, iw6_ds_xb3), whose Demonware is the same generation.
#pragma once

enum bdLogMessageType
{
	BD_LOG_INFO = 0,
	BD_LOG_WARNING = 1,
	BD_LOG_ERROR = 2,
};

// 1429C3A20
void bdLogMessage(const bdLogMessageType type, const char *const baseChannel, const char *const channel,
                  const char *const file, const char *const function, const unsigned int line,
                  const char *const format, ...);
