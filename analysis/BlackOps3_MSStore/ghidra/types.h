typedef unsigned char   undefined;

typedef unsigned char    bool;
typedef unsigned char    byte;
typedef unsigned int    dword;
typedef unsigned long long    GUID;
typedef pointer32 ImageBaseOffset32;

typedef long long    longlong;
typedef unsigned long long    qword;
typedef unsigned char    uchar;
typedef unsigned int    uint;
typedef unsigned long    ulong;
typedef unsigned long long    ulonglong;
typedef unsigned char    undefined1;
typedef unsigned short    undefined2;
typedef unsigned int    undefined4;
typedef unsigned long long    undefined5;
typedef unsigned long long    undefined8;
typedef unsigned short    ushort;
typedef unsigned short    wchar16;
typedef short    wchar_t;
typedef unsigned short    word;
typedef struct _s__RTTIBaseClassDescriptor _s__RTTIBaseClassDescriptor, *P_s__RTTIBaseClassDescriptor;

typedef struct _s__RTTIBaseClassDescriptor RTTIBaseClassDescriptor;

typedef RTTIBaseClassDescriptor *RTTIBaseClassDescriptor *32 __((image-base-relative));

typedef RTTIBaseClassDescriptor *32 __((image-base-relative)) *RTTIBaseClassDescriptor *32 __((image-base-relative)) *32 __((image-base-relative));

typedef struct PMD PMD, *PPMD;

struct PMD {
    int mdisp;
    int pdisp;
    int vdisp;
};

struct _s__RTTIBaseClassDescriptor {
    ImageBaseOffset32 pTypeDescriptor; /* ref to TypeDescriptor (RTTI 0) for class */
    dword numContainedBases; /* count of extended classes in BaseClassArray (RTTI 2) */
    struct PMD where; /* member displacement structure */
    dword attributes; /* bit flags */
    ImageBaseOffset32 pClassHierarchyDescriptor; /* ref to ClassHierarchyDescriptor (RTTI 3) for class */
};

typedef struct _com_error _com_error, *P_com_error;

struct _com_error { /* PlaceHolder Class Structure */
};

typedef union IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryUnion IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryUnion, *PIMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryUnion;

typedef struct IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryStruct IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryStruct, *PIMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryStruct;

struct IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryStruct {
    dword OffsetToDirectory:31;
    dword DataIsDirectory:1;
};

union IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryUnion {
    dword OffsetToData;
    struct IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryStruct IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryStruct;
};

typedef struct CLIENT_ID CLIENT_ID, *PCLIENT_ID;

struct CLIENT_ID {
    void *UniqueProcess;
    void *UniqueThread;
};

typedef struct _s__RTTIClassHierarchyDescriptor _s__RTTIClassHierarchyDescriptor, *P_s__RTTIClassHierarchyDescriptor;

typedef struct _s__RTTIClassHierarchyDescriptor RTTIClassHierarchyDescriptor;

struct _s__RTTIClassHierarchyDescriptor {
    dword signature;
    dword attributes; /* bit flags */
    dword numBaseClasses; /* number of base classes (i.e. rtti1Count) */
    RTTIBaseClassDescriptor *32 __((image-base-relative)) *32 __((image-base-relative)) pBaseClassArray; /* ref to BaseClassArray (RTTI 2) */
};

typedef ulonglong __uint64;

typedef struct _s__RTTICompleteObjectLocator _s__RTTICompleteObjectLocator, *P_s__RTTICompleteObjectLocator;

typedef struct _s__RTTICompleteObjectLocator RTTICompleteObjectLocator;

struct _s__RTTICompleteObjectLocator {
    dword signature;
    dword offset; /* offset of vbtable within class */
    dword cdOffset; /* constructor displacement offset */
    ImageBaseOffset32 pTypeDescriptor; /* ref to TypeDescriptor (RTTI 0) for class */
    ImageBaseOffset32 pClassDescriptor; /* ref to ClassHierarchyDescriptor (RTTI 3) */
};

typedef struct _s_FuncInfo _s_FuncInfo, *P_s_FuncInfo;

typedef int __ehstate_t;

struct _s_FuncInfo {
    uint magicNumber_and_bbtFlags;
    __ehstate_t maxState;
    ImageBaseOffset32 dispUnwindMap;
    uint nTryBlocks;
    ImageBaseOffset32 dispTryBlockMap;
    uint nIPMapEntries;
    ImageBaseOffset32 dispIPToStateMap;
    int dispUnwindHelp;
    ImageBaseOffset32 dispESTypeList;
    int EHFlags;
};

typedef struct _s_IPToStateMapEntry _s_IPToStateMapEntry, *P_s_IPToStateMapEntry;

struct _s_IPToStateMapEntry {
    ImageBaseOffset32 Ip;
    __ehstate_t state;
};

typedef struct _s_IPToStateMapEntry IPToStateMapEntry;

typedef struct _s_FuncInfo FuncInfo;

typedef struct _MEMORYSTATUSEX _MEMORYSTATUSEX, *P_MEMORYSTATUSEX;

typedef ulong DWORD;

typedef ulonglong ULONGLONG;

typedef ULONGLONG DWORDLONG;

struct _MEMORYSTATUSEX {
    DWORD dwLength;
    DWORD dwMemoryLoad;
    DWORDLONG ullTotalPhys;
    DWORDLONG ullAvailPhys;
    DWORDLONG ullTotalPageFile;
    DWORDLONG ullAvailPageFile;
    DWORDLONG ullTotalVirtual;
    DWORDLONG ullAvailVirtual;
    DWORDLONG ullAvailExtendedVirtual;
};

typedef struct _SYSTEM_INFO _SYSTEM_INFO, *P_SYSTEM_INFO;

typedef struct _SYSTEM_INFO *LPSYSTEM_INFO;

typedef union _union_552 _union_552, *P_union_552;

typedef void *LPVOID;

typedef ulonglong ULONG_PTR;

typedef ULONG_PTR DWORD_PTR;

typedef ushort WORD;

typedef struct _struct_553 _struct_553, *P_struct_553;

struct _struct_553 {
    WORD wProcessorArchitecture;
    WORD wReserved;
};

union _union_552 {
    DWORD dwOemId;
    struct _struct_553 s;
};

struct _SYSTEM_INFO {
    union _union_552 u;
    DWORD dwPageSize;
    LPVOID lpMinimumApplicationAddress;
    LPVOID lpMaximumApplicationAddress;
    DWORD_PTR dwActiveProcessorMask;
    DWORD dwNumberOfProcessors;
    DWORD dwProcessorType;
    DWORD dwAllocationGranularity;
    WORD wProcessorLevel;
    WORD wProcessorRevision;
};

typedef struct _OVERLAPPED _OVERLAPPED, *P_OVERLAPPED;

typedef union _union_540 _union_540, *P_union_540;

typedef void *HANDLE;

typedef struct _struct_541 _struct_541, *P_struct_541;

typedef void *PVOID;

struct _struct_541 {
    DWORD Offset;
    DWORD OffsetHigh;
};

union _union_540 {
    struct _struct_541 s;
    PVOID Pointer;
};

struct _OVERLAPPED {
    ULONG_PTR Internal;
    ULONG_PTR InternalHigh;
    union _union_540 u;
    HANDLE hEvent;
};

typedef struct _SECURITY_ATTRIBUTES _SECURITY_ATTRIBUTES, *P_SECURITY_ATTRIBUTES;

typedef int BOOL;

struct _SECURITY_ATTRIBUTES {
    DWORD nLength;
    LPVOID lpSecurityDescriptor;
    BOOL bInheritHandle;
};

typedef struct _SYSTEMTIME _SYSTEMTIME, *P_SYSTEMTIME;

typedef struct _SYSTEMTIME SYSTEMTIME;

struct _SYSTEMTIME {
    WORD wYear;
    WORD wMonth;
    WORD wDayOfWeek;
    WORD wDay;
    WORD wHour;
    WORD wMinute;
    WORD wSecond;
    WORD wMilliseconds;
};

typedef struct _STARTUPINFOW _STARTUPINFOW, *P_STARTUPINFOW;

typedef wchar_t WCHAR;

typedef WCHAR *LPWSTR;

typedef uchar BYTE;

typedef BYTE *LPBYTE;

struct _STARTUPINFOW {
    DWORD cb;
    LPWSTR lpReserved;
    LPWSTR lpDesktop;
    LPWSTR lpTitle;
    DWORD dwX;
    DWORD dwY;
    DWORD dwXSize;
    DWORD dwYSize;
    DWORD dwXCountChars;
    DWORD dwYCountChars;
    DWORD dwFillAttribute;
    DWORD dwFlags;
    WORD wShowWindow;
    WORD cbReserved2;
    LPBYTE lpReserved2;
    HANDLE hStdInput;
    HANDLE hStdOutput;
    HANDLE hStdError;
};

typedef struct _STARTUPINFOW *LPSTARTUPINFOW;

typedef struct _WIN32_FIND_DATAA _WIN32_FIND_DATAA, *P_WIN32_FIND_DATAA;

typedef struct _FILETIME _FILETIME, *P_FILETIME;

typedef struct _FILETIME FILETIME;

typedef char CHAR;

struct _FILETIME {
    DWORD dwLowDateTime;
    DWORD dwHighDateTime;
};

struct _WIN32_FIND_DATAA {
    DWORD dwFileAttributes;
    FILETIME ftCreationTime;
    FILETIME ftLastAccessTime;
    FILETIME ftLastWriteTime;
    DWORD nFileSizeHigh;
    DWORD nFileSizeLow;
    DWORD dwReserved0;
    DWORD dwReserved1;
    CHAR cFileName[260];
    CHAR cAlternateFileName[14];
};

typedef struct _WIN32_FIND_DATAW _WIN32_FIND_DATAW, *P_WIN32_FIND_DATAW;

typedef struct _WIN32_FIND_DATAW *LPWIN32_FIND_DATAW;

struct _WIN32_FIND_DATAW {
    DWORD dwFileAttributes;
    FILETIME ftCreationTime;
    FILETIME ftLastAccessTime;
    FILETIME ftLastWriteTime;
    DWORD nFileSizeHigh;
    DWORD nFileSizeLow;
    DWORD dwReserved0;
    DWORD dwReserved1;
    WCHAR cFileName[260];
    WCHAR cAlternateFileName[14];
};

typedef enum _COMPUTER_NAME_FORMAT {
    ComputerNameNetBIOS=0,
    ComputerNameDnsHostname=1,
    ComputerNameDnsDomain=2,
    ComputerNameDnsFullyQualified=3,
    ComputerNamePhysicalNetBIOS=4,
    ComputerNamePhysicalDnsHostname=5,
    ComputerNamePhysicalDnsDomain=6,
    ComputerNamePhysicalDnsFullyQualified=7,
    ComputerNameMax=8
} _COMPUTER_NAME_FORMAT;

typedef struct _OVERLAPPED *LPOVERLAPPED;

typedef DWORD (*PTHREAD_START_ROUTINE)(LPVOID);

typedef PTHREAD_START_ROUTINE LPTHREAD_START_ROUTINE;

typedef struct _MEMORYSTATUSEX *LPMEMORYSTATUSEX;

typedef struct _SECURITY_ATTRIBUTES *LPSECURITY_ATTRIBUTES;

typedef struct _PROCESS_INFORMATION _PROCESS_INFORMATION, *P_PROCESS_INFORMATION;

struct _PROCESS_INFORMATION {
    HANDLE hProcess;
    HANDLE hThread;
    DWORD dwProcessId;
    DWORD dwThreadId;
};

typedef struct _STARTUPINFOA _STARTUPINFOA, *P_STARTUPINFOA;

typedef CHAR *LPSTR;

struct _STARTUPINFOA {
    DWORD cb;
    LPSTR lpReserved;
    LPSTR lpDesktop;
    LPSTR lpTitle;
    DWORD dwX;
    DWORD dwY;
    DWORD dwXSize;
    DWORD dwYSize;
    DWORD dwXCountChars;
    DWORD dwYCountChars;
    DWORD dwFillAttribute;
    DWORD dwFlags;
    WORD wShowWindow;
    WORD cbReserved2;
    LPBYTE lpReserved2;
    HANDLE hStdInput;
    HANDLE hStdOutput;
    HANDLE hStdError;
};

typedef struct _WIN32_FIND_DATAA *LPWIN32_FIND_DATAA;

typedef struct _STARTUPINFOA *LPSTARTUPINFOA;

