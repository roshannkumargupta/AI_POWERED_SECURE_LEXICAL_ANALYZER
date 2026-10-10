#include <stdio.h>
FILE* run_filter(const char* filter) {
    char cmd[128];
    snprintf(cmd, sizeof(cmd), "sort %s", filter);
    return popen(cmd, "r");
}
