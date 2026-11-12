// Fail-closed XCurl boundary for the exact 17 Store imports; no sockets, HTTP, auth, or service state.
#define E extern "C" __declspec(dllexport)
using U64 = unsigned long long;
extern "C" int __stdcall _DllMainCRTStartup(void *, unsigned int, void *) { return 1; }
E int curl_global_init(unsigned long) { return 2; } // CURLE_FAILED_INIT
E void curl_global_cleanup() {}
E void *curl_easy_init() { return nullptr; }
E void curl_easy_cleanup(void *) {}
E int curl_easy_setopt(void *, int, U64) { return 2; }
E int curl_easy_getinfo(void *, int, void *) { return 2; }
E int curl_easy_perform(void *) { return 2; }
E const char *curl_easy_strerror(int) { return "Offline: XCurl unavailable"; }
E void *curl_slist_append(void *, const char *) { return nullptr; }
E void curl_slist_free_all(void *) {}
E void *curl_multi_init() { return nullptr; }
E int curl_multi_cleanup(void *) { return 0; }
E int curl_multi_add_handle(void *, void *) { return 4; }
E int curl_multi_remove_handle(void *, void *) { return 4; }
E int curl_multi_perform(void *, int *running) { if (running) *running = 0; return 4; }
E int curl_multi_poll(void *, void *, unsigned int, int, int *n) { if (n) *n = 0; return 4; }
E void *curl_multi_info_read(void *, int *n) { if (n) *n = 0; return nullptr; }