typedef struct _RTL_CONDITION_VARIABLE _RTL_CONDITION_VARIABLE, *P_RTL_CONDITION_VARIABLE;

typedef struct _RTL_CONDITION_VARIABLE RTL_CONDITION_VARIABLE;

typedef RTL_CONDITION_VARIABLE *PCONDITION_VARIABLE;

struct _RTL_CONDITION_VARIABLE {
    PVOID Ptr;
};

typedef struct _RTL_SRWLOCK _RTL_SRWLOCK, *P_RTL_SRWLOCK;

typedef struct _RTL_SRWLOCK RTL_SRWLOCK;

typedef RTL_SRWLOCK *PSRWLOCK;

struct _RTL_SRWLOCK {
    PVOID Ptr;
};

typedef struct _PROCESS_INFORMATION *LPPROCESS_INFORMATION;

typedef struct _RTL_CRITICAL_SECTION _RTL_CRITICAL_SECTION, *P_RTL_CRITICAL_SECTION;

typedef struct _RTL_CRITICAL_SECTION *PRTL_CRITICAL_SECTION;

typedef PRTL_CRITICAL_SECTION LPCRITICAL_SECTION;

typedef struct _RTL_CRITICAL_SECTION_DEBUG _RTL_CRITICAL_SECTION_DEBUG, *P_RTL_CRITICAL_SECTION_DEBUG;

typedef struct _RTL_CRITICAL_SECTION_DEBUG *PRTL_CRITICAL_SECTION_DEBUG;

typedef long LONG;

typedef struct _LIST_ENTRY _LIST_ENTRY, *P_LIST_ENTRY;

typedef struct _LIST_ENTRY LIST_ENTRY;

struct _RTL_CRITICAL_SECTION {
    PRTL_CRITICAL_SECTION_DEBUG DebugInfo;
    LONG LockCount;
    LONG RecursionCount;
    HANDLE OwningThread;
    HANDLE LockSemaphore;
    ULONG_PTR SpinCount;
};

struct _LIST_ENTRY {
    struct _LIST_ENTRY *Flink;
    struct _LIST_ENTRY *Blink;
};

struct _RTL_CRITICAL_SECTION_DEBUG {
    WORD Type;
    WORD CreatorBackTraceIndex;
    struct _RTL_CRITICAL_SECTION *CriticalSection;
    LIST_ENTRY ProcessLocksList;
    DWORD EntryCount;
    DWORD ContentionCount;
    DWORD Flags;
    WORD CreatorBackTraceIndexHigh;
    WORD SpareWORD;
};

typedef enum _COMPUTER_NAME_FORMAT COMPUTER_NAME_FORMAT;

typedef struct _EXCEPTION_POINTERS _EXCEPTION_POINTERS, *P_EXCEPTION_POINTERS;

typedef LONG (*PTOP_LEVEL_EXCEPTION_FILTER)(struct _EXCEPTION_POINTERS *);

typedef struct _EXCEPTION_RECORD _EXCEPTION_RECORD, *P_EXCEPTION_RECORD;

typedef struct _EXCEPTION_RECORD EXCEPTION_RECORD;

typedef EXCEPTION_RECORD *PEXCEPTION_RECORD;

typedef struct _CONTEXT _CONTEXT, *P_CONTEXT;

typedef struct _CONTEXT *PCONTEXT;

typedef ulonglong DWORD64;

typedef union _union_54 _union_54, *P_union_54;

typedef struct _M128A _M128A, *P_M128A;

typedef struct _M128A M128A;

typedef struct _XSAVE_FORMAT _XSAVE_FORMAT, *P_XSAVE_FORMAT;

typedef struct _XSAVE_FORMAT XSAVE_FORMAT;

typedef XSAVE_FORMAT XMM_SAVE_AREA32;

typedef struct _struct_55 _struct_55, *P_struct_55;

typedef longlong LONGLONG;

struct _M128A {
    ULONGLONG Low;
    LONGLONG High;
};

struct _XSAVE_FORMAT {
    WORD ControlWord;
    WORD StatusWord;
    BYTE TagWord;
    BYTE Reserved1;
    WORD ErrorOpcode;
    DWORD ErrorOffset;
    WORD ErrorSelector;
    WORD Reserved2;
    DWORD DataOffset;
    WORD DataSelector;
    WORD Reserved3;
    DWORD MxCsr;
    DWORD MxCsr_Mask;
    M128A FloatRegisters[8];
    M128A XmmRegisters[16];
    BYTE Reserved4[96];
};

struct _struct_55 {
    M128A Header[2];
    M128A Legacy[8];
    M128A Xmm0;
    M128A Xmm1;
    M128A Xmm2;
    M128A Xmm3;
    M128A Xmm4;
    M128A Xmm5;
    M128A Xmm6;
    M128A Xmm7;
    M128A Xmm8;
    M128A Xmm9;
    M128A Xmm10;
    M128A Xmm11;
    M128A Xmm12;
    M128A Xmm13;
    M128A Xmm14;
    M128A Xmm15;
};

union _union_54 {
    XMM_SAVE_AREA32 FltSave;
    struct _struct_55 s;
};

struct _CONTEXT {
    DWORD64 P1Home;
    DWORD64 P2Home;
    DWORD64 P3Home;
    DWORD64 P4Home;
    DWORD64 P5Home;
    DWORD64 P6Home;
    DWORD ContextFlags;
    DWORD MxCsr;
    WORD SegCs;
    WORD SegDs;
    WORD SegEs;
    WORD SegFs;
    WORD SegGs;
    WORD SegSs;
    DWORD EFlags;
    DWORD64 Dr0;
    DWORD64 Dr1;
    DWORD64 Dr2;
    DWORD64 Dr3;
    DWORD64 Dr6;
    DWORD64 Dr7;
    DWORD64 Rax;
    DWORD64 Rcx;
    DWORD64 Rdx;
    DWORD64 Rbx;
    DWORD64 Rsp;
    DWORD64 Rbp;
    DWORD64 Rsi;
    DWORD64 Rdi;
    DWORD64 R8;
    DWORD64 R9;
    DWORD64 R10;
    DWORD64 R11;
    DWORD64 R12;
    DWORD64 R13;
    DWORD64 R14;
    DWORD64 R15;
    DWORD64 Rip;
    union _union_54 u;
    M128A VectorRegister[26];
    DWORD64 VectorControl;
    DWORD64 DebugControl;
    DWORD64 LastBranchToRip;
    DWORD64 LastBranchFromRip;
    DWORD64 LastExceptionToRip;
    DWORD64 LastExceptionFromRip;
};

struct _EXCEPTION_RECORD {
    DWORD ExceptionCode;
    DWORD ExceptionFlags;
    struct _EXCEPTION_RECORD *ExceptionRecord;
    PVOID ExceptionAddress;
    DWORD NumberParameters;
    ULONG_PTR ExceptionInformation[15];
};

struct _EXCEPTION_POINTERS {
    PEXCEPTION_RECORD ExceptionRecord;
    PCONTEXT ContextRecord;
};

typedef void (*LPOVERLAPPED_COMPLETION_ROUTINE)(DWORD, DWORD, LPOVERLAPPED);

typedef struct _SYSTEMTIME *LPSYSTEMTIME;

typedef PRTL_CRITICAL_SECTION PCRITICAL_SECTION;

typedef PTOP_LEVEL_EXCEPTION_FILTER LPTOP_LEVEL_EXCEPTION_FILTER;

typedef struct tagSOLE_AUTHENTICATION_SERVICE tagSOLE_AUTHENTICATION_SERVICE, *PtagSOLE_AUTHENTICATION_SERVICE;

typedef struct tagSOLE_AUTHENTICATION_SERVICE SOLE_AUTHENTICATION_SERVICE;

typedef WCHAR OLECHAR;

typedef long HRESULT;

struct tagSOLE_AUTHENTICATION_SERVICE {
    DWORD dwAuthnSvc;
    DWORD dwAuthzSvc;
    OLECHAR *pPrincipalName;
    HRESULT hr;
};

typedef struct _DISPATCHER_CONTEXT _DISPATCHER_CONTEXT, *P_DISPATCHER_CONTEXT;

struct _DISPATCHER_CONTEXT {
};

typedef enum _EXCEPTION_DISPOSITION {
    ExceptionContinueExecution=0,
    ExceptionContinueSearch=1,
    ExceptionNestedException=2,
    ExceptionCollidedUnwind=3
} _EXCEPTION_DISPOSITION;

typedef enum _EXCEPTION_DISPOSITION EXCEPTION_DISPOSITION;

typedef DWORD ULONG;

typedef OLECHAR *LPOLESTR;

typedef struct DotNetPdbInfo DotNetPdbInfo, *PDotNetPdbInfo;

struct DotNetPdbInfo {
    char signature[4];
    GUID guid;
    dword age;
    char pdbpath[44];
};

typedef struct IMFMediaType IMFMediaType, *PIMFMediaType;

typedef struct IMFMediaTypeVtbl IMFMediaTypeVtbl, *PIMFMediaTypeVtbl;


/* WARNING! conflicting data type names: /guiddef.h/GUID - /GUID */

typedef GUID IID;

typedef struct tagPROPVARIANT tagPROPVARIANT, *PtagPROPVARIANT;

typedef struct tagPROPVARIANT PROPVARIANT;

typedef enum _MF_ATTRIBUTE_TYPE {
    MF_ATTRIBUTE_UINT32=0,
    MF_ATTRIBUTE_UINT64=1,
    MF_ATTRIBUTE_DOUBLE=2,
    MF_ATTRIBUTE_GUID=3,
    MF_ATTRIBUTE_STRING=4,
    MF_ATTRIBUTE_BLOB=5,
    MF_ATTRIBUTE_IUNKNOWN=6
} _MF_ATTRIBUTE_TYPE;

typedef enum _MF_ATTRIBUTE_TYPE MF_ATTRIBUTE_TYPE;

typedef struct IMFAttributes IMFAttributes, *PIMFAttributes;

typedef enum _MF_ATTRIBUTES_MATCH_TYPE {
    MF_ATTRIBUTES_MATCH_OUR_ITEMS=0,
    MF_ATTRIBUTES_MATCH_THEIR_ITEMS=1,
    MF_ATTRIBUTES_MATCH_ALL_ITEMS=2,
    MF_ATTRIBUTES_MATCH_INTERSECTION=3,
    MF_ATTRIBUTES_MATCH_SMALLER=4
} _MF_ATTRIBUTES_MATCH_TYPE;

typedef enum _MF_ATTRIBUTES_MATCH_TYPE MF_ATTRIBUTES_MATCH_TYPE;

typedef uint UINT32;

typedef ulonglong UINT64;

typedef uchar UINT8;

typedef WCHAR *LPCWSTR;

typedef struct IUnknown IUnknown, *PIUnknown;

typedef struct IMFAttributesVtbl IMFAttributesVtbl, *PIMFAttributesVtbl;

typedef struct IUnknownVtbl IUnknownVtbl, *PIUnknownVtbl;

struct IMFMediaType {
    struct IMFMediaTypeVtbl *lpVtbl;
};

struct IUnknownVtbl {
    HRESULT (*QueryInterface)(struct IUnknown *, IID *, void **);
    ULONG (*AddRef)(struct IUnknown *);
    ULONG (*Release)(struct IUnknown *);
};

struct IUnknown {
    struct IUnknownVtbl *lpVtbl;
};

