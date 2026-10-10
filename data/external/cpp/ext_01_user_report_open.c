#include <stdio.h>
FILE* open_report(const char* filename) {
    char path[128];
    sprintf(path, "/var/reports/%s", filename);
    return fopen(path, "r");
}
