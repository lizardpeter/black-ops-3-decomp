#pragma once
// Minimal GUID layout used only by the independent, offline GDK compatibility DLL.
struct T7Guid
{
    unsigned int a;
    unsigned short b, c;
    unsigned char d[8];
};
static_assert(sizeof(T7Guid) == 16, "GUID layout");
extern "C" int T7OfflineFeatureQuery(const T7Guid *, const T7Guid *, void **);
