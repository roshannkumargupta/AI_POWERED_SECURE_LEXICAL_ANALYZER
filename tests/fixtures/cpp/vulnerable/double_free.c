#include <stdlib.h>

void cleanup() {
    char *p = (char *)malloc(32);
    free(p);
    free(p);
}