struct IMFAttributesVtbl {
    HRESULT (*QueryInterface)(struct IMFAttributes *, IID *, void **);
    ULONG (*AddRef)(struct IMFAttributes *);
    ULONG (*Release)(struct IMFAttributes *);
    HRESULT (*GetItem)(struct IMFAttributes *, GUID *, PROPVARIANT *);
    HRESULT (*GetItemType)(struct IMFAttributes *, GUID *, MF_ATTRIBUTE_TYPE *);
    HRESULT (*CompareItem)(struct IMFAttributes *, GUID *, PROPVARIANT *, BOOL *);
    HRESULT (*Compare)(struct IMFAttributes *, struct IMFAttributes *, MF_ATTRIBUTES_MATCH_TYPE, BOOL *);
    HRESULT (*GetUINT32)(struct IMFAttributes *, GUID *, UINT32 *);
    HRESULT (*GetUINT64)(struct IMFAttributes *, GUID *, UINT64 *);
    HRESULT (*GetDouble)(struct IMFAttributes *, GUID *, double *);
    HRESULT (*GetGUID)(struct IMFAttributes *, GUID *, GUID *);
    HRESULT (*GetStringLength)(struct IMFAttributes *, GUID *, UINT32 *);
    HRESULT (*GetString)(struct IMFAttributes *, GUID *, LPWSTR, UINT32, UINT32 *);
    HRESULT (*GetAllocatedString)(struct IMFAttributes *, GUID *, LPWSTR *, UINT32 *);
    HRESULT (*GetBlobSize)(struct IMFAttributes *, GUID *, UINT32 *);
    HRESULT (*GetBlob)(struct IMFAttributes *, GUID *, UINT8 *, UINT32, UINT32 *);
    HRESULT (*GetAllocatedBlob)(struct IMFAttributes *, GUID *, UINT8 **, UINT32 *);
    HRESULT (*GetUnknown)(struct IMFAttributes *, GUID *, IID *, LPVOID *);
    HRESULT (*SetItem)(struct IMFAttributes *, GUID *, PROPVARIANT *);
    HRESULT (*DeleteItem)(struct IMFAttributes *, GUID *);
    HRESULT (*DeleteAllItems)(struct IMFAttributes *);
    HRESULT (*SetUINT32)(struct IMFAttributes *, GUID *, UINT32);
    HRESULT (*SetUINT64)(struct IMFAttributes *, GUID *, UINT64);
    HRESULT (*SetDouble)(struct IMFAttributes *, GUID *, double);
    HRESULT (*SetGUID)(struct IMFAttributes *, GUID *, GUID *);
    HRESULT (*SetString)(struct IMFAttributes *, GUID *, LPCWSTR);
    HRESULT (*SetBlob)(struct IMFAttributes *, GUID *, UINT8 *, UINT32);
    HRESULT (*SetUnknown)(struct IMFAttributes *, GUID *, struct IUnknown *);
    HRESULT (*LockStore)(struct IMFAttributes *);
    HRESULT (*UnlockStore)(struct IMFAttributes *);
    HRESULT (*GetCount)(struct IMFAttributes *, UINT32 *);
    HRESULT (*GetItemByIndex)(struct IMFAttributes *, UINT32, GUID *, PROPVARIANT *);
    HRESULT (*CopyAllItems)(struct IMFAttributes *, struct IMFAttributes *);
};

struct tagPROPVARIANT {
};

struct IMFAttributes {
    struct IMFAttributesVtbl *lpVtbl;
};

struct IMFMediaTypeVtbl {
    HRESULT (*QueryInterface)(struct IMFMediaType *, IID *, void **);
    ULONG (*AddRef)(struct IMFMediaType *);
    ULONG (*Release)(struct IMFMediaType *);
    HRESULT (*GetItem)(struct IMFMediaType *, GUID *, PROPVARIANT *);
    HRESULT (*GetItemType)(struct IMFMediaType *, GUID *, MF_ATTRIBUTE_TYPE *);
    HRESULT (*CompareItem)(struct IMFMediaType *, GUID *, PROPVARIANT *, BOOL *);
    HRESULT (*Compare)(struct IMFMediaType *, struct IMFAttributes *, MF_ATTRIBUTES_MATCH_TYPE, BOOL *);
    HRESULT (*GetUINT32)(struct IMFMediaType *, GUID *, UINT32 *);
    HRESULT (*GetUINT64)(struct IMFMediaType *, GUID *, UINT64 *);
    HRESULT (*GetDouble)(struct IMFMediaType *, GUID *, double *);
    HRESULT (*GetGUID)(struct IMFMediaType *, GUID *, GUID *);
    HRESULT (*GetStringLength)(struct IMFMediaType *, GUID *, UINT32 *);
    HRESULT (*GetString)(struct IMFMediaType *, GUID *, LPWSTR, UINT32, UINT32 *);
    HRESULT (*GetAllocatedString)(struct IMFMediaType *, GUID *, LPWSTR *, UINT32 *);
    HRESULT (*GetBlobSize)(struct IMFMediaType *, GUID *, UINT32 *);
    HRESULT (*GetBlob)(struct IMFMediaType *, GUID *, UINT8 *, UINT32, UINT32 *);
    HRESULT (*GetAllocatedBlob)(struct IMFMediaType *, GUID *, UINT8 **, UINT32 *);
    HRESULT (*GetUnknown)(struct IMFMediaType *, GUID *, IID *, LPVOID *);
    HRESULT (*SetItem)(struct IMFMediaType *, GUID *, PROPVARIANT *);
    HRESULT (*DeleteItem)(struct IMFMediaType *, GUID *);
    HRESULT (*DeleteAllItems)(struct IMFMediaType *);
    HRESULT (*SetUINT32)(struct IMFMediaType *, GUID *, UINT32);
    HRESULT (*SetUINT64)(struct IMFMediaType *, GUID *, UINT64);
    HRESULT (*SetDouble)(struct IMFMediaType *, GUID *, double);
    HRESULT (*SetGUID)(struct IMFMediaType *, GUID *, GUID *);
    HRESULT (*SetString)(struct IMFMediaType *, GUID *, LPCWSTR);
    HRESULT (*SetBlob)(struct IMFMediaType *, GUID *, UINT8 *, UINT32);
    HRESULT (*SetUnknown)(struct IMFMediaType *, GUID *, struct IUnknown *);
    HRESULT (*LockStore)(struct IMFMediaType *);
    HRESULT (*UnlockStore)(struct IMFMediaType *);
    HRESULT (*GetCount)(struct IMFMediaType *, UINT32 *);
    HRESULT (*GetItemByIndex)(struct IMFMediaType *, UINT32, GUID *, PROPVARIANT *);
    HRESULT (*CopyAllItems)(struct IMFMediaType *, struct IMFAttributes *);
    HRESULT (*GetMajorType)(struct IMFMediaType *, GUID *);
    HRESULT (*IsCompressedFormat)(struct IMFMediaType *, BOOL *);
    HRESULT (*IsEqual)(struct IMFMediaType *, struct IMFMediaType *, DWORD *);
    HRESULT (*GetRepresentation)(struct IMFMediaType *, GUID, LPVOID *);
    HRESULT (*FreeRepresentation)(struct IMFMediaType *, GUID, LPVOID);
};

typedef struct IMFMediaBuffer IMFMediaBuffer, *PIMFMediaBuffer;

typedef struct IMFMediaBufferVtbl IMFMediaBufferVtbl, *PIMFMediaBufferVtbl;

struct IMFMediaBufferVtbl {
    HRESULT (*QueryInterface)(struct IMFMediaBuffer *, IID *, void **);
    ULONG (*AddRef)(struct IMFMediaBuffer *);
    ULONG (*Release)(struct IMFMediaBuffer *);
    HRESULT (*Lock)(struct IMFMediaBuffer *, BYTE **, DWORD *, DWORD *);
    HRESULT (*Unlock)(struct IMFMediaBuffer *);
    HRESULT (*GetCurrentLength)(struct IMFMediaBuffer *, DWORD *);
    HRESULT (*SetCurrentLength)(struct IMFMediaBuffer *, DWORD);
    HRESULT (*GetMaxLength)(struct IMFMediaBuffer *, DWORD *);
};

struct IMFMediaBuffer {
    struct IMFMediaBufferVtbl *lpVtbl;
};

typedef struct IMFSample IMFSample, *PIMFSample;

typedef struct IMFSampleVtbl IMFSampleVtbl, *PIMFSampleVtbl;

struct IMFSample {
    struct IMFSampleVtbl *lpVtbl;
};

struct IMFSampleVtbl {
    HRESULT (*QueryInterface)(struct IMFSample *, IID *, void **);
    ULONG (*AddRef)(struct IMFSample *);
    ULONG (*Release)(struct IMFSample *);
    HRESULT (*GetItem)(struct IMFSample *, GUID *, PROPVARIANT *);
    HRESULT (*GetItemType)(struct IMFSample *, GUID *, MF_ATTRIBUTE_TYPE *);
    HRESULT (*CompareItem)(struct IMFSample *, GUID *, PROPVARIANT *, BOOL *);
    HRESULT (*Compare)(struct IMFSample *, struct IMFAttributes *, MF_ATTRIBUTES_MATCH_TYPE, BOOL *);
    HRESULT (*GetUINT32)(struct IMFSample *, GUID *, UINT32 *);
    HRESULT (*GetUINT64)(struct IMFSample *, GUID *, UINT64 *);
    HRESULT (*GetDouble)(struct IMFSample *, GUID *, double *);
    HRESULT (*GetGUID)(struct IMFSample *, GUID *, GUID *);
    HRESULT (*GetStringLength)(struct IMFSample *, GUID *, UINT32 *);
    HRESULT (*GetString)(struct IMFSample *, GUID *, LPWSTR, UINT32, UINT32 *);
    HRESULT (*GetAllocatedString)(struct IMFSample *, GUID *, LPWSTR *, UINT32 *);
    HRESULT (*GetBlobSize)(struct IMFSample *, GUID *, UINT32 *);
    HRESULT (*GetBlob)(struct IMFSample *, GUID *, UINT8 *, UINT32, UINT32 *);
    HRESULT (*GetAllocatedBlob)(struct IMFSample *, GUID *, UINT8 **, UINT32 *);
    HRESULT (*GetUnknown)(struct IMFSample *, GUID *, IID *, LPVOID *);
    HRESULT (*SetItem)(struct IMFSample *, GUID *, PROPVARIANT *);
    HRESULT (*DeleteItem)(struct IMFSample *, GUID *);
    HRESULT (*DeleteAllItems)(struct IMFSample *);
    HRESULT (*SetUINT32)(struct IMFSample *, GUID *, UINT32);
    HRESULT (*SetUINT64)(struct IMFSample *, GUID *, UINT64);
    HRESULT (*SetDouble)(struct IMFSample *, GUID *, double);
    HRESULT (*SetGUID)(struct IMFSample *, GUID *, GUID *);
    HRESULT (*SetString)(struct IMFSample *, GUID *, LPCWSTR);
    HRESULT (*SetBlob)(struct IMFSample *, GUID *, UINT8 *, UINT32);
    HRESULT (*SetUnknown)(struct IMFSample *, GUID *, struct IUnknown *);
    HRESULT (*LockStore)(struct IMFSample *);
    HRESULT (*UnlockStore)(struct IMFSample *);
    HRESULT (*GetCount)(struct IMFSample *, UINT32 *);
    HRESULT (*GetItemByIndex)(struct IMFSample *, UINT32, GUID *, PROPVARIANT *);
    HRESULT (*CopyAllItems)(struct IMFSample *, struct IMFAttributes *);
    HRESULT (*GetSampleFlags)(struct IMFSample *, DWORD *);
    HRESULT (*SetSampleFlags)(struct IMFSample *, DWORD);
    HRESULT (*GetSampleTime)(struct IMFSample *, LONGLONG *);
    HRESULT (*SetSampleTime)(struct IMFSample *, LONGLONG);
    HRESULT (*GetSampleDuration)(struct IMFSample *, LONGLONG *);
    HRESULT (*SetSampleDuration)(struct IMFSample *, LONGLONG);
    HRESULT (*GetBufferCount)(struct IMFSample *, DWORD *);
    HRESULT (*GetBufferByIndex)(struct IMFSample *, DWORD, struct IMFMediaBuffer **);
    HRESULT (*ConvertToContiguousBuffer)(struct IMFSample *, struct IMFMediaBuffer **);
    HRESULT (*AddBuffer)(struct IMFSample *, struct IMFMediaBuffer *);
    HRESULT (*RemoveBufferByIndex)(struct IMFSample *, DWORD);
    HRESULT (*RemoveAllBuffers)(struct IMFSample *);
    HRESULT (*GetTotalLength)(struct IMFSample *, DWORD *);
    HRESULT (*CopyToBuffer)(struct IMFSample *, struct IMFMediaBuffer *);
};

typedef ulong _fsize_t;

typedef struct _finddata64i32_t _finddata64i32_t, *P_finddata64i32_t;

typedef longlong __time64_t;

struct _finddata64i32_t {
    uint attrib;
    __time64_t time_create;
    __time64_t time_access;
    __time64_t time_write;
    _fsize_t size;
    char name[260];
};

typedef BYTE UCHAR;

typedef longlong fpos_t;

typedef struct _SETJMP_FLOAT128 _SETJMP_FLOAT128, *P_SETJMP_FLOAT128;

typedef struct _SETJMP_FLOAT128 SETJMP_FLOAT128;

typedef SETJMP_FLOAT128 _JBTYPE;

struct _SETJMP_FLOAT128 {
    ulonglong Part[2];
};

