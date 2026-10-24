// Offline package DLL entry (P0001). Linked only into the offline recon.dll (tools/offline/build_dll.py).
// Refuses to stay loaded in a host that is not a prepared package: the Store exe at its fixed base, this DLL at
// 0x180000000, and the package section .t7off with its marker. A format check, not an integrity boundary.
// Ported from ghosts-decomp enhanced/offline/bootstrap.cpp.
extern "C" __declspec(dllimport) void *GetModuleHandleW(const wchar_t *);
extern "C" __declspec(dllimport) void *GetCurrentProcess();
extern "C" __declspec(dllimport) int TerminateProcess(void *, unsigned int);

namespace
{
const unsigned int kOriginalSizeOfImage = 0x1A53F000; // BlackOps3_MSStore: the package section is placed after it
const unsigned long long kSectionName = 0x0066666F37742EULL; // ".t7off\0\0"
const unsigned long long kMarker0 = 0x494C46464F3754ULL | (0x4EULL << 56); // "T7OFFLIN"
const unsigned long long kMarker1 = 0x0000000100003145ULL;                 // "E1\0\0\1\0\0\0"
}

extern "C" __declspec(dllexport) int T7OfflineDllMain(void *module, unsigned int reason, void *)
{
    if (reason != 1) return 1;
    unsigned char *image = (unsigned char *)GetModuleHandleW(nullptr);
    bool valid = (unsigned long long)image == 0x140000000ULL && (unsigned long long)module == 0x180000000ULL;
    if (valid)
    {
        valid = *(unsigned short *)image == 0x5A4D;
        const unsigned int nt = *(unsigned int *)(image + 0x3C);
        valid = valid && nt < 0x400 && *(unsigned int *)(image + nt) == 0x4550;
        if (valid)
        {
            const unsigned int count = *(unsigned short *)(image + nt + 6);
            const unsigned int optional = *(unsigned short *)(image + nt + 20);
            const unsigned int sizeOfImage = *(unsigned int *)(image + nt + 24 + 56);
            const unsigned char *section = image + nt + 24 + optional;
            valid = false;
            if (count <= 32 && optional == 240)
                for (unsigned int i = 0; i < count; ++i, section += 40)
                    if (*(unsigned long long *)section == kSectionName)
                    {
                        const unsigned int rva = *(unsigned int *)(section + 12);
                        if (rva >= kOriginalSizeOfImage && rva + 16 <= sizeOfImage)
                        {
                            const unsigned char *mark = image + rva;
                            valid = *(unsigned long long *)mark == kMarker0 &&
                                    *(unsigned long long *)(mark + 8) == kMarker1;
                        }
                    }
        }
    }
    if (!valid) { TerminateProcess(GetCurrentProcess(), 0xE0010001); return 0; }
    return 1;
}

// Imported by the package's own import descriptor so the DLL is always loaded at startup.
extern "C" __declspec(dllexport) int T7OfflineBootstrap() { return 1; }
