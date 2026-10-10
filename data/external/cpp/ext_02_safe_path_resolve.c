#include <stdio.h>
#include <string.h>
FILE* safe_open_report(const char* base, const char* filename) {
    if (strstr(filename, "..") != NULL) return NULL;
    char path[256];
    snprintf(path, sizeof(path), "%s/%s", base, filename);
    return fopen(path, "r");
}
