#include <stdio.h>

void read_safe(FILE *fp) {
    char buf[64];
    fscanf(fp, "%63s", buf);
}
