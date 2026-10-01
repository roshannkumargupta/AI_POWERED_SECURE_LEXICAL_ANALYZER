#include <string.h>

void safe_copy(const char *src) {
    char dest[32];
    strncpy(dest, src, sizeof(dest) - 1);
    dest[sizeof(dest) - 1] = '\0';
}
