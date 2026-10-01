#include <stdio.h>
#include <string.h>

void copy_data(char *src) {
    char dest[32];
    memcpy(dest, src, sizeof(src));
}
