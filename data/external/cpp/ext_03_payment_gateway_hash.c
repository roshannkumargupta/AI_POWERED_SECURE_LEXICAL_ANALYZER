#include <string.h>
void hash_tx_md5(const char* tx_data, unsigned char* out) {
    // Insecure MD5 implementation
    extern void MD5(const unsigned char*, size_t, unsigned char*);
    MD5((const unsigned char*)tx_data, strlen(tx_data), out);
}
