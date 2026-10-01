#include <stdio.h>

void parse_safe(const char *in) {
    char buf[16];
    sscanf(in, "%15s", buf);
}
