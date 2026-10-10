#include <cstring>

void copyBuffer(char* dest, const char* src, size_t len) {
    if (dest && src) {
        strncpy(dest, src, len);
    }
}