typedef struct _iobuf _iobuf, *P_iobuf;

struct _iobuf {
    char *_ptr;
    int _cnt;
    char *_base;
    int _flag;
    int _file;
    int _charbuf;
    int _bufsiz;
    char *_tmpfname;
};

typedef struct _iobuf FILE;

typedef int PMFN;

typedef struct _s_ThrowInfo _s_ThrowInfo, *P_s_ThrowInfo;

struct _s_ThrowInfo {
    uint attributes;
    PMFN pmfnUnwind;
    int pForwardCompat;
    int pCatchableTypeArray;
};

typedef struct TypeDescriptor TypeDescriptor, *PTypeDescriptor;

struct TypeDescriptor {
    void *pVFTable;
    void *spare;
    char name[0];
};

typedef struct _s_ThrowInfo ThrowInfo;

typedef char *va_list;

typedef ulonglong uintptr_t;

typedef enum _WLAN_INTERFACE_STATE {
    wlan_interface_state_not_ready=0,
    wlan_interface_state_connected=1,
    wlan_interface_state_ad_hoc_network_formed=2,
    wlan_interface_state_disconnecting=3,
    wlan_interface_state_disconnected=4,
    wlan_interface_state_associating=5,
    wlan_interface_state_discovering=6,
    wlan_interface_state_authenticating=7
} _WLAN_INTERFACE_STATE;

typedef enum _WLAN_INTERFACE_STATE WLAN_INTERFACE_STATE;

typedef struct _WLAN_INTERFACE_INFO _WLAN_INTERFACE_INFO, *P_WLAN_INTERFACE_INFO;

struct _WLAN_INTERFACE_INFO {
    GUID InterfaceGuid;
    WCHAR strInterfaceDescription[256];
    WLAN_INTERFACE_STATE isState;
};

typedef struct _WLAN_INTERFACE_INFO_LIST _WLAN_INTERFACE_INFO_LIST, *P_WLAN_INTERFACE_INFO_LIST;

typedef struct _WLAN_INTERFACE_INFO_LIST *PWLAN_INTERFACE_INFO_LIST;

typedef struct _WLAN_INTERFACE_INFO WLAN_INTERFACE_INFO;

struct _WLAN_INTERFACE_INFO_LIST {
    DWORD dwNumberOfItems;
    DWORD dwIndex;
    WLAN_INTERFACE_INFO InterfaceInfo[1];
};

typedef ulonglong size_t;

typedef struct lconv lconv, *Plconv;

struct lconv {
    char *decimal_point;
    char *thousands_sep;
    char *grouping;
    char *int_curr_symbol;
    char *currency_symbol;
    char *mon_decimal_point;
    char *mon_thousands_sep;
    char *mon_grouping;
    char *positive_sign;
    char *negative_sign;
    char int_frac_digits;
    char frac_digits;
    char p_cs_precedes;
    char p_sep_by_space;
    char n_cs_precedes;
    char n_sep_by_space;
    char p_sign_posn;
    char n_sign_posn;
    wchar_t *_W_decimal_point;
    wchar_t *_W_thousands_sep;
    wchar_t *_W_int_curr_symbol;
    wchar_t *_W_currency_symbol;
    wchar_t *_W_mon_decimal_point;
    wchar_t *_W_mon_thousands_sep;
    wchar_t *_W_positive_sign;
    wchar_t *_W_negative_sign;
};

typedef struct threadlocaleinfostruct threadlocaleinfostruct, *Pthreadlocaleinfostruct;

typedef struct threadlocaleinfostruct *pthreadlocinfo;

typedef struct localerefcount localerefcount, *Plocalerefcount;

typedef struct localerefcount locrefcount;

typedef struct __lc_time_data __lc_time_data, *P__lc_time_data;

struct localerefcount {
    char *locale;
    wchar_t *wlocale;
    int *refcount;
    int *wrefcount;
};

struct threadlocaleinfostruct {
    int refcount;
    uint lc_codepage;
    uint lc_collate_cp;
    uint lc_time_cp;
    locrefcount lc_category[6];
    int lc_clike;
    int mb_cur_max;
    int *lconv_intl_refcount;
    int *lconv_num_refcount;
    int *lconv_mon_refcount;
    struct lconv *lconv;
    int *ctype1_refcount;
    ushort *ctype1;
    ushort *pctype;
    uchar *pclmap;
    uchar *pcumap;
    struct __lc_time_data *lc_time_curr;
    wchar_t *locale_name[6];
};

struct __lc_time_data {
    char *wday_abbr[7];
    char *wday[7];
    char *month_abbr[12];
    char *month[12];
    char *ampm[2];
    char *ww_sdatefmt;
    char *ww_ldatefmt;
    char *ww_timefmt;
    int ww_caltype;
    int refcount;
    wchar_t *_W_wday_abbr[7];
    wchar_t *_W_wday[7];
    wchar_t *_W_month_abbr[12];
    wchar_t *_W_month[12];
    wchar_t *_W_ampm[2];
    wchar_t *_W_ww_sdatefmt;
    wchar_t *_W_ww_ldatefmt;
    wchar_t *_W_ww_timefmt;
    wchar_t *_W_ww_locale_name;
};

typedef int errno_t;

typedef size_t rsize_t;

typedef struct localeinfo_struct localeinfo_struct, *Plocaleinfo_struct;

typedef struct threadmbcinfostruct threadmbcinfostruct, *Pthreadmbcinfostruct;

typedef struct threadmbcinfostruct *pthreadmbcinfo;

struct threadmbcinfostruct {
    int refcount;
    int mbcodepage;
    int ismbcodepage;
    ushort mbulinfo[6];
    uchar mbctype[257];
    uchar mbcasemap[256];
    wchar_t *mblocalename;
};

struct localeinfo_struct {
    pthreadlocinfo locinfo;
    pthreadmbcinfo mbcinfo;
};

typedef longlong intptr_t;

typedef struct localeinfo_struct *_locale_t;

typedef struct tagWNDCLASSA tagWNDCLASSA, *PtagWNDCLASSA;

typedef uint UINT;

typedef longlong LONG_PTR;

typedef LONG_PTR LRESULT;

typedef struct HWND__ HWND__, *PHWND__;

typedef struct HWND__ *HWND;

typedef ulonglong UINT_PTR;

typedef UINT_PTR WPARAM;

typedef LONG_PTR LPARAM;

typedef LRESULT (*WNDPROC)(HWND, UINT, WPARAM, LPARAM);

typedef struct HINSTANCE__ HINSTANCE__, *PHINSTANCE__;

typedef struct HINSTANCE__ *HINSTANCE;

typedef struct HICON__ HICON__, *PHICON__;

typedef struct HICON__ *HICON;

typedef HICON HCURSOR;

typedef struct HBRUSH__ HBRUSH__, *PHBRUSH__;

typedef struct HBRUSH__ *HBRUSH;

typedef CHAR *LPCSTR;

struct HBRUSH__ {
    int unused;
};

struct tagWNDCLASSA {
    UINT style;
    WNDPROC lpfnWndProc;
    int cbClsExtra;
    int cbWndExtra;
    HINSTANCE hInstance;
    HICON hIcon;
    HCURSOR hCursor;
    HBRUSH hbrBackground;
    LPCSTR lpszMenuName;
    LPCSTR lpszClassName;
};

struct HICON__ {
    int unused;
};

struct HINSTANCE__ {
    int unused;
};

struct HWND__ {
    int unused;
};

typedef struct tagMSG tagMSG, *PtagMSG;

typedef struct tagMSG MSG;

typedef struct tagPOINT tagPOINT, *PtagPOINT;

typedef struct tagPOINT POINT;

struct tagPOINT {
    LONG x;
    LONG y;
};

struct tagMSG {
    HWND hwnd;
    UINT message;
    WPARAM wParam;
    LPARAM lParam;
    DWORD time;
    POINT pt;
};

typedef struct tagMSG *LPMSG;

typedef struct tagMONITORINFO tagMONITORINFO, *PtagMONITORINFO;

typedef struct tagMONITORINFO *LPMONITORINFO;

typedef struct tagRECT tagRECT, *PtagRECT;

typedef struct tagRECT RECT;

struct tagRECT {
    LONG left;
    LONG top;
    LONG right;
    LONG bottom;
};

struct tagMONITORINFO {
    DWORD cbSize;
    RECT rcMonitor;
    RECT rcWork;
    DWORD dwFlags;
};

typedef struct tagRAWINPUTHEADER tagRAWINPUTHEADER, *PtagRAWINPUTHEADER;

struct tagRAWINPUTHEADER {
    DWORD dwType;
    DWORD dwSize;
    HANDLE hDevice;
    WPARAM wParam;
};

typedef struct tagRAWINPUT tagRAWINPUT, *PtagRAWINPUT;

typedef struct tagRAWINPUTHEADER RAWINPUTHEADER;

typedef union _union_950 _union_950, *P_union_950;

typedef struct tagRAWMOUSE tagRAWMOUSE, *PtagRAWMOUSE;

typedef struct tagRAWMOUSE RAWMOUSE;

typedef struct tagRAWKEYBOARD tagRAWKEYBOARD, *PtagRAWKEYBOARD;

typedef struct tagRAWKEYBOARD RAWKEYBOARD;

typedef struct tagRAWHID tagRAWHID, *PtagRAWHID;

typedef struct tagRAWHID RAWHID;

typedef ushort USHORT;

typedef union _union_945 _union_945, *P_union_945;


/* WARNING! conflicting data type names: /WinDef.h/ULONG - /wtypes.h/ULONG */

typedef struct _struct_946 _struct_946, *P_struct_946;

struct _struct_946 {
    USHORT usButtonFlags;
    USHORT usButtonData;
};

union _union_945 {
    ULONG ulButtons;
    struct _struct_946 field1;
};

struct tagRAWHID {
    DWORD dwSizeHid;
    DWORD dwCount;
    BYTE bRawData[1];
};

struct tagRAWKEYBOARD {
    USHORT MakeCode;
    USHORT Flags;
    USHORT Reserved;
    USHORT VKey;
    UINT Message;
    ULONG ExtraInformation;
};

struct tagRAWMOUSE {
    USHORT usFlags;
    union _union_945 field1_0x4;
    ULONG ulRawButtons;
    LONG lLastX;
    LONG lLastY;
    ULONG ulExtraInformation;
};

union _union_950 {
    RAWMOUSE mouse;
    RAWKEYBOARD keyboard;
    RAWHID hid;
};

struct tagRAWINPUT {
    RAWINPUTHEADER header;
    union _union_950 data;
};

typedef struct tagRAWINPUTDEVICE tagRAWINPUTDEVICE, *PtagRAWINPUTDEVICE;

typedef struct tagRAWINPUTDEVICE RAWINPUTDEVICE;

struct tagRAWINPUTDEVICE {
    USHORT usUsagePage;
    USHORT usUsage;
    DWORD dwFlags;
    HWND hwndTarget;
};

typedef struct tagWNDCLASSA WNDCLASSA;

typedef struct tagWNDCLASSEXA tagWNDCLASSEXA, *PtagWNDCLASSEXA;

typedef struct tagWNDCLASSEXA WNDCLASSEXA;

struct tagWNDCLASSEXA {
    UINT cbSize;
    UINT style;
    WNDPROC lpfnWndProc;
    int cbClsExtra;
    int cbWndExtra;
    HINSTANCE hInstance;
    HICON hIcon;
    HCURSOR hCursor;
    HBRUSH hbrBackground;
    LPCSTR lpszMenuName;
    LPCSTR lpszClassName;
    HICON hIconSm;
};

typedef RAWINPUTDEVICE *PCRAWINPUTDEVICE;

typedef struct tagRAWINPUT *PRAWINPUT;

typedef BOOL (*WNDENUMPROC)(HWND, LPARAM);

typedef struct _GUID _GUID, *P_GUID;

struct _GUID {
    ulong Data1;
    ushort Data2;
    ushort Data3;
    uchar Data4[8];
};

typedef GUID *LPCGUID;

typedef struct _DISPLAY_DEVICEA _DISPLAY_DEVICEA, *P_DISPLAY_DEVICEA;

struct _DISPLAY_DEVICEA {
    DWORD cb;
    CHAR DeviceName[32];
    CHAR DeviceString[128];
    DWORD StateFlags;
    CHAR DeviceID[128];
    CHAR DeviceKey[128];
};

typedef struct _devicemodeA _devicemodeA, *P_devicemodeA;

typedef union _union_677 _union_677, *P_union_677;

