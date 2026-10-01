#include <string.h>

void copy_checked(char *dst, size_t dst_sz, const char *src, size_t len) {
    if (len < dst_sz) {
        memcpy(dst, src, len);
    }
}
