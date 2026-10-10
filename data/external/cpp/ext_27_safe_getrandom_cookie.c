#include <stdio.h>
int make_safe_cookie(unsigned int* out) {
    FILE* f = fopen("/dev/urandom", "rb");
    if (!f) return -1;
    fread(out, sizeof(*out), 1, f);
    fclose(f);
    return 0;
}