typedef union _union_680 _union_680, *P_union_680;

typedef struct _struct_678 _struct_678, *P_struct_678;

typedef struct _struct_679 _struct_679, *P_struct_679;

typedef struct _POINTL _POINTL, *P_POINTL;

typedef struct _POINTL POINTL;

struct _POINTL {
    LONG x;
    LONG y;
};

struct _struct_679 {
    POINTL dmPosition;
    DWORD dmDisplayOrientation;
    DWORD dmDisplayFixedOutput;
};

struct _struct_678 {
    short dmOrientation;
    short dmPaperSize;
    short dmPaperLength;
    short dmPaperWidth;
    short dmScale;
    short dmCopies;
    short dmDefaultSource;
    short dmPrintQuality;
};

union _union_677 {
    struct _struct_678 field0;
    struct _struct_679 field1;
};

union _union_680 {
    DWORD dmDisplayFlags;
    DWORD dmNup;
};

struct _devicemodeA {
    BYTE dmDeviceName[32];
    WORD dmSpecVersion;
    WORD dmDriverVersion;
    WORD dmSize;
    WORD dmDriverExtra;
    DWORD dmFields;
    union _union_677 field6_0x2c;
    short dmColor;
    short dmDuplex;
    short dmYResolution;
    short dmTTOption;
    short dmCollate;
    BYTE dmFormName[32];
    WORD dmLogPixels;
    DWORD dmBitsPerPel;
    DWORD dmPelsWidth;
    DWORD dmPelsHeight;
    union _union_680 field17_0x74;
    DWORD dmDisplayFrequency;
    DWORD dmICMMethod;
    DWORD dmICMIntent;
    DWORD dmMediaType;
    DWORD dmDitherType;
    DWORD dmReserved1;
    DWORD dmReserved2;
    DWORD dmPanningWidth;
    DWORD dmPanningHeight;
};

typedef struct _devicemodeA DEVMODEA;

typedef struct _DISPLAY_DEVICEA *PDISPLAY_DEVICEA;

typedef PVOID BCRYPT_KEY_HANDLE;

typedef PVOID BCRYPT_HANDLE;

typedef PVOID BCRYPT_ALG_HANDLE;

typedef PVOID BCRYPT_HASH_HANDLE;

typedef LONG NTSTATUS;

typedef PVOID PSECURITY_DESCRIPTOR;

typedef struct _TOKEN_PRIVILEGES _TOKEN_PRIVILEGES, *P_TOKEN_PRIVILEGES;

typedef struct _LUID_AND_ATTRIBUTES _LUID_AND_ATTRIBUTES, *P_LUID_AND_ATTRIBUTES;

typedef struct _LUID_AND_ATTRIBUTES LUID_AND_ATTRIBUTES;

typedef struct _LUID _LUID, *P_LUID;

typedef struct _LUID LUID;

struct _LUID {
    DWORD LowPart;
    LONG HighPart;
};

struct _LUID_AND_ATTRIBUTES {
    LUID Luid;
    DWORD Attributes;
};

struct _TOKEN_PRIVILEGES {
    DWORD PrivilegeCount;
    LUID_AND_ATTRIBUTES Privileges[1];
};

typedef struct _RUNTIME_FUNCTION _RUNTIME_FUNCTION, *P_RUNTIME_FUNCTION;

struct _RUNTIME_FUNCTION {
    DWORD BeginAddress;
    DWORD EndAddress;
    DWORD UnwindData;
};

typedef struct _RUNTIME_FUNCTION *PRUNTIME_FUNCTION;

typedef struct _UNWIND_HISTORY_TABLE_ENTRY _UNWIND_HISTORY_TABLE_ENTRY, *P_UNWIND_HISTORY_TABLE_ENTRY;

typedef struct _UNWIND_HISTORY_TABLE_ENTRY UNWIND_HISTORY_TABLE_ENTRY;

struct _UNWIND_HISTORY_TABLE_ENTRY {
    DWORD64 ImageBase;
    PRUNTIME_FUNCTION FunctionEntry;
};

typedef union _union_61 _union_61, *P_union_61;

typedef struct _M128A *PM128A;

typedef struct _struct_62 _struct_62, *P_struct_62;

struct _struct_62 {
    PM128A Xmm0;
    PM128A Xmm1;
    PM128A Xmm2;
    PM128A Xmm3;
    PM128A Xmm4;
    PM128A Xmm5;
    PM128A Xmm6;
    PM128A Xmm7;
    PM128A Xmm8;
    PM128A Xmm9;
    PM128A Xmm10;
    PM128A Xmm11;
    PM128A Xmm12;
    PM128A Xmm13;
    PM128A Xmm14;
    PM128A Xmm15;
};

union _union_61 {
    PM128A FloatingContext[16];
    struct _struct_62 s;
};

typedef struct _struct_64 _struct_64, *P_struct_64;

typedef ulonglong *PDWORD64;

struct _struct_64 {
    PDWORD64 Rax;
    PDWORD64 Rcx;
    PDWORD64 Rdx;
    PDWORD64 Rbx;
    PDWORD64 Rsp;
    PDWORD64 Rbp;
    PDWORD64 Rsi;
    PDWORD64 Rdi;
    PDWORD64 R8;
    PDWORD64 R9;
    PDWORD64 R10;
    PDWORD64 R11;
    PDWORD64 R12;
    PDWORD64 R13;
    PDWORD64 R14;
    PDWORD64 R15;
};

typedef union _union_63 _union_63, *P_union_63;

union _union_63 {
    PDWORD64 IntegerContext[16];
    struct _struct_64 s;
};

typedef EXCEPTION_DISPOSITION (EXCEPTION_ROUTINE)(struct _EXCEPTION_RECORD *, PVOID, struct _CONTEXT *, PVOID);

typedef struct _UNWIND_HISTORY_TABLE _UNWIND_HISTORY_TABLE, *P_UNWIND_HISTORY_TABLE;

struct _UNWIND_HISTORY_TABLE {
    DWORD Count;
    BYTE LocalHint;
    BYTE GlobalHint;
    BYTE Search;
    BYTE Once;
    DWORD64 LowAddress;
    DWORD64 HighAddress;
    UNWIND_HISTORY_TABLE_ENTRY Entry[12];
};

typedef struct _LUID *PLUID;

typedef LONG *PLONG;

typedef struct _OSVERSIONINFOA _OSVERSIONINFOA, *P_OSVERSIONINFOA;

struct _OSVERSIONINFOA {
    DWORD dwOSVersionInfoSize;
    DWORD dwMajorVersion;
    DWORD dwMinorVersion;
    DWORD dwBuildNumber;
    DWORD dwPlatformId;
    CHAR szCSDVersion[128];
};

typedef struct _OSVERSIONINFOEXW _OSVERSIONINFOEXW, *P_OSVERSIONINFOEXW;

struct _OSVERSIONINFOEXW {
    DWORD dwOSVersionInfoSize;
    DWORD dwMajorVersion;
    DWORD dwMinorVersion;
    DWORD dwBuildNumber;
    DWORD dwPlatformId;
    WCHAR szCSDVersion[128];
    WORD wServicePackMajor;
    WORD wServicePackMinor;
    WORD wSuiteMask;
    BYTE wProductType;
    BYTE wReserved;
};

typedef struct _OSVERSIONINFOA *LPOSVERSIONINFOA;

typedef DWORD EXECUTION_STATE;

typedef struct _TOKEN_PRIVILEGES *PTOKEN_PRIVILEGES;

typedef DWORD ACCESS_MASK;

typedef struct _KNONVOLATILE_CONTEXT_POINTERS _KNONVOLATILE_CONTEXT_POINTERS, *P_KNONVOLATILE_CONTEXT_POINTERS;

struct _KNONVOLATILE_CONTEXT_POINTERS {
    union _union_61 u;
    union _union_63 u2;
};

typedef union _LARGE_INTEGER _LARGE_INTEGER, *P_LARGE_INTEGER;

typedef struct _struct_19 _struct_19, *P_struct_19;

typedef struct _struct_20 _struct_20, *P_struct_20;

struct _struct_20 {
    DWORD LowPart;
    LONG HighPart;
};

struct _struct_19 {
    DWORD LowPart;
    LONG HighPart;
};

union _LARGE_INTEGER {
    struct _struct_19 s;
    struct _struct_20 u;
    LONGLONG QuadPart;
};

typedef union _LARGE_INTEGER LARGE_INTEGER;

typedef struct _OSVERSIONINFOEXW *LPOSVERSIONINFOEXW;

typedef struct _UNWIND_HISTORY_TABLE *PUNWIND_HISTORY_TABLE;

typedef LARGE_INTEGER *PLARGE_INTEGER;

typedef struct _KNONVOLATILE_CONTEXT_POINTERS *PKNONVOLATILE_CONTEXT_POINTERS;

typedef EXCEPTION_ROUTINE *PEXCEPTION_ROUTINE;

typedef HANDLE *PHANDLE;

typedef struct _EVENT_DESCRIPTOR _EVENT_DESCRIPTOR, *P_EVENT_DESCRIPTOR;

typedef struct _EVENT_DESCRIPTOR EVENT_DESCRIPTOR;

struct _EVENT_DESCRIPTOR {
    USHORT Id;
    UCHAR Version;
    UCHAR Channel;
    UCHAR Level;
    UCHAR Opcode;
    USHORT Task;
    ULONGLONG Keyword;
};

typedef struct _EVENT_DATA_DESCRIPTOR _EVENT_DATA_DESCRIPTOR, *P_EVENT_DATA_DESCRIPTOR;

struct _EVENT_DATA_DESCRIPTOR {
    ULONGLONG Ptr;
    ULONG Size;
    ULONG Reserved;
};

typedef struct _EVENT_FILTER_DESCRIPTOR _EVENT_FILTER_DESCRIPTOR, *P_EVENT_FILTER_DESCRIPTOR;

struct _EVENT_FILTER_DESCRIPTOR {
    ULONGLONG Ptr;
    ULONG Size;
    ULONG Type;
};

typedef struct _EVENT_FILTER_DESCRIPTOR *PEVENT_FILTER_DESCRIPTOR;

typedef void (*PENABLECALLBACK)(LPCGUID, ULONG, UCHAR, ULONGLONG, ULONGLONG, PEVENT_FILTER_DESCRIPTOR, PVOID);

typedef ULONGLONG REGHANDLE;

typedef struct _EVENT_DATA_DESCRIPTOR *PEVENT_DATA_DESCRIPTOR;

typedef ULONGLONG *PREGHANDLE;

typedef EVENT_DESCRIPTOR *PCEVENT_DESCRIPTOR;

typedef struct IMAGE_DOS_HEADER IMAGE_DOS_HEADER, *PIMAGE_DOS_HEADER;

struct IMAGE_DOS_HEADER {
    char e_magic[2]; /* Magic number */
    word e_cblp; /* Bytes of last page */
    word e_cp; /* Pages in file */
    word e_crlc; /* Relocations */
    word e_cparhdr; /* Size of header in paragraphs */
    word e_minalloc; /* Minimum extra paragraphs needed */
    word e_maxalloc; /* Maximum extra paragraphs needed */
    word e_ss; /* Initial (relative) SS value */
    word e_sp; /* Initial SP value */
    word e_csum; /* Checksum */
    word e_ip; /* Initial IP value */
    word e_cs; /* Initial (relative) CS value */
    word e_lfarlc; /* File address of relocation table */
    word e_ovno; /* Overlay number */
    word e_res[4][4]; /* Reserved words */
    word e_oemid; /* OEM identifier (for e_oeminfo) */
    word e_oeminfo; /* OEM information; e_oemid specific */
    word e_res2[10][10]; /* Reserved words */
    dword e_lfanew; /* File address of new exe header */
    byte e_program[64]; /* Actual DOS program */
};

typedef struct _CRYPTOAPI_BLOB _CRYPTOAPI_BLOB, *P_CRYPTOAPI_BLOB;

typedef struct _CRYPTOAPI_BLOB CRYPT_OBJID_BLOB;

struct _CRYPTOAPI_BLOB {
    DWORD cbData;
    BYTE *pbData;
};

typedef struct _CRYPTOAPI_BLOB CRYPT_INTEGER_BLOB;

typedef struct _CTL_CONTEXT _CTL_CONTEXT, *P_CTL_CONTEXT;

typedef struct _CTL_CONTEXT CTL_CONTEXT;

typedef struct _CTL_INFO _CTL_INFO, *P_CTL_INFO;

typedef struct _CTL_INFO *PCTL_INFO;

