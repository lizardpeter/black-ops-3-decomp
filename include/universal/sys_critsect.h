// universal/sys_critsect.h (reconstructed: only what reconstructed code uses so far)
//
// The engine's critical sections: a fixed table of CRITICAL_SECTIONs, entered recursively per thread (a count per
// section in thread-local storage), and a scoped lock object chained through thread-local storage so a thread can
// release every lock it holds. Names from the Steam build's community symbols (Sys_EnterCriticalSection,
// Sys_LeaveCriticalSection); the scoped lock's are descriptive.
#pragma once

enum CriticalSection
{
	CRITSECT_D3D_CONTEXT = 0x34,  // taken around every use of the immediate context and the swap chain
};

enum ScopedCriticalSectionType
{
	SCOPED_CRITSECT_NORMAL = 0,
	SCOPED_CRITSECT_RELEASE = 2,
	SCOPED_CRITSECT_TRY = 3,
};

struct ScopedCriticalSection
{
	int s;
	bool isScopedLock;
	bool isScopedRelease;
	ScopedCriticalSection *next;
};

void Sys_EnterCriticalSection(int critSect);
void Sys_LeaveCriticalSection(int critSect);
// The scoped lock's constructor (140163BB0) and destructor (140163C70). The original constructs it inline at every
// use, with the same effect as a call to the out-of-line copy: the reconstruction calls that copy.
ScopedCriticalSection *ScopedCriticalSection_Construct(ScopedCriticalSection *lock, int critSect,
                                                       ScopedCriticalSectionType type);
void ScopedCriticalSection_Destruct(ScopedCriticalSection *lock);
