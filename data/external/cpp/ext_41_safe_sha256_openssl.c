#include <string.h>
void safe_hash_token(const char* token, unsigned char* out) {
    extern void SHA256(const unsigned char*, size_t, unsigned char*);
    SHA256((const unsigned char*)token, strlen(token), out);
}
