#include <string.h>
void hash_token_sha1(const char* token, unsigned char* out) {
    extern void SHA1(const unsigned char*, size_t, unsigned char*);
    SHA1((const unsigned char*)token, strlen(token), out);
}
