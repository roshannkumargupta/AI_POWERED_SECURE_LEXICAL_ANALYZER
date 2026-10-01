#include <string.h>

void append_data(char *dst, size_t dst_sz, const char *src) {
    strncat(dst, src, dst_sz - strlen(dst) - 1);
}