typedef void *HCERTSTORE;

typedef void *HCRYPTMSG;

typedef struct _CTL_USAGE _CTL_USAGE, *P_CTL_USAGE;

typedef struct _CTL_USAGE CTL_USAGE;

typedef struct _CRYPTOAPI_BLOB CRYPT_DATA_BLOB;

typedef struct _CRYPT_ALGORITHM_IDENTIFIER _CRYPT_ALGORITHM_IDENTIFIER, *P_CRYPT_ALGORITHM_IDENTIFIER;

typedef struct _CRYPT_ALGORITHM_IDENTIFIER CRYPT_ALGORITHM_IDENTIFIER;

typedef struct _CTL_ENTRY _CTL_ENTRY, *P_CTL_ENTRY;

typedef struct _CTL_ENTRY *PCTL_ENTRY;

typedef struct _CERT_EXTENSION _CERT_EXTENSION, *P_CERT_EXTENSION;

typedef struct _CERT_EXTENSION *PCERT_EXTENSION;

typedef struct _CRYPT_ATTRIBUTE _CRYPT_ATTRIBUTE, *P_CRYPT_ATTRIBUTE;

typedef struct _CRYPT_ATTRIBUTE *PCRYPT_ATTRIBUTE;

typedef struct _CRYPTOAPI_BLOB *PCRYPT_ATTR_BLOB;

struct _CERT_EXTENSION {
    LPSTR pszObjId;
    BOOL fCritical;
    CRYPT_OBJID_BLOB Value;
};

struct _CTL_USAGE {
    DWORD cUsageIdentifier;
    LPSTR *rgpszUsageIdentifier;
};

struct _CRYPT_ATTRIBUTE {
    LPSTR pszObjId;
    DWORD cValue;
    PCRYPT_ATTR_BLOB rgValue;
};

struct _CRYPT_ALGORITHM_IDENTIFIER {
    LPSTR pszObjId;
    CRYPT_OBJID_BLOB Parameters;
};

struct _CTL_ENTRY {
    CRYPT_DATA_BLOB SubjectIdentifier;
    DWORD cAttribute;
    PCRYPT_ATTRIBUTE rgAttribute;
};

struct _CTL_INFO {
    DWORD dwVersion;
    CTL_USAGE SubjectUsage;
    CRYPT_DATA_BLOB ListIdentifier;
    CRYPT_INTEGER_BLOB SequenceNumber;
    FILETIME ThisUpdate;
    FILETIME NextUpdate;
    CRYPT_ALGORITHM_IDENTIFIER SubjectAlgorithm;
    DWORD cCTLEntry;
    PCTL_ENTRY rgCTLEntry;
    DWORD cExtension;
    PCERT_EXTENSION rgExtension;
};

struct _CTL_CONTEXT {
    DWORD dwMsgAndCertEncodingType;
    BYTE *pbCtlEncoded;
    DWORD cbCtlEncoded;
    PCTL_INFO pCtlInfo;
    HCERTSTORE hCertStore;
    HCRYPTMSG hCryptMsg;
    BYTE *pbCtlContent;
    DWORD cbCtlContent;
};

typedef struct _CRL_ENTRY _CRL_ENTRY, *P_CRL_ENTRY;

struct _CRL_ENTRY {
    CRYPT_INTEGER_BLOB SerialNumber;
    FILETIME RevocationDate;
    DWORD cExtension;
    PCERT_EXTENSION rgExtension;
};

typedef struct _CERT_REVOCATION_CRL_INFO _CERT_REVOCATION_CRL_INFO, *P_CERT_REVOCATION_CRL_INFO;

typedef struct _CRL_CONTEXT _CRL_CONTEXT, *P_CRL_CONTEXT;

typedef struct _CRL_CONTEXT CRL_CONTEXT;

typedef CRL_CONTEXT *PCCRL_CONTEXT;

typedef struct _CRL_ENTRY *PCRL_ENTRY;

typedef struct _CRL_INFO _CRL_INFO, *P_CRL_INFO;

typedef struct _CRL_INFO *PCRL_INFO;

typedef struct _CRYPTOAPI_BLOB CERT_NAME_BLOB;

struct _CERT_REVOCATION_CRL_INFO {
    DWORD cbSize;
    PCCRL_CONTEXT pBaseCrlContext;
    PCCRL_CONTEXT pDeltaCrlContext;
    PCRL_ENTRY pCrlEntry;
    BOOL fDeltaCrlEntry;
};

struct _CRL_CONTEXT {
    DWORD dwCertEncodingType;
    BYTE *pbCrlEncoded;
    DWORD cbCrlEncoded;
    PCRL_INFO pCrlInfo;
    HCERTSTORE hCertStore;
};

struct _CRL_INFO {
    DWORD dwVersion;
    CRYPT_ALGORITHM_IDENTIFIER SignatureAlgorithm;
    CERT_NAME_BLOB Issuer;
    FILETIME ThisUpdate;
    FILETIME NextUpdate;
    DWORD cCRLEntry;
    PCRL_ENTRY rgCRLEntry;
    DWORD cExtension;
    PCERT_EXTENSION rgExtension;
};

typedef struct _CERT_CHAIN_ELEMENT _CERT_CHAIN_ELEMENT, *P_CERT_CHAIN_ELEMENT;

typedef struct _CERT_CONTEXT _CERT_CONTEXT, *P_CERT_CONTEXT;

typedef struct _CERT_CONTEXT CERT_CONTEXT;

typedef CERT_CONTEXT *PCCERT_CONTEXT;

typedef struct _CERT_TRUST_STATUS _CERT_TRUST_STATUS, *P_CERT_TRUST_STATUS;

typedef struct _CERT_TRUST_STATUS CERT_TRUST_STATUS;

typedef struct _CERT_REVOCATION_INFO _CERT_REVOCATION_INFO, *P_CERT_REVOCATION_INFO;

typedef struct _CERT_REVOCATION_INFO *PCERT_REVOCATION_INFO;

typedef struct _CTL_USAGE *PCERT_ENHKEY_USAGE;

typedef struct _CERT_INFO _CERT_INFO, *P_CERT_INFO;

typedef struct _CERT_INFO *PCERT_INFO;

typedef struct _CERT_REVOCATION_CRL_INFO *PCERT_REVOCATION_CRL_INFO;

typedef struct _CERT_PUBLIC_KEY_INFO _CERT_PUBLIC_KEY_INFO, *P_CERT_PUBLIC_KEY_INFO;

typedef struct _CERT_PUBLIC_KEY_INFO CERT_PUBLIC_KEY_INFO;

typedef struct _CRYPT_BIT_BLOB _CRYPT_BIT_BLOB, *P_CRYPT_BIT_BLOB;

typedef struct _CRYPT_BIT_BLOB CRYPT_BIT_BLOB;

struct _CERT_TRUST_STATUS {
    DWORD dwErrorStatus;
    DWORD dwInfoStatus;
};

struct _CERT_CHAIN_ELEMENT {
    DWORD cbSize;
    PCCERT_CONTEXT pCertContext;
    CERT_TRUST_STATUS TrustStatus;
    PCERT_REVOCATION_INFO pRevocationInfo;
    PCERT_ENHKEY_USAGE pIssuanceUsage;
    PCERT_ENHKEY_USAGE pApplicationUsage;
    LPCWSTR pwszExtendedErrorInfo;
};

struct _CRYPT_BIT_BLOB {
    DWORD cbData;
    BYTE *pbData;
    DWORD cUnusedBits;
};

struct _CERT_PUBLIC_KEY_INFO {
    CRYPT_ALGORITHM_IDENTIFIER Algorithm;
    CRYPT_BIT_BLOB PublicKey;
};

struct _CERT_INFO {
    DWORD dwVersion;
    CRYPT_INTEGER_BLOB SerialNumber;
    CRYPT_ALGORITHM_IDENTIFIER SignatureAlgorithm;
    CERT_NAME_BLOB Issuer;
    FILETIME NotBefore;
    FILETIME NotAfter;
    CERT_NAME_BLOB Subject;
    CERT_PUBLIC_KEY_INFO SubjectPublicKeyInfo;
    CRYPT_BIT_BLOB IssuerUniqueId;
    CRYPT_BIT_BLOB SubjectUniqueId;
    DWORD cExtension;
    PCERT_EXTENSION rgExtension;
};

struct _CERT_REVOCATION_INFO {
    DWORD cbSize;
    DWORD dwRevocationResult;
    LPCSTR pszRevocationOid;
    LPVOID pvOidSpecificInfo;
    BOOL fHasFreshnessTime;
    DWORD dwFreshnessTime;
    PCERT_REVOCATION_CRL_INFO pCrlInfo;
};

struct _CERT_CONTEXT {
    DWORD dwCertEncodingType;
    BYTE *pbCertEncoded;
    DWORD cbCertEncoded;
    PCERT_INFO pCertInfo;
    HCERTSTORE hCertStore;
};

typedef struct _CERT_SIMPLE_CHAIN _CERT_SIMPLE_CHAIN, *P_CERT_SIMPLE_CHAIN;

typedef struct _CERT_SIMPLE_CHAIN *PCERT_SIMPLE_CHAIN;

typedef struct _CERT_CHAIN_ELEMENT *PCERT_CHAIN_ELEMENT;

typedef struct _CERT_TRUST_LIST_INFO _CERT_TRUST_LIST_INFO, *P_CERT_TRUST_LIST_INFO;

typedef struct _CERT_TRUST_LIST_INFO *PCERT_TRUST_LIST_INFO;

typedef CTL_CONTEXT *PCCTL_CONTEXT;

struct _CERT_SIMPLE_CHAIN {
    DWORD cbSize;
    CERT_TRUST_STATUS TrustStatus;
    DWORD cElement;
    PCERT_CHAIN_ELEMENT *rgpElement;
    PCERT_TRUST_LIST_INFO pTrustListInfo;
    BOOL fHasRevocationFreshnessTime;
    DWORD dwRevocationFreshnessTime;
};

struct _CERT_TRUST_LIST_INFO {
    DWORD cbSize;
    PCTL_ENTRY pCtlEntry;
    PCCTL_CONTEXT pCtlContext;
};

typedef struct _CERT_CHAIN_CONTEXT _CERT_CHAIN_CONTEXT, *P_CERT_CHAIN_CONTEXT;

typedef struct _CERT_CHAIN_CONTEXT CERT_CHAIN_CONTEXT;

typedef CERT_CHAIN_CONTEXT *PCCERT_CHAIN_CONTEXT;

struct _CERT_CHAIN_CONTEXT {
    DWORD cbSize;
    CERT_TRUST_STATUS TrustStatus;
    DWORD cChain;
    PCERT_SIMPLE_CHAIN *rgpChain;
    DWORD cLowerQualityChainContext;
    PCCERT_CHAIN_CONTEXT *rgpLowerQualityChainContext;
    BOOL fHasRevocationFreshnessTime;
    DWORD dwRevocationFreshnessTime;
    DWORD dwCreateFlags;
    GUID ChainId;
};

typedef ULONG_PTR HCRYPTPROV_LEGACY;

typedef struct tm tm, *Ptm;

struct tm {
    int tm_sec;
    int tm_min;
    int tm_hour;
    int tm_mday;
    int tm_mon;
    int tm_year;
    int tm_wday;
    int tm_yday;
    int tm_isdst;
};

typedef long clock_t;

typedef ULONG_PTR SIZE_T;

typedef ULONG_PTR *PDWORD_PTR;

typedef longlong INT_PTR;

typedef struct HFONT__ HFONT__, *PHFONT__;

typedef struct HFONT__ *HFONT;

struct HFONT__ {
    int unused;
};

typedef struct tagPOINT *LPPOINT;

typedef struct HKEY__ HKEY__, *PHKEY__;

struct HKEY__ {
    int unused;
};


/* WARNING! conflicting data type names: /WinDef.h/UCHAR - /winsmcrd.h/UCHAR */

typedef UCHAR *PUCHAR;

typedef DWORD *LPDWORD;

typedef DWORD *PDWORD;

typedef struct HDC__ HDC__, *PHDC__;

struct HDC__ {
    int unused;
};

typedef struct HMONITOR__ HMONITOR__, *PHMONITOR__;

typedef struct HMONITOR__ *HMONITOR;

struct HMONITOR__ {
    int unused;
};

typedef uint *PUINT;

typedef HINSTANCE HMODULE;

typedef HANDLE HLOCAL;

typedef long *LPLONG;

typedef struct HMENU__ HMENU__, *PHMENU__;

