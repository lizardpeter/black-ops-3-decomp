// Enhanced direct-connect packet authenticator. SipHash-2-4, a keyed MAC (NOT encryption).
// This is deliberately separate from original T7 protocol and never linked into the faithful build.
#pragma once
namespace T7WireAuth {
using U64 = unsigned long long;
inline U64 Rotate(U64 x, unsigned n) { return (x << n) | (x >> (64 - n)); }
inline U64 Read64(const unsigned char *p) {
    U64 result = 0;
    for (unsigned i = 0; i < 8; ++i) result |= (U64)p[i] << (8 * i);
    return result;
}
inline void Round(U64 &a, U64 &b, U64 &c, U64 &d) {
    a += b; b = Rotate(b, 13); b ^= a; a = Rotate(a, 32);
    c += d; d = Rotate(d, 16); d ^= c;
    a += d; d = Rotate(d, 21); d ^= a;
    c += b; b = Rotate(b, 17); b ^= c; c = Rotate(c, 32);
}
inline U64 Mac(const unsigned char key[16], const unsigned char *data, unsigned length) {
    const U64 k0 = Read64(key), k1 = Read64(key + 8);
    U64 a = 0x736f6d6570736575ULL ^ k0, b = 0x646f72616e646f6dULL ^ k1;
    U64 c = 0x6c7967656e657261ULL ^ k0, d = 0x7465646279746573ULL ^ k1;
    const unsigned blocks = length / 8;
    for (unsigned i = 0; i < blocks; ++i) {
        U64 m = Read64(data + i * 8);
        d ^= m; Round(a, b, c, d); Round(a, b, c, d); a ^= m;
    }
    U64 last = (U64)length << 56;
    for (unsigned i = 0; i < length % 8; ++i)
        last |= (U64)data[blocks * 8 + i] << (8 * i);
    d ^= last; Round(a, b, c, d); Round(a, b, c, d); a ^= last;
    c ^= 0xff;
    for (int i = 0; i < 4; ++i) Round(a, b, c, d);
    return a ^ b ^ c ^ d;
}
// Keyed wire v3 binds the tag to sender direction (client or server).
// Without this domain separation a client packet could be reflected back
// as if it came from the server, even without disclosure of the key.
// The transport bounds input to 8-byte header + 8-byte sequence + 1262 data.
constexpr unsigned MaxSignedContent = 8 + 8 + 1262;
inline U64 MacDirectional(const unsigned char key[16], const unsigned char *data,
                          unsigned length, unsigned char senderRole) {
    if (!data || length > MaxSignedContent ||
        (senderRole != 'C' && senderRole != 'S')) return 0;
    unsigned char signedBytes[MaxSignedContent + 1];
    for (unsigned i = 0; i < length; ++i) signedBytes[i] = data[i];
    signedBytes[length] = senderRole;
    return Mac(key, signedBytes, length + 1);
}
inline bool EqualTag(U64 tag, const unsigned char *bytes) {
    unsigned char difference = 0;
    for (unsigned i = 0; i < 8; ++i)
        difference |= (unsigned char)((tag >> (56 - i * 8)) ^ bytes[i]);
    return difference == 0;
}
struct ReplayWindow { U64 largest, seen; };
inline bool Accept(ReplayWindow &state, U64 sequence) {
    if (!sequence) return false;
    if (sequence > state.largest) {
        const U64 distance = sequence - state.largest;
        state.seen = (distance >= 64 ? 0ULL : state.seen << distance) | 1ULL;
        state.largest = sequence;
        return true;
    }
    const U64 distance = state.largest - sequence;
    if (distance >= 64 || (state.seen & (1ULL << distance))) return false;
    state.seen |= 1ULL << distance;
    return true;
}
inline bool ParseHexKey(const char *text, unsigned char key[16]) {
    if (!text) return false;
    unsigned char candidate[16] = {};
    for (unsigned i = 0; i < 32; ++i) {
        const unsigned char c = (unsigned char)text[i];
        unsigned int nibble;
        if (c >= '0' && c <= '9') nibble = c - '0';
        else if (c >= 'a' && c <= 'f') nibble = c - 'a' + 10;
        else if (c >= 'A' && c <= 'F') nibble = c - 'A' + 10;
        else return false;
        candidate[i / 2] |= (unsigned char)(nibble << (i % 2 ? 0 : 4));
    }
    if (text[32]) return false;
    unsigned char any = 0;
    for (unsigned i = 0; i < 16; ++i) any |= candidate[i];
    if (!any) return false;
    for (unsigned i = 0; i < 16; ++i) key[i] = candidate[i];
    return true;
}
} // namespace T7WireAuth
