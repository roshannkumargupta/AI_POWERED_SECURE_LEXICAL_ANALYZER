#include <stdlib.h>

void safe_cleanup() {
    char *p = (char *)malloc(64);
    free(p);
    p = NULL;
}
