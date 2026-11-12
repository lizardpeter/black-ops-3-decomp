// Narrow offline-only XPackage COM interface for the pinned BO3 Store build.
// BO3 requests class af406016-e850-4aa8-a88d-2f3dcb9dac7e and
// IXPackageImpl3 e2a4734b-2f4a-456d-aa8f-d065e04fb209.
// Vtable slot order follows xodus-gaming/xgameruntime-docs public research:
// IUnknown(3), IXPackageImpl(32), IXPackageImpl2(4), IXPackageImpl3(2).
//
// This is NOT an Xbox package emulator: no installation identity, entitlement,
// Store object, chunk download, mount or network implementation. Unimplemented
// methods fail; IsPackagedProcess=false, GetUserLocale="en-US" corresponding to
// the *actual* English original startup assets staged in our private Wine run.
// Diagnostic only, opt-in pending in-game compatibility validation.
#include "gdk_feature.h"
using U64 = unsigned long long;
using U32 = unsigned int;
extern "C" __declspec(dllimport) void OutputDebugStringA(const char *);
namespace {
constexpr int NoInterface = (int)0x80004002U;
constexpr int Unsupported = (int)0x80004001U;
constexpr int InvalidArg = (int)0x80070057U;
constexpr int InsufficientBuffer = (int)0x8007007AU;
const T7Guid ClassId = {0xaf406016U,0xe850,0x4aa8,{0xa8,0x8d,0x2f,0x3d,0xcb,0x9d,0xac,0x7e}};
const T7Guid IID3 = {0xe2a4734bU,0x2f4a,0x456d,{0xaa,0x8f,0x06,0x5e,0x04,0xfb,0x20,0x09}};
const T7Guid IID2 = {0xf92d8712U,0x2b27,0x4d8a,{0xbf,0x01,0x11,0xa6,0xf8,0xe3,0xeb,0x42}};
const T7Guid IID1 = {0x3720de07U,0xe8e4,0x44a3,{0xad,0x32,0xb3,0x59,0xe8,0xad,0xbe,0x55}};
const T7Guid IUnknown = {0,0,0,{0xc0,0,0,0,0,0,0,0x46}};
bool Same(const T7Guid *a, const T7Guid &b)
{
    if (!a || a->a!=b.a || a->b!=b.b || a->c!=b.c) return false;
    for(unsigned i=0;i<8;++i) if(a->d[i]!=b.d[i]) return false;
    return true;
}
struct Package;
using Generic = int (*)(Package*, ...);
struct Vtable {
    int (*QueryInterface)(Package*,const T7Guid*,void**);
    U32 (*AddRef)(Package*);
    U32 (*Release)(Package*);
    Generic getIdentifier;      // slot 3
    bool (*isPackaged)(Package*);// slot 4
    Generic beforeLocale[6];    // slots 5..10
    int (*getLocale)(Package*,U64,char*); // slot 11
    Generic afterLocale[29];    // slots 12..40
};
static_assert(sizeof(Vtable)==41*8,"Unexpected XPackageImpl3 vtable layout");
struct Package {const Vtable *vtable;};
volatile U32 refs = 1;
volatile U32 diagnostics = 0;
void Emit(unsigned int slot)
{
    if (__sync_fetch_and_add(&diagnostics,1U)>=96) return;
    char line[]="T7GDK:PACKAGE_METHOD_SLOT=00";
    line[sizeof("T7GDK:PACKAGE_METHOD_SLOT=")-1]=(char)('0'+(slot/10));
    line[sizeof("T7GDK:PACKAGE_METHOD_SLOT=")]=(char)('0'+(slot%10));
    OutputDebugStringA(line);
}
template<unsigned int slot>
int Fail(Package*,...)
{
    Emit(slot);
    return Unsupported;
}
U32 AddRef(Package*) {return __sync_add_and_fetch(&refs,1U);}
U32 Release(Package*)
{
    U32 old;
    do {old=__sync_fetch_and_add(&refs,0U);if(old<=1) return 1;}
    while(!__sync_bool_compare_and_swap(&refs,old,old-1));
    return old-1;
}
bool IsPackaged(Package*)
{
    Emit(4);
    return false;
}
int Locale(Package*,U64 length,char *out)
{
    Emit(11);
    if(!out) return InvalidArg;
    if(length<6) return InsufficientBuffer;
    const char locale[]="en-US";
    for(unsigned i=0;i<sizeof(locale);++i) out[i]=locale[i];
    return 0;
}
int QueryInterface(Package *self,const T7Guid *iid,void **out)
{
    if(!out) return InvalidArg;
    *out=nullptr;
    if(!Same(iid,IUnknown) && !Same(iid,IID1) && !Same(iid,IID2) && !Same(iid,IID3))
        return NoInterface;
    AddRef(self);
    *out=self;
    return 0;
}
const Vtable table = {
    QueryInterface,AddRef,Release,
    Fail<3>,IsPackaged,
    {Fail<5>,Fail<6>,Fail<7>,Fail<8>,Fail<9>,Fail<10>},
    Locale,
    {Fail<12>,Fail<13>,Fail<14>,Fail<15>,Fail<16>,Fail<17>,Fail<18>,Fail<19>,
     Fail<20>,Fail<21>,Fail<22>,Fail<23>,Fail<24>,Fail<25>,Fail<26>,Fail<27>,
     Fail<28>,Fail<29>,Fail<30>,Fail<31>,Fail<32>,Fail<33>,Fail<34>,Fail<35>,
     Fail<36>,Fail<37>,Fail<38>,Fail<39>,Fail<40>}
};
Package singleton={&table};
}
extern "C" int T7OfflinePackageQuery(const T7Guid *classId,const T7Guid *iid,void **out)
{
    if(!out) return InvalidArg;
    *out=nullptr;
    if(!Same(classId,ClassId)) return Unsupported;
    return QueryInterface(&singleton,iid,out);
}
