#include <stdio.h>
#include <string.h>

void copy_data(char *src) {
    char dest[32];
    strncpy(dest, src, sizeof(src));
}
