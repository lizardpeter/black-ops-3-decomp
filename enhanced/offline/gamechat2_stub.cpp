// Strict loader-compatible GameChat2 boundary for the pinned BO3 Store EXE.
// NO Xbox users, XUIDs, voice capture/render, voice sessions or sockets.
// Genuine GameChat2.dll is not loaded when this private offline shim is selected.
// Microsoft Game Chat 2 is only usable when GDK XNetworking is available;
// the enhanced offline GDK always reports that feature unavailable.
//
// Only the 16 *imported export names* are reproduced. These conservative
// Win64 ABI fail/zero leaves are NOT a replacement for Game Chat functionality
// and do not claim every GameChat2 function's full typed signature. In-game
// callers must gate chat initialization on its reported failure.
using U64 = unsigned long long;
#define T7_EXPORT extern "C" __declspec(dllexport)
static constexpr U64 Unsupported = 0xFFFFFFFF80004001ULL; // E_NOTIMPL sign-extended
extern "C" int __stdcall _DllMainCRTStartup(void *, unsigned int, void *) { return 1; }
#define CHAT_FAIL(name) T7_EXPORT U64 name(...) { return Unsupported; }
#define CHAT_ZERO(name) T7_EXPORT U64 name(...) { return 0; }

// Initialization and user/packet mutation all fail; never fake success.
CHAT_FAIL(ChatManagerInitialize)
CHAT_FAIL(ChatManagerAddLocalUser)
CHAT_FAIL(ChatManagerAddRemoteUser)
CHAT_FAIL(ChatManagerRemoveUser)
CHAT_FAIL(ChatManagerProcessIncomingPacket)
CHAT_FAIL(ChatUserSetAudioRenderVolume)

// No manager exists. Processing and collection routines must fail rather than
// falsely claim success while leaving output buffers untouched. Only genuine
// scalar queries and shutdown use false/zero/no-op.
CHAT_ZERO(ChatManagerCleanup)
CHAT_FAIL(ChatManagerFinishProcessingDataFrames)
CHAT_FAIL(ChatManagerFinishProcessingStateChanges)
CHAT_FAIL(ChatManagerGetChatUsers)
CHAT_FAIL(ChatManagerStartProcessingDataFrames)
CHAT_FAIL(ChatManagerStartProcessingStateChanges)
CHAT_ZERO(ChatUserGetEffectiveCommunicationRelationship)
CHAT_ZERO(ChatUserGetIsLocal)
CHAT_ZERO(ChatUserGetXboxUserId)
CHAT_ZERO(GameChatFailFastWithInform)
