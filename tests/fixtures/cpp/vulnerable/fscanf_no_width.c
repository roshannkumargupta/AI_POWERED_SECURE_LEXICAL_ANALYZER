#include <stdio.h>

void read_file(FILE *fp) {
    char buf[64];
    fscanf(fp, "%s", buf);
}