typedef struct HMENU__ *HMENU;

struct HMENU__ {
    int unused;
};

typedef struct _FILETIME *LPFILETIME;

typedef INT_PTR (*FARPROC)(void);

typedef struct HDC__ *HDC;

typedef HANDLE *LPHANDLE;

typedef struct HKEY__ *HKEY;

typedef HKEY *PHKEY;

typedef int INT;

typedef WORD ATOM;

typedef struct tagRECT *LPRECT;

typedef HANDLE HGLOBAL;

typedef BOOL *LPBOOL;

typedef void *HGDIOBJ;

typedef void *LPCVOID;

typedef struct IMAGE_RESOURCE_DIRECTORY_ENTRY IMAGE_RESOURCE_DIRECTORY_ENTRY, *PIMAGE_RESOURCE_DIRECTORY_ENTRY;

typedef union IMAGE_RESOURCE_DIRECTORY_ENTRY_NameUnion IMAGE_RESOURCE_DIRECTORY_ENTRY_NameUnion, *PIMAGE_RESOURCE_DIRECTORY_ENTRY_NameUnion;

typedef struct IMAGE_RESOURCE_DIRECTORY_ENTRY_NameStruct IMAGE_RESOURCE_DIRECTORY_ENTRY_NameStruct, *PIMAGE_RESOURCE_DIRECTORY_ENTRY_NameStruct;

struct IMAGE_RESOURCE_DIRECTORY_ENTRY_NameStruct {
    dword NameOffset:31;
    dword NameIsString:1;
};

union IMAGE_RESOURCE_DIRECTORY_ENTRY_NameUnion {
    struct IMAGE_RESOURCE_DIRECTORY_ENTRY_NameStruct IMAGE_RESOURCE_DIRECTORY_ENTRY_NameStruct;
    dword Name;
    word Id;
};

struct IMAGE_RESOURCE_DIRECTORY_ENTRY {
    union IMAGE_RESOURCE_DIRECTORY_ENTRY_NameUnion NameUnion;
    union IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryUnion DirectoryUnion;
};

typedef struct IMAGE_OPTIONAL_HEADER64 IMAGE_OPTIONAL_HEADER64, *PIMAGE_OPTIONAL_HEADER64;

typedef struct IMAGE_DATA_DIRECTORY IMAGE_DATA_DIRECTORY, *PIMAGE_DATA_DIRECTORY;

struct IMAGE_DATA_DIRECTORY {
    ImageBaseOffset32 VirtualAddress;
    dword Size;
};

struct IMAGE_OPTIONAL_HEADER64 {
    word Magic;
    byte MajorLinkerVersion;
    byte MinorLinkerVersion;
    dword SizeOfCode;
    dword SizeOfInitializedData;
    dword SizeOfUninitializedData;
    ImageBaseOffset32 AddressOfEntryPoint;
    ImageBaseOffset32 BaseOfCode;
    pointer64 ImageBase;
    dword SectionAlignment;
    dword FileAlignment;
    word MajorOperatingSystemVersion;
    word MinorOperatingSystemVersion;
    word MajorImageVersion;
    word MinorImageVersion;
    word MajorSubsystemVersion;
    word MinorSubsystemVersion;
    dword Win32VersionValue;
    dword SizeOfImage;
    dword SizeOfHeaders;
    dword CheckSum;
    word Subsystem;
    word DllCharacteristics;
    qword SizeOfStackReserve;
    qword SizeOfStackCommit;
    qword SizeOfHeapReserve;
    qword SizeOfHeapCommit;
    dword LoaderFlags;
    dword NumberOfRvaAndSizes;
    struct IMAGE_DATA_DIRECTORY DataDirectory[16];
};

typedef struct IMAGE_SECTION_HEADER IMAGE_SECTION_HEADER, *PIMAGE_SECTION_HEADER;

typedef union Misc Misc, *PMisc;

typedef enum SectionFlags {
    IMAGE_SCN_TYPE_NO_PAD=8,
    IMAGE_SCN_RESERVED_0001=16,
    IMAGE_SCN_CNT_CODE=32,
    IMAGE_SCN_CNT_INITIALIZED_DATA=64,
    IMAGE_SCN_CNT_UNINITIALIZED_DATA=128,
    IMAGE_SCN_LNK_OTHER=256,
    IMAGE_SCN_LNK_INFO=512,
    IMAGE_SCN_RESERVED_0040=1024,
    IMAGE_SCN_LNK_REMOVE=2048,
    IMAGE_SCN_LNK_COMDAT=4096,
    IMAGE_SCN_GPREL=32768,
    IMAGE_SCN_MEM_16BIT=131072,
    IMAGE_SCN_MEM_PURGEABLE=131072,
    IMAGE_SCN_MEM_LOCKED=262144,
    IMAGE_SCN_MEM_PRELOAD=524288,
    IMAGE_SCN_ALIGN_1BYTES=1048576,
    IMAGE_SCN_ALIGN_2BYTES=2097152,
    IMAGE_SCN_ALIGN_4BYTES=3145728,
    IMAGE_SCN_ALIGN_8BYTES=4194304,
    IMAGE_SCN_ALIGN_16BYTES=5242880,
    IMAGE_SCN_ALIGN_32BYTES=6291456,
    IMAGE_SCN_ALIGN_64BYTES=7340032,
    IMAGE_SCN_ALIGN_128BYTES=8388608,
    IMAGE_SCN_ALIGN_256BYTES=9437184,
    IMAGE_SCN_ALIGN_512BYTES=10485760,
    IMAGE_SCN_ALIGN_1024BYTES=11534336,
    IMAGE_SCN_ALIGN_2048BYTES=12582912,
    IMAGE_SCN_ALIGN_4096BYTES=13631488,
    IMAGE_SCN_ALIGN_8192BYTES=14680064,
    IMAGE_SCN_LNK_NRELOC_OVFL=16777216,
    IMAGE_SCN_MEM_DISCARDABLE=33554432,
    IMAGE_SCN_MEM_NOT_CACHED=67108864,
    IMAGE_SCN_MEM_NOT_PAGED=134217728,
    IMAGE_SCN_MEM_SHARED=268435456,
    IMAGE_SCN_MEM_EXECUTE=536870912,
    IMAGE_SCN_MEM_READ=1073741824,
    IMAGE_SCN_MEM_WRITE=2147483648
} SectionFlags;

union Misc {
    dword PhysicalAddress;
    dword VirtualSize;
};

struct IMAGE_SECTION_HEADER {
    char Name[8];
    union Misc Misc;
    ImageBaseOffset32 VirtualAddress;
    dword SizeOfRawData;
    dword PointerToRawData;
    dword PointerToRelocations;
    dword PointerToLinenumbers;
    word NumberOfRelocations;
    word NumberOfLinenumbers;
    enum SectionFlags Characteristics;
};

typedef struct IMAGE_NT_HEADERS64 IMAGE_NT_HEADERS64, *PIMAGE_NT_HEADERS64;

typedef struct IMAGE_FILE_HEADER IMAGE_FILE_HEADER, *PIMAGE_FILE_HEADER;

struct IMAGE_FILE_HEADER {
    word Machine; /* 34404 */
    word NumberOfSections;
    dword TimeDateStamp;
    dword PointerToSymbolTable;
    dword NumberOfSymbols;
    word SizeOfOptionalHeader;
    word Characteristics;
};

struct IMAGE_NT_HEADERS64 {
    char Signature[4];
    struct IMAGE_FILE_HEADER FileHeader;
    struct IMAGE_OPTIONAL_HEADER64 OptionalHeader;
};

typedef struct _IMAGE_RUNTIME_FUNCTION_ENTRY _IMAGE_RUNTIME_FUNCTION_ENTRY, *P_IMAGE_RUNTIME_FUNCTION_ENTRY;

struct _IMAGE_RUNTIME_FUNCTION_ENTRY {
    ImageBaseOffset32 BeginAddress;
    dword EndAddress; /* Apply ImageBaseOffset32 to see reference */
    ImageBaseOffset32 UnwindInfoAddressOrData;
};

typedef struct IMAGE_BASE_RELOCATION IMAGE_BASE_RELOCATION, *PIMAGE_BASE_RELOCATION;

struct IMAGE_BASE_RELOCATION {
    dword VirtualAddress;
    dword SizeOfBlock;
};

typedef struct IMAGE_THUNK_DATA64 IMAGE_THUNK_DATA64, *PIMAGE_THUNK_DATA64;

struct IMAGE_THUNK_DATA64 {
    qword StartAddressOfRawData;
    qword EndAddressOfRawData;
    qword AddressOfIndex;
    qword AddressOfCallBacks;
    dword SizeOfZeroFill;
    dword Characteristics;
};

typedef struct IMAGE_RESOURCE_DATA_ENTRY IMAGE_RESOURCE_DATA_ENTRY, *PIMAGE_RESOURCE_DATA_ENTRY;

struct IMAGE_RESOURCE_DATA_ENTRY {
    dword OffsetToData;
    dword Size;
    dword CodePage;
    dword Reserved;
};

typedef enum IMAGE_GUARD_FLAGS {
    IMAGE_GUARD_CF_INSTRUMENTED=256,
    IMAGE_GUARD_CFW_INSTRUMENTED=512,
    IMAGE_GUARD_CF_FUNCTION_TABLE_PRESENT=1024,
    IMAGE_GUARD_SECURITY_COOKIE_UNUSED=2048,
    IMAGE_GUARD_PROTECT_DELAYLOAD_IAT=4096,
    IMAGE_GUARD_DELAYLOAD_IAT_IN_ITS_OWN_SECTION=8192,
    IMAGE_GUARD_CF_EXPORT_SUPPRESSION_INFO_PRESENT=16384,
    IMAGE_GUARD_CF_ENABLE_EXPORT_SUPPRESSION=32768,
    IMAGE_GUARD_CF_LONGJUMP_TABLE_PRESENT=65536,
    IMAGE_GUARD_RF_INSTRUMENTED=131072,
    IMAGE_GUARD_RF_ENABLE=262144,
    IMAGE_GUARD_RF_STRICT=524288,
    IMAGE_GUARD_CF_FUNCTION_TABLE_SIZE_MASK_1=268435456,
    IMAGE_GUARD_CF_FUNCTION_TABLE_SIZE_MASK_2=536870912,
    IMAGE_GUARD_CF_FUNCTION_TABLE_SIZE_MASK_4=1073741824,
    IMAGE_GUARD_CF_FUNCTION_TABLE_SIZE_MASK_8=2147483648
} IMAGE_GUARD_FLAGS;

typedef struct IMAGE_RESOURCE_DIRECTORY IMAGE_RESOURCE_DIRECTORY, *PIMAGE_RESOURCE_DIRECTORY;

struct IMAGE_RESOURCE_DIRECTORY {
    dword Characteristics;
    dword TimeDateStamp;
    word MajorVersion;
    word MinorVersion;
    word NumberOfNamedEntries;
    word NumberOfIdEntries;
};

typedef struct IMAGE_LOAD_CONFIG_CODE_INTEGRITY IMAGE_LOAD_CONFIG_CODE_INTEGRITY, *PIMAGE_LOAD_CONFIG_CODE_INTEGRITY;

struct IMAGE_LOAD_CONFIG_CODE_INTEGRITY {
    word Flags;
    word Catalog;
    dword CatalogOffset;
    dword Reserved;
};

typedef struct IMAGE_DEBUG_DIRECTORY IMAGE_DEBUG_DIRECTORY, *PIMAGE_DEBUG_DIRECTORY;

struct IMAGE_DEBUG_DIRECTORY {
    dword Characteristics;
    dword TimeDateStamp;
    word MajorVersion;
    word MinorVersion;
    dword Type;
    dword SizeOfData;
    dword AddressOfRawData;
    dword PointerToRawData;
};

typedef struct IMAGE_LOAD_CONFIG_DIRECTORY64 IMAGE_LOAD_CONFIG_DIRECTORY64, *PIMAGE_LOAD_CONFIG_DIRECTORY64;

