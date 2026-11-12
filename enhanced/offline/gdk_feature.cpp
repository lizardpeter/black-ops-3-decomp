// One narrowly scoped, offline-safe GDK COM interface:
// XGameRuntimeIsFeatureAvailable always reports false. It cannot authenticate,
// grant entitlement, create Xbox users, or initialize online/async services.
// This is an independent implementation of the documented COM ABI, not
// copied from any upstream Wine/LGPL source. Enabled only in an explicit
// isolated diagnostic run pending BO3 native verification.
#include "gdk_feature.h"
namespace {
constexpr int NoInterface = (int)0x80004002U;
constexpr int Unsupported = (int)0x80070032U;
const T7Guid FeatureId = {0x8836fe87U, 0xedb9, 0x4fe3,
                          {0x8d, 0xad, 0x05, 0xf0, 0xd2, 0xcd, 0x5b, 0x40}};
const T7Guid UnknownId = {0, 0, 0,
                          {0xc0, 0, 0, 0, 0, 0, 0, 0x46}};
bool Same(const T7Guid *left, const T7Guid &right)
{
    if (!left || left->a != right.a || left->b != right.b || left->c != right.c)
        return false;
    for (unsigned i = 0; i < 8; ++i)
        if (left->d[i] != right.d[i]) return false;
    return true;
}
struct FeatureObject;
struct FeatureVtable
{
    int (*QueryInterface)(FeatureObject *, const T7Guid *, void **);
    unsigned int (*AddRef)(FeatureObject *);
    unsigned int (*Release)(FeatureObject *);
    bool (*IsAvailable)(FeatureObject *, unsigned int);
};
struct FeatureObject { const FeatureVtable *vtable; };
volatile unsigned int references = 1;
unsigned int AddRef(FeatureObject *)
{
    return __sync_add_and_fetch(&references, 1U);
}
unsigned int Release(FeatureObject *)
{
    unsigned int before;
    do {
        before = __sync_fetch_and_add(&references, 0U);
        if (before <= 1U) return 1U; // eternal process-local singleton
    } while (!__sync_bool_compare_and_swap(&references, before, before - 1U));
    return before - 1U;
}
bool IsAvailable(FeatureObject *, unsigned int)
{
    return false; // never report absent Microsoft GDK services available
}
int QueryInterface(FeatureObject *self, const T7Guid *iid, void **out)
{
    if (!out) return NoInterface;
    *out = nullptr;
    if (!Same(iid, FeatureId) && !Same(iid, UnknownId))
        return NoInterface;
    AddRef(self);
    *out = self;
    return 0;
}
const FeatureVtable vtable = {QueryInterface, AddRef, Release, IsAvailable};
FeatureObject singleton = {&vtable};
}
extern "C" int T7OfflineFeatureQuery(const T7Guid *classId, const T7Guid *iid, void **out)
{
    if (!out) return NoInterface;
    *out = nullptr;
    if (!Same(classId, FeatureId)) return Unsupported;
    return QueryInterface(&singleton, iid, out);
}
