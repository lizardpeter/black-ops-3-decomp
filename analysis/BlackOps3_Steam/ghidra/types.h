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
typedef unsigned int    undefined3;
typedef unsigned int    undefined4;
typedef unsigned long long    undefined5;
typedef unsigned long long    undefined6;
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

typedef struct _s_HandlerType _s_HandlerType, *P_s_HandlerType;

struct _s_HandlerType {
    uint adjectives;
    ImageBaseOffset32 dispType;
    int dispCatchObj;
    ImageBaseOffset32 dispOfHandler;
    dword dispFrame;
};

typedef struct _s_IPToStateMapEntry _s_IPToStateMapEntry, *P_s_IPToStateMapEntry;

typedef struct _s_IPToStateMapEntry IPToStateMapEntry;

typedef int __ehstate_t;

struct _s_IPToStateMapEntry {
    ImageBaseOffset32 Ip;
    __ehstate_t state;
};

typedef struct _s_UnwindMapEntry _s_UnwindMapEntry, *P_s_UnwindMapEntry;

typedef struct _s_UnwindMapEntry UnwindMapEntry;

struct _s_UnwindMapEntry {
    __ehstate_t toState;
    ImageBaseOffset32 action;
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

typedef struct _s_FuncInfo _s_FuncInfo, *P_s_FuncInfo;

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

typedef struct type_info type_info, *Ptype_info;

struct type_info { /* PlaceHolder Class Structure */
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

typedef struct _s_TryBlockMapEntry _s_TryBlockMapEntry, *P_s_TryBlockMapEntry;

typedef struct _s_TryBlockMapEntry TryBlockMapEntry;

struct _s_TryBlockMapEntry {
    __ehstate_t tryLow;
    __ehstate_t tryHigh;
    __ehstate_t catchHigh;
    int nCatches;
    ImageBaseOffset32 dispHandlerArray;
};

typedef struct _s__RTTICompleteObjectLocator _s__RTTICompleteObjectLocator, *P_s__RTTICompleteObjectLocator;

typedef struct _s__RTTICompleteObjectLocator RTTICompleteObjectLocator;

struct _s__RTTICompleteObjectLocator {
    dword signature;
    dword offset; /* offset of vbtable within class */
    dword cdOffset; /* constructor displacement offset */
    ImageBaseOffset32 pTypeDescriptor; /* ref to TypeDescriptor (RTTI 0) for class */
    ImageBaseOffset32 pClassDescriptor; /* ref to ClassHierarchyDescriptor (RTTI 3) */
};

typedef struct _s_HandlerType HandlerType;

typedef struct _s_FuncInfo FuncInfo;

typedef struct _cpinfo _cpinfo, *P_cpinfo;

typedef uint UINT;

typedef uchar BYTE;

struct _cpinfo {
    UINT MaxCharSize;
    BYTE DefaultChar[2];
    BYTE LeadByte[12];
};

typedef struct _nlsversioninfo _nlsversioninfo, *P_nlsversioninfo;

typedef struct _nlsversioninfo *LPNLSVERSIONINFO;

typedef ulong DWORD;

struct _nlsversioninfo {
    DWORD dwNLSVersionInfoSize;
    DWORD dwNLSVersion;
    DWORD dwDefinedVersion;
};

typedef struct _cpinfo *LPCPINFO;

typedef DWORD LCTYPE;

typedef struct _SYSTEM_INFO _SYSTEM_INFO, *P_SYSTEM_INFO;

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

typedef struct _SYSTEMTIME _SYSTEMTIME, *P_SYSTEMTIME;

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

typedef struct _TIME_ZONE_INFORMATION _TIME_ZONE_INFORMATION, *P_TIME_ZONE_INFORMATION;

typedef long LONG;

typedef wchar_t WCHAR;

typedef struct _SYSTEMTIME SYSTEMTIME;

struct _TIME_ZONE_INFORMATION {
    LONG Bias;
    WCHAR StandardName[32];
    SYSTEMTIME StandardDate;
    LONG StandardBias;
    WCHAR DaylightName[32];
    SYSTEMTIME DaylightDate;
    LONG DaylightBias;
};

typedef struct _WIN32_FIND_DATAW _WIN32_FIND_DATAW, *P_WIN32_FIND_DATAW;

typedef struct _WIN32_FIND_DATAW *LPWIN32_FIND_DATAW;

typedef struct _FILETIME _FILETIME, *P_FILETIME;

typedef struct _FILETIME FILETIME;

struct _FILETIME {
    DWORD dwLowDateTime;
    DWORD dwHighDateTime;
};

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

typedef struct _WIN32_FIND_DATAA _WIN32_FIND_DATAA, *P_WIN32_FIND_DATAA;

typedef char CHAR;

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

typedef struct _BY_HANDLE_FILE_INFORMATION _BY_HANDLE_FILE_INFORMATION, *P_BY_HANDLE_FILE_INFORMATION;

struct _BY_HANDLE_FILE_INFORMATION {
    DWORD dwFileAttributes;
    FILETIME ftCreationTime;
    FILETIME ftLastAccessTime;
    FILETIME ftLastWriteTime;
    DWORD dwVolumeSerialNumber;
    DWORD nFileSizeHigh;
    DWORD nFileSizeLow;
    DWORD nNumberOfLinks;
    DWORD nFileIndexHigh;
    DWORD nFileIndexLow;
};

typedef struct _SECURITY_ATTRIBUTES _SECURITY_ATTRIBUTES, *P_SECURITY_ATTRIBUTES;

typedef struct _SECURITY_ATTRIBUTES *LPSECURITY_ATTRIBUTES;

typedef int BOOL;

struct _SECURITY_ATTRIBUTES {
    DWORD nLength;
    LPVOID lpSecurityDescriptor;
    BOOL bInheritHandle;
};

typedef struct _STARTUPINFOA _STARTUPINFOA, *P_STARTUPINFOA;

typedef CHAR *LPSTR;

typedef BYTE *LPBYTE;

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

typedef enum _FINDEX_INFO_LEVELS {
    FindExInfoStandard=0,
    FindExInfoBasic=1,
    FindExInfoMaxInfoLevel=2
} _FINDEX_INFO_LEVELS;

typedef enum _FINDEX_INFO_LEVELS FINDEX_INFO_LEVELS;

typedef enum _GET_FILEEX_INFO_LEVELS {
    GetFileExInfoStandard=0,
    GetFileExMaxInfoLevel=1
} _GET_FILEEX_INFO_LEVELS;

typedef enum _GET_FILEEX_INFO_LEVELS GET_FILEEX_INFO_LEVELS;

typedef struct _PROCESS_INFORMATION _PROCESS_INFORMATION, *P_PROCESS_INFORMATION;

typedef struct _PROCESS_INFORMATION *LPPROCESS_INFORMATION;

struct _PROCESS_INFORMATION {
    HANDLE hProcess;
    HANDLE hThread;
    DWORD dwProcessId;
    DWORD dwThreadId;
};

typedef enum _FINDEX_SEARCH_OPS {
    FindExSearchNameMatch=0,
    FindExSearchLimitToDirectories=1,
    FindExSearchLimitToDevices=2,
    FindExSearchMaxSearchOp=3
} _FINDEX_SEARCH_OPS;

typedef DWORD (*PTHREAD_START_ROUTINE)(LPVOID);

typedef struct _EXCEPTION_POINTERS _EXCEPTION_POINTERS, *P_EXCEPTION_POINTERS;

typedef LONG (*PTOP_LEVEL_EXCEPTION_FILTER)(struct _EXCEPTION_POINTERS *);

typedef PTOP_LEVEL_EXCEPTION_FILTER LPTOP_LEVEL_EXCEPTION_FILTER;

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

typedef ulonglong ULONGLONG;

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

typedef struct _MEMORYSTATUSEX _MEMORYSTATUSEX, *P_MEMORYSTATUSEX;

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

typedef struct _SYSTEM_INFO *LPSYSTEM_INFO;

typedef struct _TIME_ZONE_INFORMATION TIME_ZONE_INFORMATION;

typedef struct _TIME_ZONE_INFORMATION *LPTIME_ZONE_INFORMATION;

typedef struct _STARTUPINFOW _STARTUPINFOW, *P_STARTUPINFOW;

typedef WCHAR *LPWSTR;

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

typedef union _RTL_RUN_ONCE _RTL_RUN_ONCE, *P_RTL_RUN_ONCE;

typedef union _RTL_RUN_ONCE *PRTL_RUN_ONCE;

typedef PRTL_RUN_ONCE PINIT_ONCE;

typedef BOOL (*PINIT_ONCE_FN)(PINIT_ONCE, PVOID, PVOID *);

union _RTL_RUN_ONCE {
    PVOID Ptr;
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

typedef PTHREAD_START_ROUTINE LPTHREAD_START_ROUTINE;

typedef struct _MEMORYSTATUSEX *LPMEMORYSTATUSEX;

typedef enum _FINDEX_SEARCH_OPS FINDEX_SEARCH_OPS;

typedef struct _WIN32_FIND_DATAA *LPWIN32_FIND_DATAA;

typedef struct _STARTUPINFOA *LPSTARTUPINFOA;

typedef struct _BY_HANDLE_FILE_INFORMATION *LPBY_HANDLE_FILE_INFORMATION;

typedef struct _RTL_CRITICAL_SECTION _RTL_CRITICAL_SECTION, *P_RTL_CRITICAL_SECTION;

typedef struct _RTL_CRITICAL_SECTION *PRTL_CRITICAL_SECTION;

typedef PRTL_CRITICAL_SECTION LPCRITICAL_SECTION;

typedef struct _RTL_CRITICAL_SECTION_DEBUG _RTL_CRITICAL_SECTION_DEBUG, *P_RTL_CRITICAL_SECTION_DEBUG;

typedef struct _RTL_CRITICAL_SECTION_DEBUG *PRTL_CRITICAL_SECTION_DEBUG;

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

typedef void (*LPOVERLAPPED_COMPLETION_ROUTINE)(DWORD, DWORD, LPOVERLAPPED);

typedef struct _SYSTEMTIME *LPSYSTEMTIME;

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

typedef struct DotNetPdbInfo DotNetPdbInfo, *PDotNetPdbInfo;

struct DotNetPdbInfo {
    char signature[4];
    GUID guid;
    dword age;
    char pdbpath[29];
};

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

typedef enum _MF_ATTRIBUTES_MATCH_TYPE {
    MF_ATTRIBUTES_MATCH_OUR_ITEMS=0,
    MF_ATTRIBUTES_MATCH_THEIR_ITEMS=1,
    MF_ATTRIBUTES_MATCH_ALL_ITEMS=2,
    MF_ATTRIBUTES_MATCH_INTERSECTION=3,
    MF_ATTRIBUTES_MATCH_SMALLER=4
} _MF_ATTRIBUTES_MATCH_TYPE;

typedef struct IMFAttributesVtbl IMFAttributesVtbl, *PIMFAttributesVtbl;

typedef struct IMFAttributes IMFAttributes, *PIMFAttributes;


/* WARNING! conflicting data type names: /guiddef.h/GUID - /GUID */

typedef GUID IID;

typedef struct tagPROPVARIANT tagPROPVARIANT, *PtagPROPVARIANT;

typedef struct tagPROPVARIANT PROPVARIANT;

typedef enum _MF_ATTRIBUTES_MATCH_TYPE MF_ATTRIBUTES_MATCH_TYPE;

typedef uint UINT32;

typedef ulonglong UINT64;

typedef uchar UINT8;

typedef WCHAR *LPCWSTR;

typedef struct IUnknown IUnknown, *PIUnknown;

typedef struct IUnknownVtbl IUnknownVtbl, *PIUnknownVtbl;

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

typedef struct IMFSampleVtbl IMFSampleVtbl, *PIMFSampleVtbl;

typedef struct IMFSample IMFSample, *PIMFSample;

typedef struct IMFMediaBuffer IMFMediaBuffer, *PIMFMediaBuffer;

typedef struct IMFMediaBufferVtbl IMFMediaBufferVtbl, *PIMFMediaBufferVtbl;

struct IMFSample {
    struct IMFSampleVtbl *lpVtbl;
};

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

typedef struct _strflt _strflt, *P_strflt;

struct _strflt {
    int sign;
    int decpt;
    int flag;
    char *mantissa;
};

typedef enum enum_3298 {
    INTRNCVT_OK=0,
    INTRNCVT_OVERFLOW=1,
    INTRNCVT_UNDERFLOW=2
} enum_3298;

typedef struct _flt _flt, *P_flt;

struct _flt {
    int flags;
    int nbytes;
    long lval;
    double dval;
};

typedef struct _strflt *STRFLT;

typedef enum enum_3298 INTRNCVT_STATUS;

typedef struct _flt *FLT;

typedef struct _Ctypevec _Ctypevec, *P_Ctypevec;

struct _Ctypevec {
    uint _Page;
    short *_Table;
    int _Delfl;
    wchar_t *_LocaleName;
};

typedef longlong fpos_t;

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

typedef struct _CONSOLE_READCONSOLE_CONTROL _CONSOLE_READCONSOLE_CONTROL, *P_CONSOLE_READCONSOLE_CONTROL;


/* WARNING! conflicting data type names: /WinDef.h/ULONG - /wtypes.h/ULONG */

struct _CONSOLE_READCONSOLE_CONTROL {
    ULONG nLength;
    ULONG nInitialChars;
    ULONG dwCtrlWakeupMask;
    ULONG dwControlKeyState;
};

typedef struct _CONSOLE_READCONSOLE_CONTROL *PCONSOLE_READCONSOLE_CONTROL;

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

typedef struct _stat64i32 _stat64i32, *P_stat64i32;

typedef uint _dev_t;

typedef ushort _ino_t;

typedef long _off_t;

typedef longlong __time64_t;

struct _stat64i32 {
    _dev_t st_dev;
    _ino_t st_ino;
    ushort st_mode;
    short st_nlink;
    short st_uid;
    short st_gid;
    _dev_t st_rdev;
    _off_t st_size;
    __time64_t st_atime;
    __time64_t st_mtime;
    __time64_t st_ctime;
};

typedef struct _stat64 _stat64, *P_stat64;

struct _stat64 {
    _dev_t st_dev;
    _ino_t st_ino;
    ushort st_mode;
    short st_nlink;
    short st_uid;
    short st_gid;
    _dev_t st_rdev;
    longlong st_size;
    __time64_t st_atime;
    __time64_t st_mtime;
    __time64_t st_ctime;
};

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

typedef ulonglong size_t;

typedef ushort wint_t;

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

typedef long __time32_t;

typedef struct threadlocaleinfostruct threadlocinfo;

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

typedef int errno_t;

typedef longlong intptr_t;

typedef struct localeinfo_struct *_locale_t;

typedef size_t rsize_t;

typedef ushort wctype_t;

typedef struct _SP_DEVICE_INTERFACE_DETAIL_DATA_W _SP_DEVICE_INTERFACE_DETAIL_DATA_W, *P_SP_DEVICE_INTERFACE_DETAIL_DATA_W;

struct _SP_DEVICE_INTERFACE_DETAIL_DATA_W {
    DWORD cbSize;
    WCHAR DevicePath[1];
};

typedef PVOID HDEVINFO;

typedef struct _SP_DEVICE_INTERFACE_DATA _SP_DEVICE_INTERFACE_DATA, *P_SP_DEVICE_INTERFACE_DATA;

struct _SP_DEVICE_INTERFACE_DATA {
    DWORD cbSize;
    GUID InterfaceClassGuid;
    DWORD Flags;
    ULONG_PTR Reserved;
};

typedef struct _SP_DEVICE_INTERFACE_DETAIL_DATA_W *PSP_DEVICE_INTERFACE_DETAIL_DATA_W;

typedef struct _SP_DEVINFO_DATA _SP_DEVINFO_DATA, *P_SP_DEVINFO_DATA;

struct _SP_DEVINFO_DATA {
    DWORD cbSize;
    GUID ClassGuid;
    DWORD DevInst;
    ULONG_PTR Reserved;
};

typedef struct _SP_DEVICE_INTERFACE_DATA *PSP_DEVICE_INTERFACE_DATA;

typedef struct _SP_DEVINFO_DATA *PSP_DEVINFO_DATA;

typedef struct tagWNDCLASSA tagWNDCLASSA, *PtagWNDCLASSA;

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

typedef struct exception exception, *Pexception;

struct exception { /* PlaceHolder Class Structure */
};

typedef struct ctype<char> ctype<char>, *Pctype<char>;

struct ctype<char> { /* PlaceHolder Class Structure */
};

typedef struct basic_filebuf<char,std::char_traits<char>_> basic_filebuf<char,std::char_traits<char>_>, *Pbasic_filebuf<char,std::char_traits<char>_>;

struct basic_filebuf<char,std::char_traits<char>_> { /* PlaceHolder Class Structure */
};

typedef struct _System_error_category _System_error_category, *P_System_error_category;

struct _System_error_category { /* PlaceHolder Class Structure */
};

typedef struct _Locimp _Locimp, *P_Locimp;

struct _Locimp { /* PlaceHolder Class Structure */
};

typedef struct _GUID _GUID, *P_GUID;

struct _GUID {
    ulong Data1;
    ushort Data2;
    ushort Data3;
    uchar Data4[8];
};

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

typedef struct _CONTEXT CONTEXT;

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

typedef struct _IMAGE_SECTION_HEADER _IMAGE_SECTION_HEADER, *P_IMAGE_SECTION_HEADER;

typedef union _union_238 _union_238, *P_union_238;

union _union_238 {
    DWORD PhysicalAddress;
    DWORD VirtualSize;
};

struct _IMAGE_SECTION_HEADER {
    BYTE Name[8];
    union _union_238 Misc;
    DWORD VirtualAddress;
    DWORD SizeOfRawData;
    DWORD PointerToRawData;
    DWORD PointerToRelocations;
    DWORD PointerToLinenumbers;
    WORD NumberOfRelocations;
    WORD NumberOfLinenumbers;
    DWORD Characteristics;
};

typedef struct _RUNTIME_FUNCTION *PRUNTIME_FUNCTION;

typedef struct _EXCEPTION_POINTERS EXCEPTION_POINTERS;

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

typedef struct _OSVERSIONINFOEXA _OSVERSIONINFOEXA, *P_OSVERSIONINFOEXA;

struct _OSVERSIONINFOEXA {
    DWORD dwOSVersionInfoSize;
    DWORD dwMajorVersion;
    DWORD dwMinorVersion;
    DWORD dwBuildNumber;
    DWORD dwPlatformId;
    CHAR szCSDVersion[128];
    WORD wServicePackMajor;
    WORD wServicePackMinor;
    WORD wSuiteMask;
    BYTE wProductType;
    BYTE wReserved;
};

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

typedef struct _MEMORY_BASIC_INFORMATION _MEMORY_BASIC_INFORMATION, *P_MEMORY_BASIC_INFORMATION;

typedef struct _MEMORY_BASIC_INFORMATION *PMEMORY_BASIC_INFORMATION;

typedef ULONG_PTR SIZE_T;

struct _MEMORY_BASIC_INFORMATION {
    PVOID BaseAddress;
    PVOID AllocationBase;
    DWORD AllocationProtect;
    SIZE_T RegionSize;
    DWORD State;
    DWORD Protect;
    DWORD Type;
};

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

typedef WCHAR *PCWSTR;

typedef LONG (*PVECTORED_EXCEPTION_HANDLER)(struct _EXCEPTION_POINTERS *);

typedef struct _IMAGE_SECTION_HEADER *PIMAGE_SECTION_HEADER;

typedef WCHAR *LPWCH;

typedef struct _UNWIND_HISTORY_TABLE *PUNWIND_HISTORY_TABLE;

typedef void (*PFLS_CALLBACK_FUNCTION)(PVOID);

typedef LARGE_INTEGER *PLARGE_INTEGER;

typedef struct _KNONVOLATILE_CONTEXT_POINTERS *PKNONVOLATILE_CONTEXT_POINTERS;

typedef EXCEPTION_ROUTINE *PEXCEPTION_ROUTINE;

typedef struct _OSVERSIONINFOEXA *LPOSVERSIONINFOEXA;

typedef HANDLE *PHANDLE;

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

typedef ULONG_PTR HCRYPTKEY;

typedef ULONG_PTR HCRYPTHASH;

typedef uint ALG_ID;

typedef ULONG_PTR HCRYPTPROV;

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

typedef WORD *LPWORD;

typedef struct HKEY__ *HKEY;

typedef HKEY *PHKEY;

typedef int INT;

typedef WORD ATOM;

typedef struct tagRECT *LPRECT;

typedef HANDLE HGLOBAL;

typedef BOOL *LPBOOL;

typedef void *HGDIOBJ;

typedef BYTE *PBYTE;

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

typedef struct IMAGE_RESOURCE_DIRECTORY IMAGE_RESOURCE_DIRECTORY, *PIMAGE_RESOURCE_DIRECTORY;

struct IMAGE_RESOURCE_DIRECTORY {
    dword Characteristics;
    dword TimeDateStamp;
    word MajorVersion;
    word MinorVersion;
    word NumberOfNamedEntries;
    word NumberOfIdEntries;
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

typedef struct _tiddata _tiddata, *P_tiddata;

typedef struct _tiddata *_ptiddata;

typedef struct setloc_struct setloc_struct, *Psetloc_struct;

typedef struct setloc_struct _setloc_struct;

typedef struct _is_ctype_compatible _is_ctype_compatible, *P_is_ctype_compatible;

struct _is_ctype_compatible {
    ulong id;
    int is_clike;
};

struct setloc_struct {
    wchar_t *pchLanguage;
    wchar_t *pchCountry;
    int iLocState;
    int iPrimaryLen;
    BOOL bAbbrevLanguage;
    BOOL bAbbrevCountry;
    UINT _cachecp;
    wchar_t _cachein[131];
    wchar_t _cacheout[131];
    struct _is_ctype_compatible _Loc_c[5];
    wchar_t _cacheLocaleName[85];
};

struct _tiddata {
    ulong _tid;
    uintptr_t _thandle;
    int _terrno;
    ulong _tdoserrno;
    uint _fpds;
    ulong _holdrand;
    char *_token;
    wchar_t *_wtoken;
    uchar *_mtoken;
    char *_errmsg;
    wchar_t *_werrmsg;
    char *_namebuf0;
    wchar_t *_wnamebuf0;
    char *_namebuf1;
    wchar_t *_wnamebuf1;
    char *_asctimebuf;
    wchar_t *_wasctimebuf;
    void *_gmtimebuf;
    char *_cvtbuf;
    uchar _con_ch_buf[5];
    ushort _ch_buf_used;
    void *_initaddr;
    void *_initarg;
    void *_pxcptacttab;
    void *_tpxcptinfoptrs;
    int _tfpecode;
    pthreadmbcinfo ptmbcinfo;
    pthreadlocinfo ptlocinfo;
    int _ownlocale;
    ulong _NLG_dwCode;
    void *_terminate;
    void *_unexpected;
    void *_translator;
    void *_purecall;
    void *_curexception;
    void *_curcontext;
    int _ProcessingThrow;
    void *_curexcspec;
    void *_pExitContext;
    void *_pUnwindContext;
    void *_pFrameInfoChain;
    ulonglong _ImageBase;
    ulonglong _ThrowImageBase;
    void *_pForeignException;
    _setloc_struct _setloc_data;
    void *_reserved1;
    void *_reserved2;
    void *_reserved3;
    int _cxxReThrow;
    ulong __initDomain;
    int _initapartment;
};

typedef struct SC SC, *PSC;

struct SC { /* PlaceHolder Structure */
};

typedef struct EHExceptionRecord EHExceptionRecord, *PEHExceptionRecord;

struct EHExceptionRecord { /* PlaceHolder Structure */
};

typedef struct _xDISPATCHER_CONTEXT _xDISPATCHER_CONTEXT, *P_xDISPATCHER_CONTEXT;

struct _xDISPATCHER_CONTEXT { /* PlaceHolder Structure */
};

typedef struct _s_CatchableType _s_CatchableType, *P_s_CatchableType;

struct _s_CatchableType { /* PlaceHolder Structure */
};

typedef struct _Init_atexit _Init_atexit, *P_Init_atexit;

struct _Init_atexit { /* PlaceHolder Structure */
};

typedef struct _LocaleUpdate _LocaleUpdate, *P_LocaleUpdate;

struct _LocaleUpdate { /* PlaceHolder Structure */
};

typedef struct _Fac_tidy_reg_t _Fac_tidy_reg_t, *P_Fac_tidy_reg_t;

struct _Fac_tidy_reg_t { /* PlaceHolder Structure */
};

typedef struct _Yarn<char> _Yarn<char>, *P_Yarn<char>;

struct _Yarn<char> { /* PlaceHolder Structure */
};

typedef struct _Locinfo _Locinfo, *P_Locinfo;

struct _Locinfo { /* PlaceHolder Structure */
};

typedef struct error_condition error_condition, *Perror_condition;

struct error_condition { /* PlaceHolder Structure */
};

typedef struct ios_base ios_base, *Pios_base;

struct ios_base { /* PlaceHolder Structure */
};

typedef struct _Lockit _Lockit, *P_Lockit;

struct _Lockit { /* PlaceHolder Structure */
};

typedef struct _Init_locks _Init_locks, *P_Init_locks;

struct _Init_locks { /* PlaceHolder Structure */
};

typedef struct Rect Rect, *PRect;

struct Rect { /* PlaceHolder Structure */
};

typedef struct SubAllocator SubAllocator, *PSubAllocator;

struct SubAllocator { /* PlaceHolder Structure */
};

typedef struct _LDBL12 _LDBL12, *P_LDBL12;

struct _LDBL12 {
    uchar ld12[12];
};

typedef struct _CRT_FLOAT _CRT_FLOAT, *P_CRT_FLOAT;

struct _CRT_FLOAT {
    float f;
};

typedef struct _CRT_DOUBLE _CRT_DOUBLE, *P_CRT_DOUBLE;

struct _CRT_DOUBLE {
    double x;
};

typedef int (*_onexit_t)(void);

typedef struct IUnknown *LPUNKNOWN;