struct IMAGE_LOAD_CONFIG_DIRECTORY64 {
    dword Size;
    dword TimeDateStamp;
    word MajorVersion;
    word MinorVersion;
    dword GlobalFlagsClear;
    dword GlobalFlagsSet;
    dword CriticalSectionDefaultTimeout;
    qword DeCommitFreeBlockThreshold;
    qword DeCommitTotalFreeThreshold;
    pointer64 LockPrefixTable;
    qword MaximumAllocationSize;
    qword VirtualMemoryThreshold;
    qword ProcessAffinityMask;
    dword ProcessHeapFlags;
    word CsdVersion;
    word DependentLoadFlags;
    pointer64 EditList;
    pointer64 SecurityCookie;
    pointer64 SEHandlerTable;
    qword SEHandlerCount;
    pointer64 GuardCFCCheckFunctionPointer;
    pointer64 GuardCFDispatchFunctionPointer;
    pointer64 GuardCFFunctionTable;
    qword GuardCFFunctionCount;
    enum IMAGE_GUARD_FLAGS GuardFlags;
    struct IMAGE_LOAD_CONFIG_CODE_INTEGRITY CodeIntegrity;
    pointer64 GuardAddressTakenIatEntryTable;
    qword GuardAddressTakenIatEntryCount;
    pointer64 GuardLongJumpTargetTable;
    qword GuardLongJumpTargetCount;
    pointer64 DynamicValueRelocTable;
    pointer64 CHPEMetadataPointer;
    pointer64 GuardRFFailureRoutine;
    pointer64 GuardRFFailureRoutineFunctionPointer;
    dword DynamicValueRelocTableOffset;
    word DynamicValueRelocTableSection;
    word Reserved1;
    pointer64 GuardRFVerifyStackPointerFunctionPointer;
    dword HotPatchTableOffset;
    dword Reserved2;
    qword Reserved3;
};

typedef LONG LSTATUS;

typedef ACCESS_MASK REGSAM;

typedef struct tMIXERCONTROLDETAILS tMIXERCONTROLDETAILS, *PtMIXERCONTROLDETAILS;

typedef union _union_1121 _union_1121, *P_union_1121;

union _union_1121 {
    HWND hwndOwner;
    DWORD cMultipleItems;
};

struct tMIXERCONTROLDETAILS {
    DWORD cbStruct;
    DWORD dwControlID;
    DWORD cChannels;
    union _union_1121 u;
    DWORD cbDetails;
    LPVOID paDetails;
};

typedef union _union_1110 _union_1110, *P_union_1110;

union _union_1110 {
    DWORD cSteps;
    DWORD cbCustomData;
    DWORD dwReserved[6];
};

typedef struct tagMIXERCAPSA tagMIXERCAPSA, *PtagMIXERCAPSA;

typedef UINT MMVERSION;

struct tagMIXERCAPSA {
    WORD wMid;
    WORD wPid;
    MMVERSION vDriverVersion;
    CHAR szPname[32];
    DWORD fdwSupport;
    DWORD cDestinations;
};

typedef struct tagMIXERCONTROLA tagMIXERCONTROLA, *PtagMIXERCONTROLA;

typedef union _union_1107 _union_1107, *P_union_1107;

typedef struct _struct_1108 _struct_1108, *P_struct_1108;

typedef struct _struct_1109 _struct_1109, *P_struct_1109;

struct _struct_1108 {
    LONG lMinimum;
    LONG lMaximum;
};

struct _struct_1109 {
    DWORD dwMinimum;
    DWORD dwMaximum;
};

union _union_1107 {
    struct _struct_1108 s;
    struct _struct_1109 s2;
    DWORD dwReserved[6];
};

struct tagMIXERCONTROLA {
    DWORD cbStruct;
    DWORD dwControlID;
    DWORD dwControlType;
    DWORD fdwControl;
    DWORD cMultipleItems;
    CHAR szShortName[16];
    CHAR szName[64];
    union _union_1107 Bounds;
    union _union_1110 Metrics;
};

typedef struct tagMIXERLINEA tagMIXERLINEA, *PtagMIXERLINEA;

typedef struct tagMIXERLINEA *LPMIXERLINEA;

typedef struct _struct_1103 _struct_1103, *P_struct_1103;

struct _struct_1103 {
    DWORD dwType;
    DWORD dwDeviceID;
    WORD wMid;
    WORD wPid;
    MMVERSION vDriverVersion;
    CHAR szPname[32];
};

struct tagMIXERLINEA {
    DWORD cbStruct;
    DWORD dwDestination;
    DWORD dwSource;
    DWORD dwLineID;
    DWORD fdwLine;
    DWORD_PTR dwUser;
    DWORD dwComponentType;
    DWORD cChannels;
    DWORD cConnections;
    DWORD cControls;
    CHAR szShortName[16];
    CHAR szName[64];
    struct _struct_1103 Target;
};

typedef struct tagMIXERLINECONTROLSA tagMIXERLINECONTROLSA, *PtagMIXERLINECONTROLSA;

typedef union _union_1117 _union_1117, *P_union_1117;

typedef struct tagMIXERCONTROLA *LPMIXERCONTROLA;

union _union_1117 {
    DWORD dwControlID;
    DWORD dwControlType;
};

struct tagMIXERLINECONTROLSA {
    DWORD cbStruct;
    DWORD dwLineID;
    union _union_1117 u;
    DWORD cControls;
    DWORD cbmxctrl;
    LPMIXERCONTROLA pamxctrl;
};

typedef struct HMIXER__ HMIXER__, *PHMIXER__;

struct HMIXER__ {
    int unused;
};

typedef struct tagMIXERLINECONTROLSA *LPMIXERLINECONTROLSA;

typedef struct HMIXER__ *HMIXER;

typedef UINT MMRESULT;

typedef struct HMIXEROBJ__ HMIXEROBJ__, *PHMIXEROBJ__;

typedef struct HMIXEROBJ__ *HMIXEROBJ;

struct HMIXEROBJ__ {
    int unused;
};

typedef HMIXER *LPHMIXER;

typedef struct tMIXERCONTROLDETAILS *LPMIXERCONTROLDETAILS;

typedef struct tagMIXERCAPSA *LPMIXERCAPSA;

typedef struct MRECmpImpl MRECmpImpl, *PMRECmpImpl;

struct MRECmpImpl { /* PlaceHolder Structure */
};

typedef struct IErrorInfo IErrorInfo, *PIErrorInfo;

struct IErrorInfo { /* PlaceHolder Structure */
};

typedef struct _Mbstatet _Mbstatet, *P_Mbstatet;

struct _Mbstatet { /* PlaceHolder Structure */
};

typedef struct MemBlock MemBlock, *PMemBlock;

struct MemBlock { /* PlaceHolder Structure */
};

typedef struct CAtlBaseModule CAtlBaseModule, *PCAtlBaseModule;

struct CAtlBaseModule { /* PlaceHolder Structure */
};

typedef struct basic_ostream<wchar_t,struct_std::char_traits<wchar_t>_> basic_ostream<wchar_t,struct_std::char_traits<wchar_t>_>, *Pbasic_ostream<wchar_t,struct_std::char_traits<wchar_t>_>;

struct basic_ostream<wchar_t,struct_std::char_traits<wchar_t>_> { /* PlaceHolder Structure */
};

typedef struct basic_streambuf<wchar_t,std::char_traits<wchar_t>_> basic_streambuf<wchar_t,std::char_traits<wchar_t>_>, *Pbasic_streambuf<wchar_t,std::char_traits<wchar_t>_>;

struct basic_streambuf<wchar_t,std::char_traits<wchar_t>_> { /* PlaceHolder Structure */
};

typedef struct basic_istream<char,struct_std::char_traits<char>_> basic_istream<char,struct_std::char_traits<char>_>, *Pbasic_istream<char,struct_std::char_traits<char>_>;

struct basic_istream<char,struct_std::char_traits<char>_> { /* PlaceHolder Structure */
};

typedef struct codecvt_base codecvt_base, *Pcodecvt_base;

struct codecvt_base { /* PlaceHolder Structure */
};

typedef struct basic_ostream<wchar_t,std::char_traits<wchar_t>_> basic_ostream<wchar_t,std::char_traits<wchar_t>_>, *Pbasic_ostream<wchar_t,std::char_traits<wchar_t>_>;

struct basic_ostream<wchar_t,std::char_traits<wchar_t>_> { /* PlaceHolder Structure */
};

typedef struct basic_streambuf<wchar_t,struct_std::char_traits<wchar_t>_> basic_streambuf<wchar_t,struct_std::char_traits<wchar_t>_>, *Pbasic_streambuf<wchar_t,struct_std::char_traits<wchar_t>_>;

struct basic_streambuf<wchar_t,struct_std::char_traits<wchar_t>_> { /* PlaceHolder Structure */
};

typedef struct locale locale, *Plocale;

struct locale { /* PlaceHolder Structure */
};

typedef struct basic_istream<char,std::char_traits<char>_> basic_istream<char,std::char_traits<char>_>, *Pbasic_istream<char,std::char_traits<char>_>;

struct basic_istream<char,std::char_traits<char>_> { /* PlaceHolder Structure */
};

typedef struct _Fac_tidy_reg_t _Fac_tidy_reg_t, *P_Fac_tidy_reg_t;

struct _Fac_tidy_reg_t { /* PlaceHolder Structure */
};

typedef struct basic_streambuf<char,std::char_traits<char>_> basic_streambuf<char,std::char_traits<char>_>, *Pbasic_streambuf<char,std::char_traits<char>_>;

struct basic_streambuf<char,std::char_traits<char>_> { /* PlaceHolder Structure */
};

typedef struct basic_iostream<char,std::char_traits<char>_> basic_iostream<char,std::char_traits<char>_>, *Pbasic_iostream<char,std::char_traits<char>_>;

struct basic_iostream<char,std::char_traits<char>_> { /* PlaceHolder Structure */
};

typedef struct basic_streambuf<char,struct_std::char_traits<char>_> basic_streambuf<char,struct_std::char_traits<char>_>, *Pbasic_streambuf<char,struct_std::char_traits<char>_>;

struct basic_streambuf<char,struct_std::char_traits<char>_> { /* PlaceHolder Structure */
};

typedef struct _Facet_base _Facet_base, *P_Facet_base;

struct _Facet_base { /* PlaceHolder Structure */
};

typedef struct basic_iostream<wchar_t,std::char_traits<wchar_t>_> basic_iostream<wchar_t,std::char_traits<wchar_t>_>, *Pbasic_iostream<wchar_t,std::char_traits<wchar_t>_>;

struct basic_iostream<wchar_t,std::char_traits<wchar_t>_> { /* PlaceHolder Structure */
};

typedef struct basic_ostream<char,struct_std::char_traits<char>_> basic_ostream<char,struct_std::char_traits<char>_>, *Pbasic_ostream<char,struct_std::char_traits<char>_>;

struct basic_ostream<char,struct_std::char_traits<char>_> { /* PlaceHolder Structure */
};

typedef struct codecvt<char,char,_Mbstatet> codecvt<char,char,_Mbstatet>, *Pcodecvt<char,char,_Mbstatet>;

struct codecvt<char,char,_Mbstatet> { /* PlaceHolder Structure */
};

typedef struct fpos<_Mbstatet> fpos<_Mbstatet>, *Pfpos<_Mbstatet>;

struct fpos<_Mbstatet> { /* PlaceHolder Structure */
};

typedef struct basic_ios<wchar_t,std::char_traits<wchar_t>_> basic_ios<wchar_t,std::char_traits<wchar_t>_>, *Pbasic_ios<wchar_t,std::char_traits<wchar_t>_>;

struct basic_ios<wchar_t,std::char_traits<wchar_t>_> { /* PlaceHolder Structure */
};

typedef struct basic_ios<char,std::char_traits<char>_> basic_ios<char,std::char_traits<char>_>, *Pbasic_ios<char,std::char_traits<char>_>;

struct basic_ios<char,std::char_traits<char>_> { /* PlaceHolder Structure */
};

typedef struct basic_ostream<char,std::char_traits<char>_> basic_ostream<char,std::char_traits<char>_>, *Pbasic_ostream<char,std::char_traits<char>_>;

struct basic_ostream<char,std::char_traits<char>_> { /* PlaceHolder Structure */
};

typedef struct _Lockit _Lockit, *P_Lockit;

struct _Lockit { /* PlaceHolder Structure */
};

typedef struct _Locimp _Locimp, *P_Locimp;

struct _Locimp { /* PlaceHolder Structure */
};

typedef struct facet facet, *Pfacet;

struct facet { /* PlaceHolder Structure */
};

typedef struct id id, *Pid;

struct id { /* PlaceHolder Structure */
};

typedef struct _AsyncTaskCollection _AsyncTaskCollection, *P_AsyncTaskCollection;

struct _AsyncTaskCollection { /* PlaceHolder Structure */
};

typedef int (*_onexit_t)(void);

typedef struct IUnknown *LPUNKNOWN;

